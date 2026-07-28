"""
Paper Fetcher - 从多个数据源获取最新论文
支持: Arxiv, Semantic Scholar, OpenReview
"""
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# Retry helper with exponential backoff
# ============================================================
def _retry_request(url, timeout=10, max_retries=3):
    """Perform HTTP GET with exponential backoff retry"""
    import random
    last_error = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PaperAutomation/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code == 429:
                wait = (2 ** attempt) * 3 + random.uniform(0, 2)
                logger.warning(f"[Retry] 429 rate limited, waiting {wait:.1f}s (attempt {attempt+1}/{max_retries})")
            elif e.code == 503:
                wait = (2 ** attempt) * 2 + random.uniform(0, 1)
                logger.warning(f"[Retry] 503 unavailable, waiting {wait:.1f}s (attempt {attempt+1}/{max_retries})")
            else:
                raise
            time.sleep(wait)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = (2 ** attempt) * 2 + random.uniform(0, 1)
                logger.warning(f"[Retry] {type(e).__name__}, waiting {wait:.1f}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
    raise last_error

# ============================================================
# Arxiv API
# ============================================================
def fetch_arxiv(query: str, max_results: int = 10, categories: list = None, max_age_days: int = None) -> list:
    """从Arxiv API搜索论文"""
    papers = []
    
    cutoff = None
    if max_age_days is not None and max_age_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    
    search_parts = []
    if query:
        search_parts.append(f"all:{urllib.parse.quote(query)}")
    if categories:
        cat_str = "+OR+".join(f"cat:{c}" for c in categories)
        search_parts.append(f"({cat_str})")
    
    search_query = "+AND+".join(search_parts) if search_parts else "all:artificial+intelligence"
    
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query={search_query}"
        f"&start=0&max_results={max_results}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )
    
    logger.info(f"[Arxiv] Fetching: {url[:200]}...")
    
    try:
        data = _retry_request(url, timeout=10, max_retries=3)
    except Exception as e:
        logger.error(f"[Arxiv] Request failed after retries: {e}")
        return papers
    
    root = ET.fromstring(data)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    
    for entry in root.findall("atom:entry", ns):
        try:
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            published_el = entry.find("atom:published", ns)
            link_el = entry.find("atom:id", ns)
            
            title = " ".join(title_el.text.split()) if title_el is not None and title_el.text else ""
            
            # Extract arXiv ID
            arxiv_id = ""
            if link_el is not None and link_el.text:
                arxiv_id = link_el.text.strip().split("/abs/")[-1]
                # Remove version suffix
                arxiv_id = arxiv_id.split("v")[0] if "v" in arxiv_id.split("/")[-1] else arxiv_id
            
            authors = []
            for author_el in entry.findall("atom:author", ns):
                name_el = author_el.find("atom:name", ns)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())
            
            abstract = " ".join(summary_el.text.split()) if summary_el is not None and summary_el.text else ""
            
            published = published_el.text if published_el is not None and published_el.text else ""
            
            # Extract categories
            cats = []
            for cat_el in entry.findall("atom:category", ns):
                term = cat_el.get("term", "")
                if term:
                    cats.append(term)
            
            # Date filter
            if cutoff and published:
                try:
                    pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    if pub_date < cutoff:
                        continue
                except (ValueError, AttributeError):
                    pass  # Include if we cannot parse date
            
            # Extract primary category
            for cat_el in entry.findall("arxiv:primary_category", ns):
                primary_cat = cat_el.get("term", "")
            
            papers.append({
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "arxiv_id": arxiv_id,
                "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else link_el.text.strip() if link_el is not None and link_el.text else "",
                "published": published,
                "year": published[:4] if published else "",
                "source": "arxiv",
                "categories": cats,
                "primary_category": primary_cat,
            })
        except Exception as e:
            logger.warning(f"[Arxiv] Parse error: {e}")
            continue
    
    logger.info(f"[Arxiv] Found {len(papers)} papers")
    return papers


# ============================================================
# Semantic Scholar API
# ============================================================
def fetch_semantic_scholar(query: str, limit: int = 10, fields: str = None) -> list:
    """从Semantic Scholar API搜索论文"""
    papers = []
    
    if fields is None:
        fields = "title,year,url,abstract,externalIds,authors,venue,journal,publicationDate,citationCount"
    
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": fields,
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    
    logger.info(f"[S2] Fetching: {url[:200]}...")
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperAutomation/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"[S2] Request failed: {e}")
        return papers
    
    for item in data.get("data", []):
        try:
            paper_id = item.get("paperId", "")
            title = item.get("title", "")
            abstract = item.get("abstract", "") or ""
            year = item.get("year", "")
            url = item.get("url", "")
            
            # External IDs
            ext = item.get("externalIds", {}) or {}
            arxiv_id = ext.get("ArXiv", "")
            doi = ext.get("DOI", "")
            
            # Authors
            authors = [a.get("name", "") for a in item.get("authors", [])]
            
            # Venue
            venue = item.get("venue", "") or ""
            journal = (item.get("journal", {}) or {}).get("name", "") if item.get("journal") else ""
            
            # Citation count
            citations = item.get("citationCount", 0)
            
            papers.append({
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "year": str(year) if year else "",
                "url": url or f"https://api.semanticscholar.org/CorpusID:{paper_id}",
                "arxiv_id": arxiv_id,
                "doi": doi,
                "venue": venue,
                "journal": journal,
                "citation_count": citations,
                "source": "semantic_scholar",
                "s2_id": paper_id,
            })
        except Exception as e:
            logger.warning(f"[S2] Parse error: {e}")
            continue
    
    logger.info(f"[S2] Found {len(papers)} papers")
    return papers


# ============================================================
# OpenReview API
# ============================================================
def fetch_openreview(query: str, limit: int = 10) -> list:
    """从OpenReview API搜索论文"""
    papers = []
    
    params = urllib.parse.urlencode({
        "term": query,
        "limit": limit,
    })
    url = f"https://api2.openreview.net/notes/search?{params}"
    
    logger.info(f"[OR] Fetching: {url[:200]}...")
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperAutomation/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"[OR] Request failed: {e}")
        return papers
    
    for note in data.get("notes", []):
        try:
            content = note.get("content", {})
            title_val = content.get("title", {})
            title = title_val.get("value", "") if isinstance(title_val, dict) else str(title_val)
            if not title:
                continue
            
            abstract_val = content.get("abstract", {})
            abstract = abstract_val.get("value", "") if isinstance(abstract_val, dict) else str(abstract_val)
            
            authors_val = content.get("authors", {})
            author_list = authors_val.get("value", []) if isinstance(authors_val, dict) else (authors_val if isinstance(authors_val, list) else [])
            
            forum = note.get("forum", "")
            paper_id = note.get("id", "")
            
            papers.append({
                "title": title,
                "authors": author_list,
                "abstract": abstract,
                "year": str(note.get("cdate", 0))[:4] if note.get("cdate") else "",
                "url": f"https://openreview.net/forum?id={forum}" if forum else "",
                "forum_id": forum,
                "paper_id": paper_id,
                "source": "openreview",
            })
        except Exception as e:
            logger.warning(f"[OR] Parse error: {e}")
            continue
    
    logger.info(f"[OR] Found {len(papers)} papers")
    return papers


# ============================================================
# Arxiv RSS / New submissions (by category, recent)
# ============================================================
def fetch_arxiv_recent(categories: list = None, lookback_days: int = 730) -> list:
    """获取Arxiv上最近N天的新论文"""
    if categories is None:
        categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO"]
    
    cat_str = "+OR+".join(f"cat:{c}" for c in categories)
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query=({cat_str})"
        f"&start=0&max_results=100"
        f"&sortBy=submittedDate&sortOrder=descending"
    )
    
    logger.info(f"[Arxiv Recent] Fetching...")
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperAutomation/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read().decode("utf-8")
    except Exception as e:
        logger.error(f"[Arxiv Recent] Request failed: {e}")
        return []
    
    root = ET.fromstring(data)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    papers = []
    
    for entry in root.findall("atom:entry", ns):
        try:
            published_el = entry.find("atom:published", ns)
            published_str = published_el.text if published_el is not None and published_el.text else ""
            
            # Filter by date
            if published_str:
                try:
                    pub_date = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                    if pub_date < cutoff:
                        continue
                except (ValueError, AttributeError):
                    pass  # Include if we can't parse date
            
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            link_el = entry.find("atom:id", ns)
            
            title = " ".join(title_el.text.split()) if title_el is not None and title_el.text else ""
            
            arxiv_id = ""
            if link_el is not None and link_el.text:
                arxiv_id = link_el.text.strip().split("/abs/")[-1].split("v")[0]
            
            authors = []
            for author_el in entry.findall("atom:author", ns):
                name_el = author_el.find("atom:name", ns)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())
            
            abstract = " ".join(summary_el.text.split()) if summary_el is not None and summary_el.text else ""
            
            cats = []
            for cat_el in entry.findall("atom:category", ns):
                term = cat_el.get("term", "")
                if term:
                    cats.append(term)
            
            primary_cat = ""
            for cat_el in entry.findall("arxiv:primary_category", ns):
                primary_cat = cat_el.get("term", "")
            
            papers.append({
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "arxiv_id": arxiv_id,
                "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "",
                "published": published_str,
                "year": published_str[:4] if published_str else "",
                "source": "arxiv",
                "categories": cats,
                "primary_category": primary_cat,
            })
        except Exception as e:
            logger.warning(f"[Arxiv Recent] Parse error: {e}")
            continue
    
    logger.info(f"[Arxiv Recent] Found {len(papers)} papers from last {lookback_days} days")
    return papers


# ============================================================
# Combined fetcher for a direction
# ============================================================
def fetch_for_direction(direction: dict, config: dict) -> list:
    """为一个研究方向从多个数据源拉取论文"""
    all_papers = []
    seen_titles = set()
    
    keywords = direction.get("keywords", {})
    primary_kw = keywords.get("primary", [])
    secondary_kw = keywords.get("secondary", [])
    all_kw = primary_kw[:3] + secondary_kw[:2]  # Use top keywords to avoid too many queries
    
    sources = config.get("sources", {})
    max_age_days = sources.get("arxiv", {}).get("lookback_days", None)
    
    # Arxiv search with combined primary keywords (P0: merge 3→1 query + 10s delay + 60s 429 cooldown)
    if sources.get("arxiv", {}).get("enabled", True):
        arxiv_kws = [kw for kw in primary_kw[:3] if kw]
        if arxiv_kws:
            combined_query = " OR ".join(f'"{kw}"' for kw in arxiv_kws)
            logger.info(f"[Fetch] Arxiv combined query: {len(arxiv_kws)} keywords merged")
            try:
                papers = fetch_arxiv(
                    query=combined_query,
                    max_results=sources.get("arxiv", {}).get("max_results_per_query", 10),
                    max_age_days=max_age_days,
                    categories=sources.get("arxiv", {}).get("categories"),
                )
                for p in papers:
                    key = p["title"].lower().strip()
                    if key not in seen_titles:
                        seen_titles.add(key)
                        all_papers.append(p)
                if not papers:
                    logger.warning("[Fetch] Arxiv returned 0 results (possible 429), cooling down 60s...")
                    time.sleep(60)
                else:
                    logger.info(f"[Fetch] Arxiv returned {len(papers)} papers, waiting 10s...")
                    time.sleep(10)
            except Exception as e:
                logger.error(f"[Fetch] Arxiv combined query failed: {e}")
                logger.warning("[Fetch] Arxiv failure, cooling down 60s before next source...")
                time.sleep(60)
    
    # Semantic Scholar with primary keywords
    if sources.get("semantic_scholar", {}).get("enabled", True):
        for kw in primary_kw[:2]:
            try:
                papers = fetch_semantic_scholar(
                    query=kw,
                    limit=sources.get("semantic_scholar", {}).get("limit_per_query", 10),
                )
                for p in papers:
                    key = p["title"].lower().strip()
                    if key not in seen_titles:
                        seen_titles.add(key)
                        all_papers.append(p)
                time.sleep(1)
            except Exception as e:
                logger.error(f"[Fetch] S2 '{kw[:50]}...' failed: {e}")
    
    # OpenReview with primary keywords
    if sources.get("openreview", {}).get("enabled", True):
        for kw in primary_kw[:2]:
            try:
                papers = fetch_openreview(
                    query=kw,
                    limit=sources.get("openreview", {}).get("limit_per_query", 10),
                )
                for p in papers:
                    key = p["title"].lower().strip()
                    if key not in seen_titles:
                        seen_titles.add(key)
                        all_papers.append(p)
                time.sleep(1)
            except Exception as e:
                logger.error(f"[Fetch] OR '{kw[:50]}...' failed: {e}")
    
    # Filter by year for all sources
    if max_age_days is not None and max_age_days > 0:
        from datetime import datetime, timedelta, timezone
        cutoff_year = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).year
        before_count = len(all_papers)
        all_papers = [p for p in all_papers if int(p.get("year", 0) or 0) >= cutoff_year]
        logger.info(f"[Fetch] Year filter ({max_age_days}d): {before_count} -> {len(all_papers)} papers (min year: {cutoff_year})")
    
    logger.info(f"[Fetch] Direction '{direction['name']}' total: {len(all_papers)} papers")
    return all_papers


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    papers = fetch_arxiv("embodied intelligence world model", max_results=5)
    for p in papers:
        print(f"  {p['title'][:80]}  [{p['arxiv_id']}]")
