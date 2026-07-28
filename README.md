# PaperAutomation

Automated academic paper discovery, screening, and deep-reading pipeline for AI researchers.

## Overview

PaperAutomation periodically fetches recent papers from arXiv, Semantic Scholar, and OpenReview, screens them against 5 research directions using keyword matching and scoring, generates bilingual (EN/ZH) summary checklists, and optionally pushes deep-reading notes to an Obsidian knowledge base.

**5 Research Directions:**
- Embodied AI (PhysBrain)
- Energy Principles (Energy-Based Models, Learning Dynamics)
- Research Agents (AI Scientist, Multi-Agent Systems)
- Multimodal Cognitive Models (VLM, MLLM, Visual Reasoning)
- AI Infrastructure (HPC, GPU Clusters, Distributed Training)

## Quick Start

### Prerequisites
- Python 3.10+
- PyYAML >= 6.0
- Windows Task Scheduler (for automation)

### Installation
```bash
git clone https://github.com/yourusername/PaperAutomation.git
cd PaperAutomation
pip install PyYAML
```

### Configuration
Edit `config.yaml` with your settings:
```yaml
obsidian:
  kb_root: C:\path\to\your\Obsidian\vault
  daily_dir: Daily
```

### Run
```bash
# Full pipeline (generates checklist only, no Obsidian push)
python main.py

# Push to Obsidian (after reviewing checklist)
python main.py --push
```

### Schedule (Windows)
```bash
# Create scheduled task (Mon/Wed 12:10)
.\setup_scheduler.ps1

# View status
.\setup_scheduler.ps1 -Status

# Run immediately
.\setup_scheduler.ps1 -RunNow
```
> **Tip:** Copy `run_pipeline.bat.example` to `run_pipeline.bat` and update paths for auto PyYAML installation before each run.

## Architecture

```
PaperAutomation/
├── main.py                  # Pipeline orchestrator
├── config.yaml              # Directions, keywords, sources, paths
├── paper_fetcher.py         # Arxiv + S2 + OpenReview fetcher
├── paper_screener.py        # Keyword scoring + dedup + selection
├── note_generator.py        # Deep-read markdown generator
├── obsidian_pusher.py       # Obsidian Daily/Projects/MOCs sync
├── setup_scheduler.ps1      # Windows Task Scheduler management
├── requirements.txt         # PyYAML
└── handoff.md               # Project changelog & documentation
```

## Pipeline Flow

```
Fetch (Arxiv + S2 + OR)
  → Screen (keyword scoring)
    → Select (top 2 per direction)
      → Generate notes
        → Translate abstracts (Google Translate)
          → Output checklist (Obsidian Daily)
            → [User review + check]
              → Deep-read → Push to Obsidian
```

## Changelog

See `handoff.md` for detailed change history (2026-06-16 → present, reverse chronological).
