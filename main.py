"""
Paper Automation - 主控制脚本
论文自动化筛选、精读生成、Obsidian推送
每周一、周四 11:00 运行
"""
import os
import sys
import time
import yaml
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
        
        # Step 3: Generate deep-read notes
        logger.info("[Step 3/5] Generating deep-read notes...")
        all_notes = generate_all_notes(screened, config)
        
        total_notes = sum(len(v) for v in all_notes.values())
        logger.info(f"[Step 3/5] Generated {total_notes} notes")
        
        # Step 4: Push to Obsidian
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
    try:
        config = load_config()
        setup_logging(config)
        logger = logging.getLogger("PaperAutomation")
        logger.info("Paper Automation initialized")
        
        success = run_pipeline(config)
        
        if success:
            logger.info("[OK] Automation finished successfully")
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
