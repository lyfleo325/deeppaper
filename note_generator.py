"""
Note Generator - 根据论文元数据生成"论文精读"格式的Markdown文件
完全遵循 paper-deep-read SKILL.md 的10段式结构
"""
import re
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    # Remove invalid Windows filename chars
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    # Remove newlines
    name = name.replace("\n", " ").replace("\r", "")
    # Trim
    name = name.strip()
    # Max length
    if len(name) > 80:
        name = name[:77] + "..."
    return name


def generate_short_name(title: str, authors: list, year: str) -> str:
    """生成论文短名称 (用于文件名)"""
    # Extract first meaningful words
    words = title.split()
    short = ""
    for w in words[:6]:
        # Skip common stop words
        if w.lower() in {"a", "an", "the", "in", "on", "of", "and", "to", "for", "with", "via", "is", "are"}:
            continue
        clean = re.sub(r"[^a-zA-Z0-9]", "", w)
        if clean:
            short += clean + "-"
    
    short = short.rstrip("-")
    if not short:
        short = title[:40].replace(" ", "-")
    
    # Add year
    if year:
        short = f"{short}-{year}"
    
    return sanitize_filename(short)


def format_authors(authors: list) -> str:
    """格式化作者列表"""
    if not authors:
        return "Unknown"
    if len(authors) <= 5:
        return ", ".join(authors)
    else:
        return f"{', '.join(authors[:3])} et al."


def format_paper_info_table(paper: dict) -> str:
    """生成论文信息表格"""
    title = paper.get("title", "Unknown")
    authors = format_authors(paper.get("authors", []))
    year = paper.get("year", "")
    url = paper.get("url", "")
    arxiv_id = paper.get("arxiv_id", "")
    doi = paper.get("doi", "")
    source = paper.get("source", "Unknown")
    venue = paper.get("venue", "") or paper.get("journal", "") or "arXiv"
    citations = paper.get("citation_count", "N/A")
    
    source_link = url or f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
    
    lines = [
        "| 项目 | 内容 |",
        "|------|------|",
        f"| **标题** | {title} |",
        f"| **作者** | {authors} |",
        f"| **年份** | {year} |",
        f"| **来源** | {venue} |",
        f"| **链接** | [{arxiv_id or doi or 'Link'}]({source_link}) |",
        f"| **引用数** | {citations} |",
        f"| **数据源** | {source} |",
    ]
    
    if doi:
        lines.insert(-1, f"| **DOI** | {doi} |")
    
    return "\n".join(lines)


def generate_tags(direction: dict) -> str:
    """生成 YAML frontmatter 的 tags"""
    tags = ["paper-reading"]
    direction_name = direction.get("name", "")
    tag_name = direction.get("tag", "")
    project = direction.get("ob_project", "")
    
    if tag_name:
        tags.append(tag_name)
    if project:
        tags.append(project)
    
    return "\n  - ".join(tags)


def generate_deep_read_md(paper: dict, direction: dict, source_config: dict = None) -> str:
    """
    生成完整的论文精读Markdown文件
    遵循 paper-deep-read SKILL.md 格式
    """
    title = paper.get("title", "Unknown Paper")
    authors = format_authors(paper.get("authors", []))
    abstract = paper.get("abstract", "No abstract available.")
    year = paper.get("year", "")
    url = paper.get("url", "")
    arxiv_id = paper.get("arxiv_id", "")
    doi = paper.get("doi", "")
    source = paper.get("source", "Unknown")
    venue = paper.get("venue", "") or paper.get("journal", "") or "arXiv"
    score = paper.get("relevance_score", 0)
    
    direction_name = direction.get("name", "")
    ob_project = direction.get("ob_project", "")
    tag_list = generate_tags(direction)
    
    # Short name for aliases
    short_name = generate_short_name(title, paper.get("authors", []), year)
    
    # Source identifier
    source_id = arxiv_id or doi or url.split("/")[-1] if url else ""
    
    # Today's date
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Main link for source
    main_link = url or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "")
    
    pieces = [
        "---",
        f"title: \"{title}\"",
        "tags:",
        f"  - {tag_list}",
        "aliases:",
        f"  - \"{short_name}\"",
        f"created: {today}",
        f"source: {source_id}",
        "status: 待精读",
        "---",
        "",
        f"# 📄 {title}",
        "",
        f"> **论文自动化筛选 & 精读笔记**",
        f"> 方向: {direction_name} | 项目: [[{ob_project}/{ob_project}|{ob_project}]]",
        f"> 推荐分数: {score}",
        f"> 生成日期: {today}",
        "",
        "## 一、论文信息",
        "",
        format_paper_info_table(paper),
        "",
        "## 二、核心问题与动机",
        "",
        f"> 摘要: {abstract}",
        "",
        "*(待精读后补充)*",
        "",
        "## 三、方法",
        "",
        "*(待精读后补充)*",
        "",
        "## 四、技术原理",
        "",
        "*(待精读后补充)*",
        "",
        "## 五、理论分析",
        "",
        "*(待精读后补充)*",
        "",
        "## 六、实验结果",
        "",
        "| 实验 | 数据集 | 指标 | 结果 | 对比基线 |",
        "|------|--------|------|------|----------|",
        "| | | | | |",
        "",
        "## 七、优势与局限",
        "",
        "### 优势",
        "*(待精读后补充)*",
        "",
        "### 局限",
        "*(待精读后补充)*",
        "",
        "## 八、与相关工作的关系",
        "",
        "| 相关论文 | 关系 | 区别 |",
        "|----------|------|------|",
        "| | | |",
        "",
        f"## 九、对{direction_name}方向的启示",
        "",
        "*(待精读后补充)*",
        "",
        "## 十、总结与评价",
        "",
        "| 维度 | 评分(1-5) | 说明 |",
        "|------|-----------|------|",
        "| 创新性 | - | 待评估 |",
        "| 技术深度 | - | 待评估 |",
        "| 实验充分 | - | 待评估 |",
        "| 可复现性 | - | 待评估 |",
        "| 影响力 | - | 待评估 |",
        "",
        "---",
        "",
        f"## 🔗 关联笔记",
        "",
        f"- 所属项目: [[{ob_project}/{ob_project}|{ob_project}]]",
    ]
    
    # Add MOC cross-links based on direction
    moc_link = direction.get("moc_link", "")
    if moc_link:
        pieces.append(f"- MOC: [[MOCs/{moc_link}|{moc_link}]]")
    
    pieces.extend([
        f"- 数据源: {source}",
        "",
        "---",
        "",
        "> [!tip] 下一步",
        "> 使用 Codex + paper-deep-read skill 进行完整精读",
        f"> 命令: `对本文进行精读，输出到Obsidian Daily目录，关联{ob_project} MOC`",
        "",
    ])
    
    return "\n".join(pieces)


def generate_all_notes(screened: dict, config: dict) -> dict:
    """
    为所有筛选出的论文生成精读笔记
    返回 {direction_name: [(filename, content), ...]}
    """
    all_notes = {}
    directions = config.get("directions", [])
    
    for direction in directions:
        name = direction.get("name", "Unknown")
        papers = screened.get(name, [])
        notes = []
        
        for paper in papers:
            try:
                content = generate_deep_read_md(paper, direction)
                
                # Generate filename
                short = generate_short_name(
                    paper.get("title", ""),
                    paper.get("authors", []),
                    paper.get("year", ""),
                )
                filename = f"{short}-论文精读.md"
                
                notes.append((filename, content))
                logger.info(f"[NoteGen] Generated: {filename}")
            except Exception as e:
                logger.error(f"[NoteGen] Failed for '{paper.get('title', '')}': {e}")
        
        all_notes[name] = notes
    
    return all_notes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    test_paper = {
        "title": "World Models for Embodied Intelligence: A New Paradigm",
        "authors": ["Alice Smith", "Bob Jones", "Charlie Lee", "Diana Wang"],
        "abstract": "We present a novel approach to building world models for embodied AI agents...",
        "year": "2026",
        "url": "https://arxiv.org/abs/2606.12345",
        "arxiv_id": "2606.12345",
        "source": "arxiv",
        "relevance_score": 85.5,
    }
    test_direction = {
        "name": "具身智能",
        "ob_project": "PhysBrain",
        "tag": "embodied-ai",
        "moc_link": "PhysBrain",
    }
    md = generate_deep_read_md(test_paper, test_direction)
    print(md[:500])
