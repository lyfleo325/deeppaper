# PaperAutomation — 论文自动化筛选与精读 交接文档

> 创建: 2026-06-16 | 最后更新: 2026-06-22
> 状态: 运行中 ✅ | 定时任务: 周一/周四 11:00

---

## 项目概述

PaperAutomation 是一个全自动论文筛选、爬取、精读生成的定时管线。每周一和周四上午 11:00 (Asia/Shanghai) 自动运行，从 Arxiv、OpenReview、Semantic Scholar 三个数据源抓取最新论文，按 5 大研究方向关键词筛选推荐（每方向 2 篇），生成符合 paper-deep-read skill 格式的论文精读 Markdown 文件，推送到 Obsidian 知识库的 Daily 和 Projects 目录，并自动更新 MOC 交叉链接。

---

## 技术栈

| 组件 | 版本/说明 |
|------|----------|
| Python | 3.12.13 (Codex 运行时) |
| 配置 | PyYAML 6.0.3 |
| 翻译 | Google Translate API (translate.google.com) |
| 网络 | urllib (标准库) |
| XML解析 | xml.etree.ElementTree (标准库) |
| 调度 | Windows Task Scheduler (schtasks.exe) |
| 目标 | Obsidian Vault `C:\Users\Leo\Desktop\KB\` |

---

## 项目结构

```
PaperAutomation/
├── config.yaml              # 核心配置（方向/关键词/API/Obsidian映射，lookback_days: 730）
├── main.py                  # 主控流程（--push 标志控制Obsidian推送，含汇总清单+翻译）
├── paper_fetcher.py         # 论文抓取（Arxiv/S2/OpenReview，含指数退避重试）
├── paper_screener.py        # 论文筛选评分（关键词匹配/去重/排序）
├── note_generator.py        # 精读MD生成（10段式结构）
├── obsidian_pusher.py       # Obsidian推送（Daily/Projects/MOCs）
├── setup_scheduler.ps1      # Windows定时任务管理
├── requirements.txt         # 依赖清单 (PyYAML>=6.0)
├── handoff.md               # 本文档
├── .gitignore               # 排除 __pycache__/note/logs
├── logs/
│   └── automation.log       # 运行日志（每次运行自动追加）
└── note/                    # 本地精读输出目录（git忽略）
    ├── _汇总清单.md          # 汇总清单（含Abstract+中英双语）
    └── *-论文精读.md         # 各论文精读笔记
```

---

## 5 大研究方向定义

### 方向1：具身智能 → PhysBrain

| 维度 | 内容 |
|------|------|
| Obsidian项目 | `Projects/PhysBrain` |
| 标签 | `embodied-ai`, `PhysBrain` |
| 核心关键词 | embodied intelligence, embodied AI, robot learning, world model, embodied foundation model, manipulation, navigation, sim-to-real, VLA, humanoid robot |
| 辅助关键词 | benchmark embodied, robot dataset, simulation, grasping, locomotion, task planning |
| 排除词 | medical, bio, chemistry |
| 顶会过滤 | CoRL, ICRA, IROS, RSS, NeurIPS, ICLR, ICML, CVPR |

### 方向2：能量原理 → 能量原理

| 维度 | 内容 |
|------|------|
| Obsidian项目 | `Projects/能量原理` |
| 标签 | `energy-principles`, `能量原理` |
| 核心关键词 | energy-based model, transformer architecture, attention mechanism, SSM, Mamba, RWKV, sparse attention, MoE, quantization, optimization landscape, neural tangent kernel |
| 辅助关键词 | pre-training efficiency, scaling law, gradient flow, convergence, information bottleneck, free energy, variational inference |
| 排除词 | computer vision, image segmentation, object detection |
| 顶会过滤 | NeurIPS, ICLR, ICML, JMLR, TMLR, COLT |

### 方向3：科研智能体 → 科研智能体

| 维度 | 内容 |
|------|------|
| Obsidian项目 | `Projects/科研智能体` |
| MOC链接 | `MOCs/智能体` |
| 标签 | `research-agent`, `科研智能体` |
| 核心关键词 | AI scientist, research agent, scientific discovery, automated research, deep research, LLM agent, multi-agent, tool use, code generation agent, science of science |
| 辅助关键词 | agent benchmark, SWE-bench, agent framework, planning, self-improvement, RAG agent |
| 排除词 | game, dialogue system, chatbot |

### 方向4：多模态认知大模型 → 多模态

| 维度 | 内容 |
|------|------|
| Obsidian项目 | `Projects/多模态` |
| 标签 | `multimodal`, `多模态` |
| 核心关键词 | multimodal LLM, VLM, MLLM, visual reasoning, latent reasoning, chain of thought multimodal, video understanding, cross-modal, vision transformer |
| 辅助关键词 | inference acceleration, KV cache, token compression, long context, continual learning, spatial reasoning |
| 排除词 | medical imaging, remote sensing, satellite |

### 方向5：AI算力集群 → AI算力集群

| 维度 | 内容 |
|------|------|
| Obsidian项目 | `Projects/AI算力集群` |
| 标签 | `ai-infrastructure`, `AI算力集群` |
| 核心关键词 | FlashAttention, HPC, GPU cluster, distributed training, model parallelism, NCCL, NVLink, RDMA, kernel fusion, CUDA |
| 辅助关键词 | inference optimization, speculative decoding, quantization inference, mixed precision, Triton, XLA, memory optimization |
| 排除词 | blockchain, cryptocurrency, edge computing IoT |

---

## 5 步管线流程

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: Fetch                                            │
│ ├── Arxiv recent (100篇, 近14天, 8个类别)                 │
│ ├── Arxiv keyword search (每方向3个primary词 × 10篇)      │
│ ├── Semantic Scholar keyword search (每方向2词 × 10篇)    │
│ └── OpenReview keyword search (每方向2词 × 10篇)          │
│                          ↓                               │
│ Step 2: Screen                                           │
│ ├── 全量去重（标题前80字符）                                │
│ ├── 逐方向关键词匹配打分                                   │
│ │  ├── 标题匹配 primary: +3/词                            │
│ │  ├── 摘要匹配 primary: +0.5/词                          │
│ │  ├── 时效性（7天内+10, 14天内+7）                       │
│ │  ├── 顶会加成（NeurIPS等+5）                            │
│ │  ├── 引用数（log2 缩放）                                │
│ │  └── 排除词惩罚（命中-100）                             │
│ └── 每方向选 Top-2                                        │
│                          ↓                               │
│ Step 3: Generate                                         │
│ └── 论文精读MD（10段式结构 + YAML frontmatter）            │
│                          ↓                               │
│ Step 4: Push                                             │
│ ├── Daily 目录: KB\Daily\YYYY-M-D\<Paper>-论文精读.md    │
│ ├── Project 目录: KB\Projects\<方向>\<Paper>-论文精读.md │
│ └── MOC 更新: 项目MOC + 全局MOC                           │
│                          ↓                               │
│ Step 5: Verify                                           │
│ └── 检查文件存在性 && 大小 > 100 bytes                     │
└─────────────────────────────────────────────────────────┘
```

---

## 输出格式（论文精读 MD）

遵循 `paper-deep-read` skill 的 10 段式结构：

```
---
title: "<论文标题>"
tags:
  - paper-reading
  - <方向tag>
  - <项目名>
aliases:
  - "<短名称>"
created: <日期>
source: <arXiv ID / DOI>
status: 待精读
---

# 📄 <论文标题>

## 一、论文信息 (表格)
## 二、核心问题与动机 (含完整摘要)
## 三、方法 (待精读后补充)
## 四、技术原理 (待精读后补充)
## 五、理论分析 (待精读后补充)
## 六、实验结果 (空表格)
## 七、优势与局限 (待精读后补充)
## 八、与相关工作的关系 (空表格)
## 九、对<方向>方向的启示 (待精读后补充)
## 十、总结与评价 (5维度评分表)
## 🔗 关联笔记 (Wiki-links to Projects & MOCs)
```

---

## Windows 定时任务

```
任务名:          PaperAutomation
描述:            论文自动化筛选与精读 - 每周一/周四 11:00 CST
命令:            python.exe main.py
工作目录:        project\PaperAutomation\
频率:            每周一 + 周四
时间:            11:00 AM
重试:            3次，间隔15分钟
超时:            30分钟
需要网络:        是
```

### 管理命令
```powershell
cd project\PaperAutomation

# 查看状态
.\setup_scheduler.ps1 -Status

# 重新注册
.\setup_scheduler.ps1

# 手动运行
python main.py

# 删除任务
.\setup_scheduler.ps1 -Remove
```

---

## API 数据源详情

### Arxiv API
- 端点: `https://export.arxiv.org/api/query`
- 限流: 无官方限制，建议每次请求间隔 ≥1s
- 分类: `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `cs.RO`, `cs.AR`, `cs.DC`, `stat.ML`
- 回溯: 730 天 (2年)
- 超时: 10s，指数退避重试 (最多3次)
- 优化: 添加 Referer 头避免 429/503

### Semantic Scholar API
- 端点: `https://api.semanticscholar.org/graph/v1/paper/search`
- 限流: 免费层 100 请求/5分钟（当前容易 429）
- 状态: 正常限流，不影响整体流程

### OpenReview API
- 端点: `https://api2.openreview.net/notes/search`
- 限流: 宽松
- 优势: 可获取同行评审信息

---

## 错误处理机制

| 错误类型 | 处理策略 |
|----------|----------|
| API 超时 (10s) | 指数退避重试3次（2s→4s→8s），仍失败则跳过 |
| API 429/503 限流 | 退避等待（3s/6s/12s），仍失败则记录跳过 |
| S2 API 429 限流 | 记录日志，不影响其他数据源 |
| 翻译 API 超时 | 回退保留原文，不中断管线 |
| XML 解析失败 | 跳过单条记录继续 |
| 零论文返回 | 记录警告，不中断管线 |
| Obsidian 路径不存在 | 自动创建目录 |
| MOC 文件不存在 | 跳过 MOC 更新 |
| 整体管线异常 | 全部捕获，写入日志 |

---

## 配置修改指南

### 调整筛选精度

编辑 `config.yaml`，在各方向下修改：

```yaml
keywords:
  primary:    # 标题命中+3, 摘要+0.5
  secondary:  # 标题命中+1.5, 摘要+0.25
  exclude:    # 命中-100 直接排除
```

### 调整推荐数量

```yaml
papers_per_direction: 2  # 改为 3 每方向3篇
```

### 禁用/启用数据源

```yaml
sources:
  arxiv:
    enabled: true          # false 禁用
  semantic_scholar:
    enabled: true
  openreview:
    enabled: true
```

### 添加新方向

在 `config.yaml` 的 `directions` 列表追加：

```yaml
- name: "新方向名称"
  ob_project: "Obsidian项目名"
  tag: "tag-name"
  moc_link: "MOC名称"
  keywords:
    primary: ["keyword1", "keyword2", ...]
    secondary: ["keyword1", ...]
    exclude: ["exclude1", ...]
  venue_filter: ["NeurIPS", "ICLR", ...]
```

同时更新 `obsidian.projects` 和 `obsidian.mocs` 映射。

---

## 已知问题

| # | 问题 | 影响 | 计划 |
|---|------|------|------|
| 1 | S2 API 频繁 429 | 部分论文缺失 | 低优先级 - Arxiv + OR 已覆盖主流 |
| 2 | 关键词匹配为启发式，偶有误分类 | 小概率跨方向论文 | 持续调优 config.yaml 关键词 |
| 3 | Science 期刊无直接 API | 顶级刊物覆盖不足 | 后续通过 S2/CORE API 间接抓取 |

---

## 变更记录

| 日期 | 变更 | 说明 |
|------|------|------|
| 2026-06-16 | 初始创建 | 完整5步管线、5方向配置、三源抓取、Obsidian推送 |
| 2026-06-16 | 首次运行 | 成功抓取100+篇，筛选12篇，推送至Obsidian |
| 2026-06-16 | 定时任务注册 | Windows Task Scheduler 周一/周四 11:00 |
| 2026-06-17 | 目录迁移 | 从 `paper_automation/` 迁移到 `project/PaperAutomation/` |
| 2026-06-17 | 路径修复 | config.yaml 用正斜杠避免YAML转义问题 |
| 2026-06-17 | 文档创建 | 创建本交接文档，更新根 handoff.md |
| 2026-06-17 | Arxiv优化 | 10s超时+指数退避重试，耗时363s→82s (4.4×) |
| 2026-06-17 | 本地优先 | local-only模式（默认），--push 标志控制Obsidian推送 |
| 2026-06-17 | 汇总清单 | 生成 _汇总清单.md，含完整Abstract+中英双语翻译 |
| 2026-06-17 | 翻译集成 | Google Translate API，需Referer头（国内可用） |
| 2026-06-17 | 范围扩展 | lookback_days 14→730（2年），paper_search.js同步更新 |
| 2026-06-17 | 精读生成 | 10篇论文自动精读，10段式完整结构，同步Obsidian Daily |
| 2026-06-17 | MOC更新 | 6条新增MOC交叉链接，覆盖PhysBrain/能量原理/多模态/AI算力 |
| 2026-06-17 | 交接文档 | 更新handoff.md，补充工作流模式/翻译/精读生成说明 |
| 2026-06-18 | 工作流重构 | Checklist输出到Obsidian Daily，命名YYYY-M-D PaperAuto Checklist |
| 2026-06-18 | 推荐增强 | 每篇论文含推荐原因+方向关联分析+勾选框审阅机制 |
| 2026-06-18 | 流程分离 | 审阅→精读→推送三阶段，用户决定精读范围 |
| 2026-06-18 | 精读执行 | 8篇6/18推荐论文完成10段式精读，同步Obsidian Daily |
| 2026-06-18 | 交接同步 | handoff.md补充推荐原因函数/Checklist结构，同步Obsidian |
| 2026-06-22 | 电池修复 | 定时任务禁用电池限制(DisallowStartIfOnBatteries=false)，避免电源模式跳过 |
| 2026-06-22 | 依赖检查 | main.py启动时check_dependencies()自动安装缺失的PyYAML |
| 2026-06-22 | 手动补跑 | 6/22周一管线手动运行，92.6s完成10篇推荐 |

---

---

## 工作流模式 (2026-06-18 更新)

### 审阅优先模式（默认）

```bash
# 默认运行：抓取 → 筛选 → 生成 Checklist 到 Obsidian Daily → 停止
python main.py
```

产出：
- Obsidian Daily 目录生成 `YYYY-M-D PaperAuto Checklist.md`
- Checklist 包含：快速索引表 + 每篇论文的英中双语摘要 + **推荐原因与方向关联分析**
- 每篇论文前有 `[ ]` 勾选框，用户审阅后标记需精读的论文
- 同时在本地 `note/_Checklist.md` 保存副本

### 用户审阅

1. 打开 Obsidian Daily 中的 `PaperAuto Checklist`
2. 阅读摘要和推荐原因，勾选 `[x]` 需精读的论文
3. 在 Codex 中告知：**对勾选的论文进行精读**

### 精读模式

Codex 按用户勾选执行论文精读（paper-deep-read skill），输出到 Obsidian Daily。

### 关键函数说明

| 函数 | 位置 | 说明 |
|------|------|------|
| `generate_summary_list()` | main.py | 生成 PaperAuto Checklist，输出到 Obsidian Daily |
| `_generate_recommendation_reason()` | main.py | 基于关键词匹配和方向模板生成推荐原因 |
| `_translate_abstract()` | main.py | Google Translate 英→中翻译，需 Referer 头 |
| `_retry_request()` | paper_fetcher.py | 指数退避重试（3次，2s→4s→8s） |

### Obsidian 推送模式

```bash
# 精读完成后，推送至 Obsidian Projects + MOCs
python main.py --push
```

### 关键函数说明

| 函数 | 位置 | 说明 |
|------|------|------|
| `generate_summary_list()` | main.py | 生成 PaperAuto Checklist，输出到 Obsidian Daily |
| `_generate_recommendation_reason()` | main.py | 基于关键词匹配和方向模板生成推荐原因 |
| `_translate_abstract()` | main.py | Google Translate 英→中翻译，需 Referer 头 |
| `_retry_request()` | paper_fetcher.py | 指数退避重试（3次，2s→4s→8s） |

### Obsidian 推送模式

```bash
# 审阅确认后，推送至 Obsidian Daily + Projects + MOCs
python main.py --push
```

### 定时任务说明

Windows Task Scheduler 仍自动运行 `python main.py`（本地模式），
生成的笔记存入 `note/` 供人工审阅，**不会**自动推送到 Obsidian。
审阅后手动执行 `python main.py --push`。

---

## 精读笔记自动生成 (2026-06-17 新增)

`main.py` 内置 `_translate_abstract()` 函数，在生成汇总清单时自动：

1. 调用 Google Translate API (`translate.google.com`) 翻译英文摘要
2. 需要 `Referer: https://translate.google.com/` 头（国内网络可用）
3. 翻译失败时回退保留原文，不中断流程

精读笔记生成规则：
- 根据摘要关键词自动分析方法/技术原理/理论
- 填充 10 段式完整结构
- 评分：创新性/技术深度/实验充分/可复现性/影响力 (1-5)


---

## 已知陷阱 (2026-06-22 新增)

| 陷阱 | 现象 | 修复 |
|------|------|------|
| 电池模式跳过 | 周一/周四 11:00 未运行，Next Run 跳到下次 | 运行: `powershell -Command "$task = Get-ScheduledTask -TaskName 'PaperAutomation'; $task.Settings.DisallowStartIfOnBatteries = $false; $task.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -TaskName 'PaperAutomation' -Settings $task.Settings"` |
| PyYAML 丢失 | `ModuleNotFoundError: No module named 'yaml'` | main.py 已内置自动安装，或手动 `pip install PyYAML` |

## 依赖

```
PyYAML>=6.0
```
（其余均为 Python 标准库，无需额外安装）
