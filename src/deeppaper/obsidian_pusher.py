"""
Obsidian Pusher - 将生成的论文精读MD文件推送到Obsidian知识库
- Daily目录 (按日期)
- Projects目录 (按方向项目)
- MOCs交叉链接
"""
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_daily_dir(kb_root: str) -> str:
    """Get Daily dir path, format: YYYY-M-D, e.g. 2026-6-16"""
    today = datetime.now()
    # Format: 2026-6-16 (no zero-padding for month/day under 10)
    date_str = f"{today.year}-{today.month}-{today.day}"
    return os.path.join(kb_root, "Daily", date_str)


def get_project_dir(kb_root: str, project_name: str) -> str:
    """获取Project目录路径"""
    return os.path.join(kb_root, "Projects", project_name)


def ensure_dir(path: str):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
    logger.info(f"[Obsidian] Ensured directory: {path}")


def save_file(path: str, content: str):
    """保存文件到指定路径"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"[Obsidian] Saved: {path}")


def update_moc_file(moc_path: str, paper_title: str, note_filename: str, short_name: str):
    """
    更新MOC文件，添加论文条目
    如果文件已包含该论文则跳过
    """
    if not os.path.exists(moc_path):
        logger.warning(f"[Obsidian] MOC not found: {moc_path}")
        return False
    
    with open(moc_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if already exists
    if note_filename in content or short_name in content:
        logger.info(f"[Obsidian] MOC already contains: {note_filename}")
        return False
    
    # Find insertion point - look for ## 📄 论文列表 or ## 论文列表 section
    insert_patterns = [
        r"(##\s*📄\s*论文列表)",
        r"(##\s*论文列表)",
        r"(##\s*📎\s*论文列表)",
        r"(##\s*📚\s*论文)",
    ]
    
    inserted = False
    for pattern in insert_patterns:
        match = re.search(pattern, content)
        if match:
            insert_pos = content.find("\n", match.end())
            if insert_pos == -1:
                insert_pos = match.end()
            
            new_entry = f"\n- [[{note_filename.replace('.md', '')}|{paper_title[:60]}]]"
            
            content = content[:insert_pos] + new_entry + content[insert_pos:]
            inserted = True
            break
    
    if not inserted:
        # Append at end
        content += f"\n\n## 📄 论文列表\n- [[{note_filename.replace('.md', '')}|{paper_title[:60]}]]\n"
    
    with open(moc_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"[Obsidian] Updated MOC: {moc_path}")
    return True


def update_project_moc(project_dir: str, project_name: str, paper_title: str, note_filename: str, short_name: str):
    """
    更新Project目录下的项目MOC文件 (如 能量原理.md)
    """
    moc_file = os.path.join(project_dir, f"{project_name}.md")
    
    if not os.path.exists(moc_file):
        logger.warning(f"[Obsidian] Project MOC not found: {moc_file}")
        return False
    
    with open(moc_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    if note_filename in content or short_name in content:
        logger.info(f"[Obsidian] Project MOC already contains: {note_filename}")
        return False
    
    # Find the core papers table or paper list section
    # Try to insert after "核心论文" or "论文" section header
    insert_markers = [
        r"(##\s*📚\s*核心论文)",
        r"(##\s*📎\s*论文列表)",
        r"(##\s*论文)",
        r"(##\s*📄\s*论文列表)",
        r"(##\s*📚\s*论文)",
    ]
    
    inserted = False
    for pattern in insert_markers:
        match = re.search(pattern, content)
        if match:
            # Find end of section (next ## or EOF)
            rest = content[match.end():]
            next_section = re.search(r"\n##\s", rest)
            
            if next_section:
                insert_pos = match.end() + next_section.start()
            else:
                insert_pos = len(content)
            
            new_entry = f"\n- [[{note_filename.replace('.md', '')}|{paper_title[:60]}]]"
            content = content[:insert_pos] + new_entry + content[insert_pos:]
            inserted = True
            break
    
    if not inserted:
        content += f"\n\n## 📄 论文列表\n- [[{note_filename.replace('.md', '')}|{paper_title[:60]}]]\n"
    
    with open(moc_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"[Obsidian] Updated Project MOC: {moc_file}")
    return True


def push_to_obsidian(all_notes: dict, config: dict) -> dict:
    """
    将所有生成的笔记推送到Obsidian知识库
    返回统计信息
    """
    kb_root = config.get("obsidian", {}).get("kb_root", "")
    if not kb_root or not os.path.exists(kb_root):
        raise FileNotFoundError(f"Obsidian KB root not found: {kb_root}")
    
    obsidian_config = config.get("obsidian", {})
    project_mapping = obsidian_config.get("projects", {})
    moc_mapping = obsidian_config.get("mocs", {})
    
    stats = {
        "daily_saved": 0,
        "project_saved": 0,
        "moc_updated": 0,
        "errors": 0,
    }
    
    # Get today's Daily dir
    daily_dir = get_daily_dir(kb_root)
    ensure_dir(daily_dir)
    
    directions = config.get("directions", [])
    
    for direction in directions:
        dir_name = direction.get("name", "")
        ob_project = direction.get("ob_project", "")
        moc_link = direction.get("moc_link", "")
        
        notes = all_notes.get(dir_name, [])
        project_dir = get_project_dir(kb_root, ob_project)
        ensure_dir(project_dir)
        
        for filename, content in notes:
            try:
                # Extract paper title for linking
                title_match = re.search(r'title:\s*"(.+?)"', content)
                paper_title = title_match.group(1) if title_match else "Unknown"
                short_name_clean = filename.replace(".md", "")
                
                # 1. Save to Daily directory
                daily_path = os.path.join(daily_dir, filename)
                save_file(daily_path, content)
                stats["daily_saved"] += 1
                
                # 2. Save to Project directory
                project_path = os.path.join(project_dir, filename)
                save_file(project_path, content)
                stats["project_saved"] += 1
                
                # 3. Update Project MOC
                if update_project_moc(project_dir, ob_project, paper_title, filename, short_name_clean):
                    stats["moc_updated"] += 1
                
                # 4. Update MOC cross-reference (if configured)
                if moc_link and moc_link in moc_mapping:
                    moc_path = os.path.join(kb_root, moc_mapping[moc_link])
                    if update_moc_file(moc_path, paper_title, filename, short_name_clean):
                        stats["moc_updated"] += 1
                
            except Exception as e:
                logger.error(f"[Obsidian] Failed to push '{filename}': {e}")
                stats["errors"] += 1
    
    return stats


def verify_push(all_notes: dict, config: dict) -> bool:
    """验证所有文件是否已正确推送"""
    kb_root = config.get("obsidian", {}).get("kb_root", "")
    daily_dir = get_daily_dir(kb_root)
    
    all_ok = True
    directions = config.get("directions", [])
    
    for direction in directions:
        dir_name = direction.get("name", "")
        notes = all_notes.get(dir_name, [])
        
        for filename, content in notes:
            # Check Daily
            daily_path = os.path.join(daily_dir, filename)
            if os.path.exists(daily_path):
                size = os.path.getsize(daily_path)
                if size < 100:
                    logger.warning(f"[Verify] File too small: {daily_path} ({size} bytes)")
                    all_ok = False
            else:
                logger.error(f"[Verify] Missing: {daily_path}")
                all_ok = False
    
    return all_ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    print(f"Daily dir: {get_daily_dir('C:/Users/Leo/Desktop/KB')}")
