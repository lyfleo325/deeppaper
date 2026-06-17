"""
Paper Automation - 主控制脚本
论文自动化筛选、精读生成、Obsidian推送
每周一、周四 11:00 运行
"""
import os
import sys
import time
import yaml
import argparse
import logging
import traceback
from datetime import datetime

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paper_fetcher import fetch_for_direction, fetch_arxiv_recent
from paper_screener import screen_all_directions, deduplicate_papers
from note_generator import generate_all_notes
from obsidian_pusher import push_to_obsidian, verify_push


def setup_logging(config: dict) -> logging.Logger:
    """设置日志"""
    log_file = config.get("notifications", {}).get(
        "log_file",
        os.path.join(os.path.dirname(__file__), "logs", "automation.log"),
    )
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    level = logging.DEBUG if config.get("debug", False) else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    return logging.getLogger("PaperAutomation")


def notify_error(config: dict, msg: str):
    """发送错误通知"""
    method = config.get("notifications", {}).get("method", "log")
    
    logger = logging.getLogger("PaperAutomation")
    logger.error(f"[NOTIFY] {msg}")
    
    if method in ("toast", "both"):
        try:
            # Windows toast notification via PowerShell
            import subprocess
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $textNodes = $template.GetElementsByTagName("text")
            $textNodes.Item(0).AppendChild($template.CreateTextNode("论文自动化 - 错误")) > $null
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{msg[:200]}")) > $null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("PaperAutomation").Show($toast)
            '''
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
        except Exception:
            pass


def load_config() -> dict:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config



def _translate_abstract(text: str) -> str:
    """Translate English abstract to Simplified Chinese via Google Translate"""
    if not text or len(text) < 10:
        return text
    try:
        import urllib.request, urllib.parse, json
        chunk = text[:800]
        q = urllib.parse.quote(chunk)
        url = f"https://translate.google.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={q}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://translate.google.com/",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            translated = "".join([s[0] for s in result[0] if s and s[0]])
            if translated and len(translated) > 5 and translated != text:
                return translated
    except Exception as e:
        logging.getLogger("PaperAutomation").warning(f"[Translate] Failed: {e}")
    return text  # fallback to original


def generate_summary_list(all_notes: dict, screened: dict, config: dict, note_dir: str) -> str:
    """Generate summary checklist with abstracts and Chinese translations"""
    from datetime import datetime
    import json
    today = datetime.now().strftime("%Y-%m-%d")
    directions = config.get("directions", [])
    total = sum(len(v) for v in all_notes.values())
    
    lines = [
        "# 📋 论文精读汇总清单",
        "",
        f"> 生成日期: {today}",
        f"> 总计: {total} 篇论文 | {len(directions)} 个方向",
        f"> 状态: 待确认精读",
        "",
        "---",
        "",
        "## 📖 论文目录",
        "",
    ]
    
    for direction in directions:
        name = direction.get("name", "")
        notes = all_notes.get(name, [])
        if not notes:
            continue
        anchor = name
        lines.append(f"- [{name}](#{anchor}) ({len(notes)}篇)")
    
    lines.extend(["", "---", ""])
    
    dir_idx = 0
    for direction in directions:
        name = direction.get("name", "Unknown")
        ob_project = direction.get("ob_project", "")
        notes = all_notes.get(name, [])
        papers = screened.get(name, [])
        if not notes:
            continue
        
        dir_idx += 1
        lines.append(f"## 📌 {name} ({ob_project})")
        lines.append("")
        lines.append("| # | 论文标题 | 分数 | arXiv ID | 精读文件 |")
        lines.append("|---|----------|------|----------|----------|")
        
        for i, (filename, note_content) in enumerate(notes, 1):
            paper = papers[i-1] if i-1 < len(papers) else {}
            title = paper.get("title", filename.replace("-论文精读.md", ""))
            score = paper.get("relevance_score", "-")
            arxiv_id = paper.get("arxiv_id", "-")
            lines.append(f"| {i} | {title[:60]} | {score} | {arxiv_id} | [[{filename.replace('.md', '')}]] |")
        
        lines.append("")
        
        # Detailed abstracts with translations
        for i, (filename, note_content) in enumerate(notes, 1):
            paper = papers[i-1] if i-1 < len(papers) else {}
            title = paper.get("title", "")
            score = paper.get("relevance_score", "-")
            arxiv_id = paper.get("arxiv_id", "-")
            url = paper.get("url", f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "")
            abstract = paper.get("abstract", "No abstract available.")
            
            # Translate
            logging.getLogger("PaperAutomation").info(f"[Translate] Translating abstract for: {title[:50]}...")
            zh_abstract = _translate_abstract(abstract) if abstract else ""
            
            lines.append(f"### {i}. {title}")
            lines.append("")
            lines.append(f"- **分数**: {score} | **arXiv**: [{arxiv_id}]({url})")
            lines.append(f"- **精读文件**: [[{filename.replace('.md', '')}]]")
            lines.append("")
            lines.append("**🔤 英文摘要 (Original Abstract)**")
            lines.append("")
            lines.append(f"> {abstract[:1200]}")
            lines.append("")
            lines.append("**🇨🇳 中文摘要 (Chinese Translation)**")
            lines.append("")
            lines.append(f"> {zh_abstract[:1200]}")
            lines.append("")
            lines.append("---")
            lines.append("")
    
    summary_path = os.path.join(note_dir, "_汇总清单.md")
    summary_content = "\n".join(lines)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_content)
    
    return summary_path


def run_pipeline(config: dict = None) -> bool:

    """
    运行完整的自动化管线:
    1. Fetch papers from all sources
    2. Screen for each direction
    3. Generate deep-read notes
    4. Push to Obsidian
    5. Verify
    """
    if config is None:
        config = load_config()
    
    logger = logging.getLogger("PaperAutomation")
    
    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"Paper Automation Pipeline START - {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    directions = config.get("directions", [])
    sources = config.get("sources", {})
    papers_per_dir = config.get("papers_per_direction", 2)
    
    all_errors = []
    
    try:
        # Step 1: Fetch papers from Arxiv recent (as baseline)
        logger.info("[Step 1/5] Fetching recent papers from Arxiv...")
        all_papers = []
        try:
            arxiv_config = sources.get("arxiv", {})
            recent = fetch_arxiv_recent(
                categories=arxiv_config.get("categories"),
                lookback_days=arxiv_config.get("lookback_days", 14),
            )
            all_papers.extend(recent)
            logger.info(f"  Arxiv recent: {len(recent)} papers")
        except Exception as e:
            err_msg = f"Arxiv recent fetch failed: {e}"
            logger.error(err_msg)
            all_errors.append(err_msg)
        
        # Step 1b: Fetch per-direction from all sources
        for direction in directions:
            dir_name = direction.get("name", "Unknown")
            logger.info(f"[Step 1/5] Fetching for direction: {dir_name}")
            try:
                dir_papers = fetch_for_direction(direction, config)
                all_papers.extend(dir_papers)
                logger.info(f"  '{dir_name}': +{len(dir_papers)} papers")
            except Exception as e:
                err_msg = f"Fetch for '{dir_name}' failed: {e}"
                logger.error(err_msg)
                all_errors.append(err_msg)
            time.sleep(2)  # Rate limiting between directions
        
        # Dedup all papers
        all_papers = deduplicate_papers(all_papers)
        logger.info(f"[Step 1/5] Total unique papers: {len(all_papers)}")
        
        if len(all_papers) == 0:
            raise RuntimeError("No papers fetched from any source!")
        
        # Step 2: Screen for each direction
        logger.info("[Step 2/5] Screening papers for all directions...")
        screened = screen_all_directions(all_papers, directions, papers_per_dir)
        
        total_selected = sum(len(v) for v in screened.values())
        logger.info(f"[Step 2/5] Selected {total_selected} papers across {len(directions)} directions")
        
        if total_selected == 0:
            logger.warning("No papers selected! Check keyword configuration.")
        
        # Local note directory
        note_dir = os.path.join(os.path.dirname(__file__), "note")
        
        # Step 3: Generate deep-read notes
        logger.info("[Step 3/5] Generating deep-read notes...")
        all_notes = generate_all_notes(screened, config)
        
        total_notes = sum(len(v) for v in all_notes.values())
        logger.info(f"[Step 3/5] Generated {total_notes} notes")
        
        # Save local copy to note/ directory
        local_saved = 0
        os.makedirs(note_dir, exist_ok=True)
        for dir_name, notes in all_notes.items():
            for filename, note_content in notes:
                try:
                    local_path = os.path.join(note_dir, filename)
                    with open(local_path, "w", encoding="utf-8") as f:
                        f.write(note_content)
                    local_saved += 1
                except Exception as e:
                    logger.error(f"[Local] Failed to save '{filename}': {e}")
        logger.info(f"[Local] Saved {local_saved} notes to {note_dir}")
        
        # Generate summary checklist
        summary_path = generate_summary_list(all_notes, screened, config, note_dir)
        logger.info(f"[Local] Summary checklist: {summary_path}")
        
        # Step 4: Push to Obsidian (only if --push flag is set)
        push_to_obsidian_enabled = config.get("_push_to_obsidian", False)
        if not push_to_obsidian_enabled:
            logger.info("[Step 4/5] Obsidian push SKIPPED (use --push to enable)")
            logger.info("[Step 5/5] Verification SKIPPED (local-only mode)")
            elapsed = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"Pipeline COMPLETED (local-only) in {elapsed:.1f}s")
            logger.info(f"[INFO] Notes saved to {note_dir}")
            logger.info(f"[INFO] Run 'python main.py --push' to push to Obsidian")
            logger.info("=" * 60)
            return True
        
        logger.info("[Step 4/5] Pushing to Obsidian...")
        stats = push_to_obsidian(all_notes, config)
        logger.info(
            f"[Step 4/5] Push complete: "
            f"Daily={stats['daily_saved']}, Project={stats['project_saved']}, "
            f"MOC={stats['moc_updated']}, Errors={stats['errors']}"
        )
        
        # Step 5: Verify
        logger.info("[Step 5/5] Verifying...")
        if verify_push(all_notes, config):
            logger.info("[Step 5/5] Verification PASSED [OK]")
        else:
            logger.warning("[Step 5/5] Verification found issues [WARN]")
        
    except Exception as e:
        err_msg = f"Pipeline failed: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)
        all_errors.append(err_msg)
    
    elapsed = time.time() - start_time
    status = "COMPLETED" if not all_errors else "COMPLETED WITH ERRORS"
    logger.info("=" * 60)
    logger.info(f"Pipeline {status} in {elapsed:.1f}s")
    
    # Report errors
    if all_errors:
        logger.warning(f"Errors encountered ({len(all_errors)}):")
        for i, err in enumerate(all_errors, 1):
            logger.warning(f"  [{i}] {err[:200]}")
        notify_error(config, f"论文自动化完成，但有{len(all_errors)}个错误: {all_errors[0][:150]}")
    else:
        logger.info("All steps completed successfully!")
    
    logger.info("=" * 60)
    
    return len(all_errors) == 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="PaperAutomation - 论文自动化筛选与精读")
    parser.add_argument("--push", action="store_true", help="推送至 Obsidian 知识库")
    parser.add_argument("--local-only", action="store_true", default=True, help="仅本地生成 (默认)")
    args = parser.parse_args()
    
    try:
        config = load_config()
        # Store push flag in config for pipeline access
        config["_push_to_obsidian"] = args.push
        
        setup_logging(config)
        logger = logging.getLogger("PaperAutomation")
        logger.info("Paper Automation initialized")
        
        success = run_pipeline(config)
        
        if success:
            logger.info("[OK] Automation finished successfully")
            if not args.push:
                logger.info("[INFO] 精读笔记已存入 note/ 目录，审阅后运行 python main.py --push 推送至 Obsidian")
            sys.exit(0)
        else:
            logger.warning("[WARN] Automation finished with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"FATAL: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
