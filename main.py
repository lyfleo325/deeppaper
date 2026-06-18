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
    """Generate PaperAuto Checklist to Obsidian Daily with recommendation reasons"""
    import logging
    from datetime import datetime
    logger = logging.getLogger("PaperAutomation")
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    directions = config.get("directions", [])
    total = sum(len(v) for v in all_notes.values())

    kb_root = config.get("obsidian", {}).get("kb_root", r"C:\Users\Leo\Desktop\KB")
    daily_date = f"{today.year}-{today.month}-{today.day}"
    daily_dir = os.path.join(kb_root, "Daily", daily_date)
    os.makedirs(daily_dir, exist_ok=True)

    checklist_name = f"{daily_date} PaperAuto Checklist.md"
    checklist_path = os.path.join(daily_dir, checklist_name)

    lines = [
        f"# \U0001f4cb {daily_date} PaperAuto Checklist",
        "",
        f"> **\u751f\u6210\u65f6\u95f4**: {today.strftime('%Y-%m-%d %H:%M')}",
        f"> **\u603b\u8ba1**: {total} \u7bc7\u63a8\u8350\u8bba\u6587 | {len(directions)} \u4e2a\u7814\u7a76\u65b9\u5411",
        f"> **\u72b6\u6001**: \U0001f534 \u5f85\u5ba1\u9605\u786e\u8ba4",
        "",
        "---",
        "",
        "## \U0001f4d6 \u5feb\u901f\u7d22\u5f15",
        "",
    ]

    for direction in directions:
        name = direction.get("name", "")
        notes = all_notes.get(name, [])
        if not notes:
            continue
        lines.append(f"- [{name}](#{name}) ({len(notes)}\u7bc7)")

    lines.extend(["", "---", ""])

    paper_idx = 0

    for direction in directions:
        name = direction.get("name", "Unknown")
        ob_project = direction.get("ob_project", "")
        notes = all_notes.get(name, [])
        papers = screened.get(name, [])
        if not notes:
            continue

        lines.append(f"## \U0001f4cc {name} \u2192 `{ob_project}`")
        lines.append("")
        lines.append("| # | \u52fe\u9009 | \u8bba\u6587\u6807\u9898 | \u8bc4\u5206 | arXiv |")
        lines.append("|---|------|----------|------|-------|")

        for i, (filename, note_content) in enumerate(notes, 1):
            paper = papers[i-1] if i-1 < len(papers) else {}
            title = paper.get("title", filename.replace("-\u8bba\u6587\u7cbe\u8bfb.md", ""))
            score = paper.get("relevance_score", "-")
            arxiv_id = paper.get("arxiv_id", "-")
            lines.append(f"| {i} | [ ] | {title[:55]} | {score} | [{arxiv_id}](https://arxiv.org/abs/{arxiv_id}) |")

        lines.append("")
        lines.append("---")
        lines.append("")

        for i, (filename, note_content) in enumerate(notes, 1):
            paper = papers[i-1] if i-1 < len(papers) else {}
            title = paper.get("title", "")
            score = paper.get("relevance_score", "-")
            arxiv_id = paper.get("arxiv_id", "-")
            url = paper.get("url", f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "")
            abstract = paper.get("abstract", "No abstract available.")

            paper_idx += 1
            logger.info(f"[Checklist] Translating: {title[:50]}...")
            zh_abstract = _translate_abstract(abstract) if abstract else ""
            rec_reason = _generate_recommendation_reason(paper, direction, score)

            lines.append(f"### {paper_idx}. {title}")
            lines.append("")
            lines.append(f"- [ ] **\u7cbe\u8bfb\u786e\u8ba4**")
            lines.append(f"- **\u8bc4\u5206**: {score} | **arXiv**: [{arxiv_id}]({url})")
            lines.append(f"- **\u6570\u636e\u6e90**: {paper.get('source', 'Unknown')}")
            lines.append("")

            lines.append("**\U0001f524 \u82f1\u6587\u6458\u8981**")
            lines.append("")
            lines.append(f"> {abstract[:1000]}")
            lines.append("")

            lines.append("**\U0001f1e8\U0001f1f3 \u4e2d\u6587\u6458\u8981**")
            lines.append("")
            lines.append(f"> {zh_abstract[:1000]}")
            lines.append("")

            lines.append("**\U0001f4a1 \u63a8\u8350\u539f\u56e0\u4e0e\u65b9\u5411\u5173\u8054**")
            lines.append("")
            lines.append(f"> {rec_reason}")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.extend([
        "## \u26a1 \u5ba1\u9605\u64cd\u4f5c\u6307\u5357",
        "",
        "1. \u9605\u8bfb\u5404\u8bba\u6587\u7684\u4e2d\u82f1\u6587\u6458\u8981\u548c\u63a8\u8350\u539f\u56e0",
        "2. \u52fe\u9009 `[x]` \u6807\u8bb0\u9700\u8981\u7cbe\u8bfb\u7684\u8bba\u6587",
        "3. \u5728 Codex \u4e2d\u544a\u77e5: **\u5bf9\u52fe\u9009\u7684\u8bba\u6587\u8fdb\u884c\u7cbe\u8bfb**",
        "4. \u7cbe\u8bfb\u5b8c\u6210\u540e\u8fd0\u884c `python main.py --push` \u63a8\u9001\u81f3 Obsidian Projects",
        "",
        "> \U0001f4a1 \u53ef\u5728 Obsidian \u4e2d\u76f4\u63a5\u7f16\u8f91\u6b64\u6e05\u5355\uff0c\u4fee\u6539\u540e\u81ea\u52a8\u540c\u6b65",
    ])

    checklist_content = "\n".join(lines)
    with open(checklist_path, "w", encoding="utf-8") as f:
        f.write(checklist_content)

    local_path = os.path.join(note_dir, "_Checklist.md")
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(checklist_content)

    logger.info(f"[Checklist] Saved: {checklist_path}")
    return checklist_path


def _generate_recommendation_reason(paper: dict, direction: dict, score) -> str:
    """Generate recommendation reason and relevance analysis"""
    title = paper.get("title", "")
    abstract = paper.get("abstract", "").lower()
    dir_name = direction.get("name", "")
    keywords = direction.get("keywords", {})
    primary_kw = [k.lower() for k in keywords.get("primary", [])]

    matched = []
    for kw in primary_kw:
        if kw.lower() in title.lower() or kw.lower() in abstract:
            matched.append(kw)

    reasons = []

    if "\u5177\u8eab" in dir_name:
        if any(k in abstract for k in ["robot", "manipulation", "embodied"]):
            reasons.append("\u76f4\u63a5\u6d89\u53ca\u5177\u8eab\u667a\u80fd\u6838\u5fc3\u95ee\u9898\uff08\u673a\u5668\u4eba\u64cd\u63a7/\u611f\u77e5/\u5bfc\u822a\uff09")
        if any(k in abstract for k in ["world model", "simulator", "sim-to-real"]):
            reasons.append("\u6d89\u53ca\u4e16\u754c\u6a21\u578b\u6216\u4eff\u771f\u5230\u73b0\u5b9e\u8fc1\u79fb\uff0c\u662f\u5177\u8eab\u667a\u80fd\u7684\u5173\u952e\u6280\u672f")
        if any(k in abstract for k in ["vla", "vision-language-action"]):
            reasons.append("\u89c6\u89c9-\u8bed\u8a00-\u52a8\u4f5c\uff08VLA\uff09\u7edf\u4e00\u6846\u67b6\uff0c\u5177\u8eab\u667a\u80fd\u524d\u6cbf\u65b9\u5411")
    elif "\u80fd\u91cf" in dir_name:
        if any(k in abstract for k in ["energy", "optimization", "dynamics"]):
            reasons.append("\u4ece\u80fd\u91cf/\u4f18\u5316/\u52a8\u529b\u5b66\u89d2\u5ea6\u5206\u6790\u6a21\u578b\u884c\u4e3a")
        if any(k in abstract for k in ["mamba", "ssm", "state space"]):
            reasons.append("\u72b6\u6001\u7a7a\u95f4\u6a21\u578b\u76f8\u5173\uff0c\u6d89\u53ca\u5e8f\u5217\u5efa\u6a21\u6548\u7387\u7406\u8bba\u5206\u6790")
        if any(k in abstract for k in ["moe", "mixture", "routing"]):
            reasons.append("\u6df7\u5408\u4e13\u5bb6\u8def\u7531\u673a\u5236\uff0c\u6d89\u53ca\u6a21\u578b\u5bb9\u91cf\u4e0e\u6548\u7387\u7684\u6743\u8861\u5206\u6790")
    elif "\u79d1\u7814" in dir_name:
        if any(k in abstract for k in ["agent", "multi-agent", "llm"]):
            reasons.append("LLM\u9a71\u52a8\u7684\u667a\u80fd\u4f53\u7cfb\u7edf\uff0c\u76f4\u63a5\u8d21\u732e\u4e8e\u79d1\u7814\u81ea\u52a8\u5316\u5de5\u5177\u94fe")
        if any(k in abstract for k in ["communication", "protocol", "coordination"]):
            reasons.append("\u667a\u80fd\u4f53\u95f4\u901a\u4fe1\u4e0e\u534f\u8c03\u673a\u5236\uff0c\u591a\u667a\u80fd\u4f53\u7cfb\u7edf\u6838\u5fc3\u6311\u6218")
        if any(k in abstract for k in ["self-correct", "self-improve", "feedback"]):
            reasons.append("\u81ea\u7ea0\u6b63/\u81ea\u6539\u8fdb\u673a\u5236\uff0c\u63d0\u5347\u667a\u80fd\u4f53\u7cfb\u7edf\u53ef\u9760\u6027")
    elif "\u591a\u6a21\u6001" in dir_name:
        if any(k in abstract for k in ["vision", "language", "multimodal"]):
            reasons.append("\u89c6\u89c9-\u8bed\u8a00\u591a\u6a21\u6001\u878d\u5408\uff0c\u8be5\u65b9\u5411\u6838\u5fc3\u7814\u7a76\u4e3b\u9898")
        if any(k in abstract for k in ["distillation", "cross-modal", "transfer"]):
            reasons.append("\u8de8\u6a21\u6001\u77e5\u8bc6\u8fc1\u79fb/\u84b8\u998f\uff0c\u63d0\u5347\u591a\u6a21\u6001\u6a21\u578b\u6548\u7387")
        if any(k in abstract for k in ["reasoning", "spatial", "visual"]):
            reasons.append("\u89c6\u89c9\u63a8\u7406\u80fd\u529b\u589e\u5f3a\uff0c\u591a\u6a21\u6001\u8ba4\u77e5\u6838\u5fc3\u6311\u6218")
    elif "\u7b97\u529b" in dir_name:
        if any(k in abstract for k in ["hpc", "gpu", "inference", "training"]):
            reasons.append("\u9ad8\u6027\u80fd\u8ba1\u7b97/\u63a8\u7406\u4f18\u5316\uff0c\u76f4\u63a5\u8d21\u732e\u4e8eAI\u57fa\u7840\u8bbe\u65bd\u6548\u7387\u63d0\u5347")
        if any(k in abstract for k in ["memory", "throughput", "latency"]):
            reasons.append("\u5185\u5b58/\u541e\u5410\u91cf/\u5ef6\u8fdf\u4f18\u5316\uff0c\u7b97\u529b\u96c6\u7fa4\u5173\u952e\u6307\u6807")
        if any(k in abstract for k in ["distributed", "parallel", "pipeline"]):
            reasons.append("\u5206\u5e03\u5f0f/\u5e76\u884c/\u6d41\u6c34\u7ebf\u67b6\u6784\uff0cAI\u7b97\u529b\u96c6\u7fa4\u6838\u5fc3\u8bbe\u8ba1")

    if not reasons:
        reasons.append(f"\u4e0e\u300c{dir_name}\u300d\u65b9\u5411\u5173\u952e\u8bcd\u5339\u914d\u5ea6\u9ad8\uff08\u8bc4\u5206 {score}\uff09")
        if matched:
            reasons.append(f"\u5339\u914d\u5173\u952e\u8bcd: {', '.join(matched[:5])}")
        reasons.append("\u6458\u8981\u5185\u5bb9\u8868\u660e\u4e0e\u65b9\u5411\u6838\u5fc3\u7814\u7a76\u4e3b\u9898\u76f8\u5173")

    return "\n".join([f"- {r}" for r in reasons])



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
