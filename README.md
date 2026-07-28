# PaperAutomation + Paper Reading + Obsidian Wiki

<p align="center">
  <a href="https://github.com/lyfleo325/deeppaper"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" /></a>
  <a href="https://github.com/lyfleo325/deeppaper/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey.svg" alt="Platform" />
</p>

> **DeepPaper** ? A fully automated academic paper discovery, screening, and deep-reading pipeline.  
> Three sources. Five research directions. Your Obsidian knowledge base, always up to date.

The idea is simple: you define the research directions you care about, and DeepPaper periodically scans arXiv, Semantic Scholar, and OpenReview for the most relevant new papers, scores them, generates bilingual summaries, and pushes deep-reading notes into your [Obsidian](https://obsidian.md) vault ? with `[[wikilinks]]` to your existing MOCs. You review the checklist, then decide what gets persisted.

---

## Quick Start

### Prerequisites

- **Python 3.10+** (tested on 3.12)
- **Windows** (Task Scheduler integration; code works cross-platform but scheduling is Windows-only)
- **Obsidian** (optional ? pipeline runs fully offline without it)

### pip install

```bash
pip install deeppaper

# Or install from source:
git clone https://github.com/lyfleo325/deeppaper.git
cd deeppaper
pip install -e .
```

### First run

```bash
# Initialize your config (writes config.yaml to current directory)
deeppaper setup

# Edit config ? set your Obsidian vault path
deeppaper config --edit

# Check everything is ready
deeppaper doctor

# Run the pipeline (local-only)
deeppaper run

# After reviewing checklist, push to Obsidian
deeppaper run --push
```

---

## CLI Reference

```
deeppaper ? command-line interface

Commands:
  run         Run the full paper pipeline
  setup       Initialize config.yaml from built-in template
  config      Display or edit current configuration
  doctor      Environment health check
  directions  List all research directions with keywords
  schedule    Manage Windows scheduled task
```

### `deeppaper run`

```bash
deeppaper run              # Generate checklist (local-only)
deeppaper run --push       # Push deep-read notes to Obsidian
deeppaper run -d ????    # Only run one direction
deeppaper run -d ???? -d ???  # Run specific directions
```

### `deeppaper doctor`

```bash
deeppaper doctor
```

Checks: Python version, PyYAML, Click, config.yaml, Obsidian vault path, source configuration, research directions.

### `deeppaper directions`

```bash
deeppaper directions
```

Lists all 5 research directions with their keyword sets, exclusions, and venue filters.

### `deeppaper config`

```bash
deeppaper config           # Display current config summary
deeppaper config --edit    # Open config.yaml in Notepad
```

### `deeppaper setup`

```bash
deeppaper setup              # Create config.yaml in cwd
deeppaper setup -o my.yaml   # Custom output path
deeppaper setup --force      # Overwrite existing config
```

### `deeppaper schedule`

```bash
deeppaper schedule install  # Create Windows scheduled task (Mon/Wed 12:10)
deeppaper schedule status   # Check task status
deeppaper schedule remove   # Remove scheduled task
```

---

## What it does

DeepPaper runs a **5-step pipeline** every cycle:

```
????????????????    ????????????????    ????????????????    ????????????????    ????????????????
?  1. FETCH    ? ? ?  2. SCREEN   ? ? ?  3. GENERATE  ? ? ?  4. PUSH     ? ? ?  5. VERIFY   ?
?              ?    ?              ?    ?              ?    ?              ?    ?              ?
? arXiv        ?    ? keyword      ?    ? deep-read    ?    ? Daily/       ?    ? file size    ?
? Semantic     ?    ? scoring      ?    ? markdown     ?    ? Projects/    ?    ? check +      ?
? Scholar      ?    ? + dedup      ?    ? + bilingual  ?    ? MOCs         ?    ? path verify  ?
? OpenReview   ?    ? + top-2 per  ?    ? abstract     ?    ? (--push      ?    ?              ?
?              ?    ? direction    ?    ? translation  ?    ?  only)       ?    ?              ?
????????????????    ????????????????    ????????????????    ????????????????    ????????????????
```

**Error resilience built in:**
- Exponential backoff retry on HTTP errors (429, 503)
- arXiv query merging (3 keywords ? 1 OR query) to reduce rate-limit hits
- 60-second cooldown after 429 or exception
- Configurable retry with 60-minute delay between attempts

---

## Five research directions

Each direction has curated keyword sets (primary + secondary), exclusion filters, and venue constraints ? all in `config.yaml`.

| # | Direction | Project Tag | Focus |
|---|-----------|-------------|-------|
| 1 | **Embodied AI** | `PhysBrain` | Robot learning, VLA, manipulation, sim-to-real, humanoid |
| 2 | **Energy Principles** | `????` | EBMs, SSMs, MoE, learning dynamics, optimization landscape |
| 3 | **Research Agents** | `?????` | AI Scientist, multi-agent, tool use, autonomous research |
| 4 | **Multimodal Models** | `???` | VLM, MLLM, visual reasoning, multimodal alignment, OPD/GRPO |
| 5 | **AI Infrastructure** | `AI????` | HPC, GPU clusters, distributed training, FlashAttention, inference optimization |

Each direction outputs **top 2 papers per cycle** (configurable: `papers_per_direction`).

---

## Project structure

```
deeppaper/
??? pyproject.toml                # Package metadata (setuptools)
??? src/
?   ??? deeppaper/
?       ??? __init__.py           # Package init + version
?       ??? __main__.py           # python -m deeppaper
?       ??? cli.py                # Click CLI (run/setup/config/doctor/directions/schedule)
?       ??? main.py               # Pipeline orchestrator (5-step flow)
?       ??? paper_fetcher.py      # arXiv + Semantic Scholar + OpenReview fetcher
?       ??? paper_screener.py     # Keyword scoring, deduplication, top-N selection
?       ??? note_generator.py     # Deep-read Markdown (10-section format)
?       ??? obsidian_pusher.py    # Obsidian sync: Daily / Projects / MOCs
?       ??? config.yaml           # Built-in default config (overridden by cwd/config.yaml)
??? setup_scheduler.ps1           # Windows Task Scheduler management
??? run_pipeline.bat.example      # Template batch file for scheduled runs
??? requirements.txt              # PyYAML >= 6.0, click >= 8.0
??? handoff.md                    # Changelog + project documentation
??? .gitignore
??? logs/
?   ??? automation.log            # Per-run log (auto-appended)
??? note/                         # Generated notes (gitignored)
    ??? _????.md                # Bilingual summary checklist
    ??? *-????.md               # Per-paper deep-read notes
```

---

## Obsidian integration

After `deeppaper run --push`, DeepPaper writes into your Obsidian vault:

| Target | Path Pattern | Content |
|--------|-------------|---------|
| **Daily** | `Daily/YYYY-M-D/` | Deep-read notes for today's run |
| **Project** | `Projects/{ProjectName}/` | Same notes, grouped by research direction |
| **MOC** | `MOCs/{??}.md` | `[[wikilinks]]` appended automatically |

Example vault layout after a run:

```
KB/
??? Daily/
?   ??? 2026-7-28/
?       ??? VLMR1-Stable-Generalizable-R1style-2025-????.md
??? Projects/
?   ??? ???/
?       ??? VLMR1-Stable-Generalizable-R1style-2025-????.md
??? MOCs/
    ??? ???.md   ? [[VLMR1-Stable-Generalizable-R1style-2025|VLMR1: Stable...]]
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
Phase 1: deeppaper run
         ? Fetch, screen, generate checklist only
         ? Output: note/_????.md (bilingual abstracts + recommendation reasons)

Phase 2: Read the checklist. Decide.
         ? deeppaper run --push
         ? Persist selected deep-read notes to Obsidian vault
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
