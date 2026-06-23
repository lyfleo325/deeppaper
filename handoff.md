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
| 2026-06-22 | 精读增强 | 5篇勾选论文完成10/10全段精读(含详细实验数据+优劣势+5维评分) |
| 2026-06-22 | 规范完善 | 精读笔记所有章节必须实质性填写，不得使用占位符 |
| 2026-06-23 | 关键词审计 | 基于推荐质量分析5方向筛选词，输出优化建议 |
| 2026-06-23 | 关键词应用 | config.yaml应用优化：具身+6P，能量降级泛化词+10E bio过滤，科研+4P，多模态+3P，算力+8P |
| 2026-06-23 | 效果验证 | 能量原理bio论文归零，命中SVD-Surgeon+Scaling SSM；算力命中ARGUS(10K-GPU) |
| 2026-06-23 | 交接同步 | 关键词优化记录写入handoff.md，同步Obsidian Daily |
| 2026-06-23 | 日期过滤修复 | fetch_arxiv新增max_age_days参数，方向搜索按published日期过滤730天，彻底消除2022年FlashAttention等旧论文渗漏 |
| 2026-06-23 | 验证通过 | 修复后运行推荐全部为2026年论文，零旧论文渗漏 |

---

## 关键词推荐优化 (2026-06-23 审计)

基于近期推荐论文质量分析，对5方向筛选关键词进行审计与优化建议。

### 审计方法
- 分析2026-06-17至06-22的50+篇推荐论文
- 评估各方向命中精度（是否匹配方向主题）
- 识别误分类案例及其根因

### 方向1：具身智能 (PhysBrain) ⭐ 精度较好

**现有关键词**: embodied intelligence, embodied AI, robot learning, world model, manipulation, navigation, sim-to-real, VLA, humanoid robot (18 primary, 9 secondary)

**审计发现**:
- "world model" 过于宽泛，命中大量非具身论文（纯CV/语言模型的世界模型）
- "humanoid robot" 命中面过窄
- 缺少"visuomotor"、"dexterous"等2025-2026前沿热词

**优化建议**:
| 变更 | 关键词 | 原因 |
|------|--------|------|
| 新增Primary | `visuomotor policy`, `dexterous manipulation` | VLA/灵巧操作前沿 |
| 新增Primary | `bimanual`, `mobile manipulation` | 双臂/移动操作 |
| 新增Primary | `robot foundation model`, `robot pretraining` | 机器人基础模型 |
| 新增Secondary | `imitation learning robotics`, `RL robotics` | 明确标注robotics避免泛化 |
| 降级 | `world model` → `world model robotics` | 加限定词降噪 |
| 新增Exclude | `language model` (不含robot/embodied) | 过滤纯NLP世界模型 |

### 方向2：能量原理 ⚠️ 精度较差，需重点优化

**现有关键词**: energy-based model, transformer architecture, attention mechanism, SSM, Mamba, MoE, quantization, optimization landscape (20 primary, 13 secondary)

**审计发现**:
- "transformer architecture"、"attention mechanism" 命中几乎所有ML论文，方向辨识度极低
- "SSM" 和 "Mamba" 单独作为关键词会误匹配应用类论文（如语义分割）
- Moebius(图像修复)误分类：仅因涉及"高效架构"被归入
- 能量原理的本质是"模型架构效率与学习动力学的理论分析"，非具体架构名称

**优化建议（聚焦方向本质）**:
| 变更 | 关键词 | 原因 |
|------|--------|------|
| **保留Primary** | `energy-based model`, `learning dynamics`, `optimization landscape`, `neural scaling law` | 核心理论方向 |
| **保留Primary** | `state space model Mamba` (合并), `mixture of experts routing` | 加限定词提纯 |
| 新增Primary | `model compression theory`, `pruning theory` | 模型压缩的理论分析 |
| 新增Primary | `training dynamics analysis`, `loss landscape analysis` | 训练动力学 |
| 降级Secondary | `transformer architecture`, `attention mechanism` | 太泛→仅辅助 |
| 降级Secondary | `SSM`, `Mamba` (单独) | 移到辅助避免独立匹配 |
| 新增Secondary | `information bottleneck deep learning`, `neural collapse` | 理论框架 |
| 新增Exclude | `semantic segmentation`, `object detection` | 过滤纯应用CV |
| 新增Exclude | `image inpainting`, `image generation` | 过滤生成式CV |

### 方向3：科研智能体 ✅ 精度好

**现有关键词**: AI scientist, research agent, LLM agent, multi-agent, tool use, code generation agent (15 primary, 12 secondary)

**审计发现**: 命中精度较高，推荐论文均与科研自动化/多智能体直接相关。

**优化建议（小幅增强）**:
| 变更 | 关键词 | 原因 |
|------|--------|------|
| 新增Primary | `agentic workflow`, `agent orchestration` | 2025-2026热词 |
| 新增Primary | `LLM-based agent`, `tool-augmented LLM` | 补充表达 |
| 新增Secondary | `agentic AI framework`, `autonomous coding` | 扩展覆盖 |
| 新增Secondary | `agent evaluation benchmark` | 评估方向 |
| 新增Exclude | `reinforcement learning game agent` | 过滤游戏RL |

### 方向4：多模态认知大模型 ✅ 精度较好

**现有关键词**: multimodal LLM, VLM, MLLM, visual reasoning, chain of thought multimodal, video understanding, cross-modal (15 primary, 12 secondary)

**审计发现**: 命中精度较高。StylisticBias虽非传统VLM，但从"多模态认知"角度（MLLM偏见分析）仍有价值。

**优化建议（小幅增强）**:
| 变更 | 关键词 | 原因 |
|------|--------|------|
| 新增Primary | `multimodal agent`, `embodied VLM` | 多模态智能体 |
| 新增Primary | `visual instruction tuning` | 指令微调 |
| 新增Secondary | `3D scene understanding VLM` | 3D方向 |
| 新增Secondary | `multimodal alignment`, `visual grounding` | 对齐/接地 |
| 降级Secondary | `KV cache` (移到AI算力) | 更属于算力方向 |

### 方向5：AI算力集群 ⚠️ 精度较差，需结构调整

**现有关键词**: FlashAttention, HPC, GPU cluster, distributed training, model parallelism, NCCL, NVLink, RDMA, CUDA (19 primary, 14 secondary)

**审计发现**:
- 核心关键词过于偏向硬件/网络层（NCCL/NVLink/RDMA），命中面极窄
- 大量LLM推理优化论文未被捕获（因关键词不匹配）
- "Surgical embodied intelligence"误分类：可能"cluster"一词命中

**优化建议（扩大覆盖面）**:
| 变更 | 关键词 | 原因 |
|------|--------|------|
| **保留Primary** | `FlashAttention`, `GPU kernel optimization`, `distributed training` | 核心 |
| 新增Primary | `LLM inference optimization`, `LLM serving system` | 推理优化热区 |
| 新增Primary | `KV cache optimization`, `speculative decoding` | 从secondary提升 |
| 新增Primary | `attention optimization`, `mixture of experts inference` | 注意力/MoE加速 |
| 新增Primary | `continuous batching`, `model quantization deployment` | 部署优化 |
| 降级Secondary | `NCCL`, `NVLink`, `RDMA` | 仅辅助上下文 |
| 新增Secondary | `paged attention`, `prefix caching` | 新兴技术 |
| 新增Secondary | `tensor parallelism`, `pipeline parallelism` (保留) | 继续辅助 |
| 新增Exclude | `robotic surgery`, `laparoscopic` | 过滤手术机器人 |
| 新增Exclude | `medical imaging` | 过滤医疗影像 |

---

## 推荐实施顺序

1. **立即实施**: 方向2(能量原理)和方向5(AI算力集群)的关键词调整，精度提升最大
2. **本周内**: 方向1(具身智能)的world model限定和热词补充
3. **可选**: 方向3(科研智能体)和方向4(多模态)的小幅优化
4. **验证方式**: 修改后运行3-5次管线，观察各方向命中精度的变化

### 验证结果 (2026-06-23)

修改后运行2次管线验证：

| 方向 | 优化前命中（典型） | 优化后命中 | 改善 |
|------|-------------------|-----------|------|
| 具身智能 | Holodeck, ThinkingVLA | BiliVLA, KEMO | VLA/长期规划前沿 |
| 能量原理 | biomolecular energy (2016), Lamarckian (1998) ❌ | SVD-Surgeon, Scaling SSM ✅ | **bio论文归零** |
| 科研智能体 | Technical Taxonomy, Contagion | MAS-PromptBench, StickyInvoc | prompt优化方向 |
| 多模态 | SpatialRGPT, StylisticBias | AIR, Each Judge | 推理+VLM评估 |
| AI算力 | STREAM, Dynamic HPC | **ARGUS(10K-GPU)**, STREAM | 万卡集群命中 ✅ |

**结论**: 方向2和方向5精度显著提升，方向1/3/4保持良好匹配。后续建议定期（每2周）审计命中质量。


---

## 精读笔记质量标准 (2026-06-22)

每篇精读笔记必须满足以下要求：

| 章节 | 最低要求 |
|------|----------|
| 一、论文信息 | 含标题/作者/年份/arXiv/分类/方向的完整表格 |
| 二、核心问题与动机 | 完整英文摘要 + 中文翻译 |
| 三、方法 | 基于摘要关键词的具体方法分析(3-4点) |
| 四、技术原理 | 不少于3句话的实质性技术解读 |
| 五、理论分析 | 不少于2点的理论支撑说明 |
| 六、实验结果 | 含数据集/指标/结果/基线的4行实验表格 |
| 七、优势与局限 | 各3-4条具体分析(非泛化描述) |
| 八、相关工作 | 对比表格 |
| 九、方向启示 | 针对具体方向的实质性启示 |
| 十、总结与评价 | 含5维评分的总结(创新性/技术深度/实验/可复现/影响力) |
| 🔗 关联笔记 | Wiki-link到Project和MOC |

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
| 旧论文渗漏 | 方向关键词搜索返回2022年FlashAttention等旧论文 | fetch_arxiv已有max_age_days=730过滤，按published字段过滤 |
| 电池模式跳过 | 周一/周四 11:00 未运行，Next Run 跳到下次 | 运行: `powershell -Command "$task = Get-ScheduledTask -TaskName 'PaperAutomation'; $task.Settings.DisallowStartIfOnBatteries = $false; $task.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -TaskName 'PaperAutomation' -Settings $task.Settings"` |
| PyYAML 丢失 | `ModuleNotFoundError: No module named 'yaml'` | main.py 已内置自动安装，或手动 `pip install PyYAML` |

## 依赖

```
PyYAML>=6.0
```
（其余均为 Python 标准库，无需额外安装）
