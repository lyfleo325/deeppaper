"""
Paper Screener - 论文筛选、评分、去重、排序
根据关键词匹配为每个方向筛选 top-N 论文
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize(text: str) -> str:
    """标准化文本用于匹配"""
    return re.sub(r"[^a-z0-9\s]", "", text.lower())


def keyword_score(text: str, keywords: list) -> float:
    """
    计算文本中关键词的匹配分数
    - 标题中出现 primary 关键词: +3 分/个
    - 摘要中出现 primary 关键词: +1 分/个  
    - 标题中出现 secondary 关键词: +1 分/个
    """
    text_lower = text.lower()
    score = 0.0
    for kw in keywords:
        kw_lower = kw.lower()
        count = text_lower.count(kw_lower)
        if count > 0:
            score += count * 1.0
    return score


def title_keyword_score(title: str, keywords: list) -> float:
    """标题加权匹配分数"""
    title_lower = title.lower()
    score = 0.0
    for kw in keywords:
        if kw.lower() in title_lower:
            score += 3.0
    return score


def abstract_keyword_score(abstract: str, keywords: list) -> float:
    """摘要匹配分数"""
    abstract_lower = abstract.lower()
    score = 0.0
    for kw in keywords:
        count = abstract_lower.count(kw.lower())
        if count > 0:
            score += min(count, 3) * 1.0  # Cap to prevent abstract spam
    return score


def recency_score(published: str) -> float:
    """
    根据发布日期计算时效性分数
    越新的论文分数越高
    """
    from datetime import datetime, timezone, timedelta
    
    if not published:
        return 0.0
    
    try:
        pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_ago = (now - pub_date).days
        
        if days_ago <= 7:
            return 10.0
        elif days_ago <= 14:
            return 7.0
        elif days_ago <= 30:
            return 4.0
        elif days_ago <= 60:
            return 2.0
        else:
            return 1.0
    except (ValueError, AttributeError):
        return 3.0  # Default medium recency if we can't parse


def venue_score(venue: str, journal: str, venue_filter: list) -> float:
    """
    根据发表场合计算分数
    顶会 +5, 匹配 venue_filter 中的 venue +3
    """
    score = 0.0
    venue_lower = (venue + " " + journal).lower()
    
    top_venues = [
        "neurips", "iclr", "icml", "cvpr", "iccv", "eccv",
        "acl", "emnlp", "naacl", "corl", "icra", "iros", "rss",
        "asplos", "isca", "micro", "hpca", "sc", "ppopp",
        "jmlr", "tpami", "tmlr",
    ]
    
    for tv in top_venues:
        if tv in venue_lower:
            score += 5.0
            break
    
    for vf in venue_filter:
        if vf.lower() in venue_lower:
            score += 3.0
            break
    
    return score


def citation_score(citation_count) -> float:
    """引用数加分 (log scale)"""
    try:
        cc = int(citation_count)
        if cc <= 0:
            return 0.0
        import math
        return min(math.log2(cc + 1) * 1.5, 10.0)
    except (ValueError, TypeError):
        return 0.0


def has_excluded_keywords(text: str, exclude_kw: list) -> bool:
    """检查文本是否包含排除关键词"""
    text_lower = text.lower()
    for kw in exclude_kw:
        if kw.lower() in text_lower:
            return True
    return False


def deduplicate_papers(papers: list) -> list:
    """去重：按标题相似度"""
    seen = set()
    unique = []
    
    for paper in papers:
        title = normalize(paper.get("title", ""))
        # Use first 80 chars as dedup key
        key = title[:80]
        if key and key not in seen:
            seen.add(key)
            unique.append(paper)
    
    return unique


def score_paper(paper: dict, direction: dict) -> float:
    """
    为论文打分
    综合: 标题关键词 + 摘要关键词 + 时效性 + 发表场合 + 引用数 - 排除词惩罚
    """
    keywords = direction.get("keywords", {})
    primary_kw = keywords.get("primary", [])
    secondary_kw = keywords.get("secondary", [])
    exclude_kw = keywords.get("exclude", [])
    venue_filter = direction.get("venue_filter", [])
    
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    published = paper.get("published", "")
    venue = paper.get("venue", "") or paper.get("journal", "")
    journal = paper.get("journal", "")
    citations = paper.get("citation_count", 0)
    
    # Exclusion check
    full_text = f"{title} {abstract}"
    if has_excluded_keywords(full_text, exclude_kw):
        return -100.0
    
    score = 0.0
    
    # Title keyword match
    score += title_keyword_score(title, primary_kw)
    score += title_keyword_score(title, secondary_kw) * 0.5
    
    # Abstract keyword match
    score += abstract_keyword_score(abstract, primary_kw) * 0.5
    score += abstract_keyword_score(abstract, secondary_kw) * 0.25
    
    # Recency
    score += recency_score(published)
    
    # Venue
    score += venue_score(venue, journal, venue_filter)
    
    # Citations
    score += citation_score(citations)
    
    # Source bonus: arxiv papers are preprints, slightly lower
    source = paper.get("source", "")
    if source == "openreview":
        score += 2.0  # Peer-reviewed venue
    
    return round(score, 2)


def screen_papers(papers: list, direction: dict, top_n: int = 2) -> list:
    """
    为某个方向筛选并排序论文
    返回 top_n 篇得分最高的论文
    """
    # Step 1: Dedup
    unique_papers = deduplicate_papers(papers)
    logger.info(f"[Screen] Direction '{direction['name']}': {len(papers)} -> {len(unique_papers)} unique")
    
    # Step 2: Score
    scored = []
    for paper in unique_papers:
        s = score_paper(paper, direction)
        if s > 0:  # Only keep positive scores
            scored.append((s, paper))
    
    # Step 3: Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Step 4: Take top_n + some buffer
    top = scored[:top_n]
    
    result = []
    for score, paper in top:
        paper["relevance_score"] = score
        result.append(paper)
        logger.info(
            f"  [{score:6.1f}] {paper.get('title', '')[:80]}"
        )
    
    return result


def screen_all_directions(all_papers: list, directions: list, papers_per_dir: int = 2) -> dict:
    """
    为所有方向筛选论文
    返回 {direction_name: [papers]}
    """
    results = {}
    
    for direction in directions:
        name = direction.get("name", "Unknown")
        try:
            selected = screen_papers(all_papers, direction, papers_per_dir)
            results[name] = selected
            logger.info(f"[Screen] '{name}': selected {len(selected)} papers")
        except Exception as e:
            logger.error(f"[Screen] '{name}' failed: {e}")
            results[name] = []
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    # Quick test with dummy data
    test_papers = [
        {
            "title": "World Models for Embodied AI: A Comprehensive Survey",
            "abstract": "We present a survey of world models for embodied intelligence and robot learning...",
            "published": "2026-06-15T00:00:00Z",
            "source": "arxiv",
            "authors": ["Alice", "Bob"],
            "url": "https://arxiv.org/abs/2606.00001",
        },
        {
            "title": "FlashAttention-3: Even Faster Attention for Large Models",
            "abstract": "We introduce FlashAttention-3 with optimized GPU kernel fusion for HPC...",
            "published": "2026-06-14T00:00:00Z",
            "source": "arxiv",
            "authors": ["Charlie"],
            "url": "https://arxiv.org/abs/2606.00002",
        },
    ]
    
    direction = {
        "name": "具身智能",
        "keywords": {
            "primary": ["embodied intelligence", "world model", "robot learning"],
            "secondary": ["benchmark", "simulation"],
            "exclude": ["medical", "bio"],
        },
        "venue_filter": ["CoRL", "ICRA", "NeurIPS"],
    }
    
    result = screen_papers(test_papers, direction, top_n=2)
    for p in result:
        print(f"  [{p['relevance_score']}] {p['title']}")
