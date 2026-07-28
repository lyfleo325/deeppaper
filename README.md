# PaperAutomation · DeepPaper

<p align="center">
  <a href="https://github.com/lyfleo325/deeppaper"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" /></a>
  <a href="https://github.com/lyfleo325/deeppaper/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey.svg" alt="Platform" />
</p>

> **DeepPaper** — A fully automated academic paper discovery, screening, and deep-reading pipeline.  
> Three sources. Five research directions. Your Obsidian knowledge base, always up to date.

The idea is simple: you define the research directions you care about, and DeepPaper periodically scans arXiv, Semantic Scholar, and OpenReview for the most relevant new papers, scores them, generates bilingual summaries, and pushes deep-reading notes into your [Obsidian](https://obsidian.md) vault — with `[[wikilinks]]` to your existing MOCs. You review the checklist, then decide what gets persisted.

---

## Quick Start

### Prerequisites

- **Python 3.10+** (tested on 3.12)
- **PyYAML >= 6.0**
- **Windows** (Task Scheduler integration; code works on Linux/macOS but scheduling is Windows-only)
- **Obsidian** (optional — pipeline runs fully offline without it)

### Clone, configure, run

```bash
git clone https://github.com/lyfleo325/deeppaper.git
cd deeppaper
pip install PyYAML
```

Edit `config.yaml` — the only file you need to touch:

```yaml
obsidian:
  kb_root: C:/Users/You/Desktop/your-vault   # your Obsidian vault path
schedule:
  days: [Monday, Wednesday]
  hour: 12
  minute: 10
```

Then:

```bash
# Run the full pipeline (local-only — generates notes + checklist in note/)
python main.py

# Review the checklist at note/_汇总清单.md, then push to Obsidian
python main.py --push
```

### Windows scheduled task

```powershell
# Create the scheduled task (Mon/Wed 12:10)
.\setup_scheduler.ps1

# Check status
.\setup_scheduler.ps1 -Status

# Trigger a run immediately
.\setup_scheduler.ps1 -RunNow
```

> Copy `run_pipeline.bat.example` → `run_pipeline.bat`, update the Python path, and the scheduled task auto-installs PyYAML before every run.

---

## What it does

DeepPaper runs a **5-step pipeline** every cycle:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. FETCH    │ → │  2. SCREEN   │ → │  3. GENERATE  │ → │  4. PUSH     │ → │  5. VERIFY   │
│              │    │              │    │              │    │              │    │              │
│ arXiv        │    │ keyword      │    │ deep-read    │    │ Daily/       │    │ file size    │
│ Semantic     │    │ scoring      │    │ markdown     │    │ Projects/    │    │ check +      │
│ Scholar      │    │ + dedup      │    │ + bilingual  │    │ MOCs         │    │ path verify  │
│ OpenReview   │    │ + top-2 per  │    │ abstract     │    │ (--push      │    │              │
│              │    │ direction    │    │ translation  │    │  only)       │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

**Error resilience built in:**
- Exponential backoff retry on HTTP errors (429, 503)
- arXiv query merging (3 keywords → 1 OR query) to reduce rate-limit hits
- 60-second cooldown after 429 or exception
- Configurable retry with 60-minute delay between attempts

---

## Five research directions

Each direction has curated keyword sets (primary + secondary), exclusion filters, and venue constraints — all in `config.yaml`.

| # | Direction | Project Tag | Focus |
|---|-----------|-------------|-------|
| 1 | **Embodied AI** | `PhysBrain` | Robot learning, VLA, manipulation, sim-to-real, humanoid |
| 2 | **Energy Principles** | `能量原理` | EBMs, SSMs, MoE, learning dynamics, optimization landscape |
| 3 | **Research Agents** | `科研智能体` | AI Scientist, multi-agent, tool use, autonomous research |
| 4 | **Multimodal Models** | `多模态` | VLM, MLLM, visual reasoning, multimodal alignment, OPD/GRPO |
| 5 | **AI Infrastructure** | `AI算力集群` | HPC, GPU clusters, distributed training, FlashAttention, inference optimization |

Each direction outputs **top 2 papers per cycle** (configurable: `papers_per_direction`).

---

## Project structure

```
deeppaper/
├── main.py                  # Pipeline orchestrator (5-step flow)
├── paper_fetcher.py         # arXiv + Semantic Scholar + OpenReview fetcher
├── paper_screener.py        # Keyword scoring, deduplication, top-N selection
├── note_generator.py        # Deep-read Markdown (10-section format)
├── obsidian_pusher.py       # Obsidian sync: Daily / Projects / MOCs
├── config.yaml              # Everything configurable: directions, sources, paths
├── setup_scheduler.ps1      # Windows Task Scheduler management
├── run_pipeline.bat.example # Template batch file for scheduled runs
├── requirements.txt         # PyYAML >= 6.0
├── handoff.md               # Changelog + project documentation
├── .gitignore
├── logs/
│   └── automation.log       # Per-run log (auto-appended)
└── note/                    # Generated notes (gitignored)
    ├── _汇总清单.md           # Bilingual summary checklist
    └── *-论文精读.md          # Per-paper deep-read notes
```

---

## Obsidian integration

After `--push`, DeepPaper writes into your Obsidian vault:

| Target | Path Pattern | Content |
|--------|-------------|---------|
| **Daily** | `Daily/YYYY-M-D/` | Deep-read notes for today's run |
| **Project** | `Projects/{ProjectName}/` | Same notes, grouped by research direction |
| **MOC** | `MOCs/{方向}.md` | `[[wikilinks]]` appended automatically |

Example vault layout after a run:

```
KB/
├── Daily/
│   └── 2026-7-28/
│       └── VLMR1-Stable-Generalizable-R1style-2025-论文精读.md
├── Projects/
│   └── 多模态/
│       └── VLMR1-Stable-Generalizable-R1style-2025-论文精读.md
└── MOCs/
    └── 多模态.md   ← [[VLMR1-Stable-Generalizable-R1style-2025|VLMR1: Stable...]]
```

---

## Deep-read note format

Each generated note follows a 10-section structure:

1. **Paper metadata** (title, authors, year, venue, DOI, citations)
2. **Core problem & motivation**
3. **Method** (with ASCII architecture diagram)
4. **Technical principles** (LaTeX-heavy)
5. **Theoretical analysis** (stability, convergence, energy landscape)
6. **Experimental results** (SOTA comparison table)
7. **Strengths & limitations**
8. **Relationship to related work** (comparison table)
9. **Implications for adjacent fields**
10. **Summary & evaluation** (5-dimension rating table)
11. **PM perspective** (optional, for flagged papers)

---

## Two-phase workflow

DeepPaper is designed around a **human-in-the-loop** review step:

```
Phase 1: python main.py
         → Fetch, screen, generate checklist only
         → Output: note/_汇总清单.md (bilingual abstracts + recommendation reasons)

Phase 2: Read the checklist. Decide.
         → python main.py --push
         → Persist selected deep-read notes to Obsidian vault
```

This prevents low-quality papers from polluting your knowledge base before you review them.

---

## Contributing

This is a personal research tool, but PRs are welcome. The most impactful contributions:

- Additional data sources (bioRxiv, PubMed, OpenAlex)
- Improved keyword scoring (embedding-based similarity)
- Multi-platform scheduler support (cron, launchd)
- LLM-based abstract quality filtering

Open an issue to discuss before submitting a PR.

---

## License

MIT
