# PaperAutomation · DeepPaper

<p align="center">
  <a href="https://github.com/lyfleo325/deeppaper"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" /></a>
  <a href="https://github.com/lyfleo325/deeppaper/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey.svg" alt="Platform" />
</p>

> **DeepPaper** — A fully automated academic paper discovery, screening, and deep-reading pipeline.  
> Three sources. Research directions. Your Obsidian knowledge base, always up to date.

---

## Quick Start

### Prerequisites

- **Python 3.10+** (tested on 3.12)
- **Windows** (Task Scheduler integration)
- **Obsidian** (optional — pipeline runs offline without it)

### Install & run

```bash
# Clone and install
git clone https://github.com/lyfleo325/deeppaper.git
cd deeppaper
pip install -e .

# Initialize config
deeppaper setup

# Edit config — set your Obsidian vault path
deeppaper config --edit

# Check everything is ready
deeppaper doctor

# Run the pipeline (generates checklist in note/)
deeppaper run

# After reviewing, push to Obsidian
deeppaper run --push
```

---

## CLI Reference

```
deeppaper [OPTIONS] COMMAND [ARGS]...

Commands:
  run         Run the full paper pipeline
  setup       Initialize config.yaml from built-in template
  config      Display or edit current configuration
  doctor      Environment health check
  directions  List all research directions with keywords
  schedule    Manage Windows scheduled task
```

### deeppaper run

```bash
deeppaper run                  # Generate checklist (local-only)
deeppaper run --push           # Push deep-read notes to Obsidian
deeppaper run -d "Research Direction 1"       # Only run one direction
deeppaper run -d "Research Direction 1" -d "Research Direction 4"  # Run specific directions
```

### deeppaper doctor

```bash
deeppaper doctor
```

Checks: Python version, PyYAML, Click, config.yaml, Obsidian vault path, source configuration, research directions.

### deeppaper directions

```bash
deeppaper directions
```

Lists all 5 research directions with keyword sets, exclusions, and venue filters.

### deeppaper config

```bash
deeppaper config              # Display current config summary
deeppaper config --edit       # Open config.yaml in Notepad
```

### deeppaper setup

```bash
deeppaper setup               # Create config.yaml in cwd
deeppaper setup -o my.yaml    # Custom output path
deeppaper setup --force       # Overwrite existing config
```

### deeppaper schedule

```bash
deeppaper schedule install    # Create Windows scheduled task (Mon/Wed 12:10)
deeppaper schedule status     # Check task status
deeppaper schedule remove     # Remove scheduled task
```

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
- arXiv query merging (3 keywords to 1 OR query) to reduce rate-limit hits
- 60-second cooldown after 429 or exception
- Configurable retry with 60-minute delay between attempts

---

## Research directions

Each direction has curated keyword sets (primary + secondary), exclusion filters, and venue constraints — all in `config.yaml`.

| # | Direction | Project Tag | Focus |
|---|-----------|-------------|-------|
| 1 | **Research Direction 1** | `dir-1` | Robot learning, VLA, manipulation, sim-to-real, humanoid |
| 2 | **Research Direction 2** | `dir-2` | EBMs, SSMs, MoE, learning dynamics, optimization landscape |
| 3 | **Research Direction 3** | `dir-3` | AI Scientist, multi-agent, tool use, autonomous research |
| 4 | **Research Direction 4** | `dir-4` | VLM, MLLM, visual reasoning, multimodal alignment |
| 5 | **Research Direction 5** | `dir-5` | HPC, GPU clusters, distributed training, inference optimization |

Each direction outputs **top 2 papers per cycle** (configurable: `papers_per_direction`).

---

## Project structure

```
deeppaper/
├── pyproject.toml                # Package metadata (setuptools)
├── src/
│   └── deeppaper/
│       ├── __init__.py           # Package init + version
│       ├── __main__.py           # python -m deeppaper
│       ├── cli.py                # Click CLI (6 commands)
│       ├── main.py               # Pipeline orchestrator (5-step)
│       ├── paper_fetcher.py      # arXiv + S2 + OpenReview fetcher
│       ├── paper_screener.py     # Keyword scoring + dedup + selection
│       ├── note_generator.py     # Deep-read Markdown (10-section)
│       ├── obsidian_pusher.py    # Obsidian: Daily / Projects / MOCs
│       └── config.yaml           # Built-in default config
├── setup_scheduler.ps1           # Windows Task Scheduler management
├── run_pipeline.bat.example      # Batch file template
├── requirements.txt              # PyYAML >= 6.0, click >= 8.0
├── handoff.md                    # Changelog + docs
├── .gitignore
├── logs/
│   └── automation.log            # Per-run log (auto-appended)
└── note/                         # Generated notes (gitignored)
    ├── _汇总清单.md                # Bilingual summary checklist
    └── *-论文精读.md               # Per-paper deep-read notes
```

---

## Obsidian integration

After `deeppaper run --push`, DeepPaper writes into your Obsidian vault:

| Target    | Path Pattern              | Content                            |
|-----------|---------------------------|------------------------------------|
| **Daily** | `Daily/YYYY-M-D/`         | Deep-read notes for today's run    |
| **Project** | `Projects/{Name}/`      | Notes grouped by research direction |
| **MOC**   | `MOCs/{方向}.md`          | `[[wikilinks]]` auto-appended      |

Example after a run:

```
KB/
├── Daily/2026-7-28/
│   └── VLMR1-...-论文精读.md
├── Projects/project-4/
│   └── VLMR1-...-论文精读.md
└── MOCs/project-4.md   ← [[VLMR1|VLMR1: Stable...]]
```

---

## Deep-read note format

Each generated note follows a 10-section structure:

1. **论文信息** — Paper metadata (title, authors, year, venue, DOI, citations)
2. **核心问题与动机** — Core problem & motivation
3. **方法** — Method (with ASCII architecture diagram)
4. **技术原理** — Technical principles (LaTeX-heavy)
5. **理论分析** — Theoretical analysis (stability, convergence, energy landscape)
6. **实验结果** — Experimental results (SOTA comparison table)
7. **优势与局限** — Strengths & limitations
8. **与相关工作的关系** — Relationship to related work (comparison table)
9. **对相关领域的启示** — Implications for adjacent fields
10. **总结与评价** — Summary & 5-dimension rating table

---

## Two-phase workflow

DeepPaper is designed around a **human-in-the-loop** review step:

```
Phase 1: deeppaper run
         → Fetch, screen, generate checklist
         → Output: note/_汇总清单.md (bilingual abstracts)

Phase 2: Review + decide
         → deeppaper run --push
         → Persist selected notes to Obsidian vault
```

This prevents low-quality papers from polluting your knowledge base.

---

## Contributing

This is a personal research tool, but PRs are welcome. Most impactful contributions:

- Additional data sources (bioRxiv, PubMed, OpenAlex)
- Improved keyword scoring (embedding-based similarity)
- Multi-platform scheduler support (cron, launchd)
- LLM-based abstract quality filtering

Open an issue before submitting a PR.

---

## License

MIT
