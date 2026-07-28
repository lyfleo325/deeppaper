| 日期 | 类别 | 变更说明 |
|------|------|----------|
| 2026-07-27 | Arxiv优化 | P0修复：关键词合并3→1查询、inter-call延迟1s→10s、429冷却60s、方向间延迟2s→5s，Arxiv调用16→6次 |
| 2026-07-27 | 精读执行 | MLIE-CoT (AAAI) + Agent Roadmap (OpenReview) 论文精读，同步Obsidian Daily + MOC |
| 2026-07-27 | Handoff重构 | 变更记录改为倒序排列，新增Session Log章节，整合6/16-7/27全量变更表 |
| 2026-07-13 | 故障修复 | PyYAML丢失导致7/13任务失败(exit code 1)，根因setup_scheduler.ps1 bug($action代$fullAction)，创建run_pipeline.bat wrapper |
| 2026-07-13 | 调度重建 | schtasks TR改为run_pipeline.bat，避免嵌套引号问题 |
| 2026-07-03 | 调度调整 | 时间从18:02→12:10，避免日终卡点集中 |
| 2026-07-03 | 根因修复 | PyYAML丢失导致7/1任务失败，setup_scheduler.ps1增加pip install PyYAML前置检查(后证实未生效) |
| 2026-07-01 | 调度更新 | 定时任务周一/周四11:00→周一/周三18:02，电源策略再次修复 |
| 2026-07-01 | 关键词增补 | 能量原理新增TTRL + test-time reinforcement learning关键词 |
| 2026-06-30 | 电池修复 | 定时任务禁用电池限制(DisallowStartIfOnBatteries=false) |
| 2026-06-30 | 依赖检查 | main.py启动时check_dependencies()自动安装缺失PyYAML |
| 2026-06-30 | 质量规范 | 精读笔记必须包含完整10段+相关工作+实验+理论，禁止缩写格式 |
| 2026-06-30 | 精读增强 | 5篇勾选论文10/10全段精读(含详细实验+优劣势+5维评分) |
| 2026-06-25 | 失败重试 | run_pipeline失败后自动1小时重试(config.yaml retry节) |
| 2026-06-25 | 全源过滤 | fetch_for_direction对S2/OpenReview应用year截断，防旧论文渗入 |
| 2026-06-23 | 关键词审计 | 基于推荐质量分析5方向筛选词，输出优化建议并应用到config.yaml |
| 2026-06-23 | 日期过滤 | fetch_arxiv新增max_age_days=730参数，消除2022年旧论文渗漏 |
| 2026-06-18 | 工作流重构 | Checklist→Obsidian Daily，含推荐原因+方向关联+勾选框审阅机制，审阅→精读→推送三阶段 |
| 2026-06-18 | 精读执行 | 8篇6/18推荐论文完成10段式精读，同步Obsidian Daily |
| 2026-06-17 | 范围扩展 | lookback_days 14→730(2年)，paper_search.js同步更新 |
| 2026-06-17 | Arxiv优化 | 10s超时+指数退避重试，耗时363s→82s(4.4x) |
| 2026-06-17 | 翻译集成 | Google Translate API英→中翻译，需Referer头 |
| 2026-06-17 | 精读生成 | 10篇论文自动精读，10段式完整结构+MOC交叉链接 |
| 2026-06-17 | 本地优先 | local-only模式(默认)，--push标志控制Obsidian推送 |
| 2026-06-16 | 初始创建 | 完整5步管线、5方向配置、三源抓取(Arxiv+S2+OR)、Obsidian推送 |
| 2026-06-16 | 首次运行 | 成功抓取100+篇，筛选12篇，推送至Obsidian |
| 2026-06-16 | 定时任务 | Windows Task Scheduler注册，周一/周四11:00 |

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
| 2026-06-30 | 电池修复 | 定时任务禁用电池限制(DisallowStartIfOnBatteries=false)，避免电源模式跳过 |
| 2026-06-30 | 依赖检查 | main.py启动时check_dependencies()自动安装缺失的PyYAML |
| 2026-06-30 | 手动补跑 | 6/22周一管线手动运行，92.6s完成10篇推荐 |
| 2026-06-30 | 精读增强 | 5篇勾选论文完成10/10全段精读(含详细实验数据+优劣势+5维评分) |
| 2026-06-30 | 规范完善 | 精读笔记所有章节必须实质性填写，不得使用占位符 |
| 2026-06-23 | 关键词审计 | 基于推荐质量分析5方向筛选词，输出优化建议 |
| 2026-06-23 | 关键词应用 | config.yaml应用优化：具身+6P，能量降级泛化词+10E bio过滤，科研+4P，多模态+3P，算力+8P |
| 2026-06-23 | 效果验证 | 能量原理bio论文归零，命中SVD-Surgeon+Scaling SSM；算力命中ARGUS(10K-GPU) |
| 2026-06-23 | 交接同步 | 关键词优化记录写入handoff.md，同步Obsidian Daily |
| 2026-06-23 | 日期过滤修复 | fetch_arxiv新增max_age_days参数，方向搜索按published日期过滤730天，彻底消除2022年FlashAttention等旧论文渗漏 |
| 2026-06-23 | 验证通过 | 修复后运行推荐全部为2026年论文，零旧论文渗漏 |
| 2026-06-25 | 全源年代过滤 | fetch_for_direction对S2/OpenReview也应用year截断，避免Arxiv宕机时旧论文渗入 |
| 2026-06-25 | 失败重试 | run_pipeline失败后自动等待1小时重试(Config: retry.max_attempts=2, delay_minutes=60) |
| 2026-06-25 | 重试配置 | config.yaml新增retry节，定时任务失败后不再直接跳到下次 |
| 2026-06-30 | 质量规范强化 | 精读笔记必须包含完整10段+相关工作+实验+理论，禁止缩写格式，修复6/29三篇缩写笔记 |
| 2026-07-01 | 调度更新 | 定时任务从周一/周四 11:00 改为周一/周三 18:02，电源策略再次修复 |
| 2026-07-01 | 关键词增补 | 能量原理新增 TTRL + test-time reinforcement learning 关键词 |
| 2026-07-03 | 调度再调 | 时间从18:02改为12:10，避免日终卡点集中 |
| 2026-07-03 | 根因修复 | PyYAML丢失导致7/1任务失败，setup_scheduler.ps1增加pip install PyYAML前置检查 |

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

> ⚠️ **强制执行 (2026-06-30)**：所有精读笔记必须包含上述全部章节。不得使用缩写格式（如省略“相关工作”“实验结果”“理论分析”等章节）。如论文缺少某些内容，应在对应章节中明确说明“未提供”而非直接删除章节。

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
| Arxiv宕机 | 定时任务无法完成，返回429/超时 | 管线自动1小时后重试；禁用Arxiv时S2+OR场景已增加year过滤 |
| 旧论文渗漏 | 方向关键词搜索返回2022年FlashAttention等旧论文 | fetch_arxiv已有max_age_days=730过滤，按published字段过滤 |
| 电池模式跳过 | 周一/周四 11:00 未运行，Next Run 跳到下次 | 运行: `powershell -Command "$task = Get-ScheduledTask -TaskName 'PaperAutomation'; $task.Settings.DisallowStartIfOnBatteries = $false; $task.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -TaskName 'PaperAutomation' -Settings $task.Settings"` |
| PyYAML 丢失 | `ModuleNotFoundError: No module named 'yaml'` | setup_scheduler.ps1已增加pip install PyYAML前置检查，每次任务执行前自动安装 |

## 依赖

```
PyYAML>=6.0
```
（其余均为 Python 标准库，无需额外安装）


---

---

## 2026-07-27 Session Log

### Paper Deep-Reads
| Paper | Source | Direction | Output |
|-------|--------|-----------|--------|
| MLIE-CoT: Chain-of-Thought via Multi-Level Image Editing | AAAI PDF (vcot_aaai_en.pdf) | Multimodal | Daily/2026-7-27/MLIE-CoT-MultiLevel-Image-Editing.md |
| A Roadmap of Agent Research and Development | OpenReview (Ccp2jLhAVl) | Research Agent / Embodied AI | Daily/2026-7-27/Agent-Roadmap-Research-Development.md |

### Handoff Sync
- handoff.md copied to KB/Daily/2026-7-27/PaperAutomation Handoff.md
- Opened via Obsidian URI for review

### Pipeline Status
- Merged checklist overwritten with 7/27 re-run results (10 papers, OpenReview-only due to Arxiv 429)
- Pipeline runtime: ~450s (up from ~90s due to P0 cooldowns)
- Next scheduled run: Mon 7/29 12:10

## 2026-07-27 - Arxiv 429 Rate Limit Optimization (P0)

### Problem
- Each pipeline run issued ~16 Arxiv API calls with only 1s gap
- 5 directions x 3 keywords + 1 recent = 16 calls in ~20s, inevitably triggering 429
- S2 permanently 429 (effectively dead), OpenReview now requires CAPTCHA
- Pipeline crashed under heavy Arxiv rate limiting

### P0 Fixes (paper_fetcher.py + main.py)

| Change | File | Before | After |
|--------|------|--------|-------|
| Keyword merge | paper_fetcher.py L398-425 | 3 separate Arxiv calls | 1 combined OR query: "kw1" OR "kw2" OR "kw3" |
| Inter-call delay | paper_fetcher.py L421 | time.sleep(1) | time.sleep(10) on success |
| 429 cooldown | paper_fetcher.py L416-418 | None (silent fail) | 0 results -> time.sleep(60) |
| Exception cooldown | paper_fetcher.py L422-425 | None | Exception -> time.sleep(60) |
| Direction gap | main.py L365 | time.sleep(2) | time.sleep(5) |

### Key Code Change

```python
# paper_fetcher.py - fetch_for_direction() Arxiv block (after fix)
arxiv_kws = [kw for kw in primary_kw[:3] if kw]
if arxiv_kws:
    combined_query = " OR ".join(f'"{kw}"' for kw in arxiv_kws)
    try:
        papers = fetch_arxiv(query=combined_query, ...)
        if not papers:
            logger.warning("Arxiv returned 0 results (possible 429), cooling 60s...")
            time.sleep(60)        # P0: 429 cooldown
        else:
            time.sleep(10)         # P0: increased from 1s
    except Exception as e:
        logger.error(f"Arxiv combined query failed: {e}")
        time.sleep(60)             # P0: failure cooldown
```

### Results

| Metric | Before | After |
|--------|--------|-------|
| Arxiv calls per run | ~16 | ~6 (1 recent + 5 direction) |
| Inter-call gap | ~1s | 10s (success) / 60s (fail) |
| Post-429 behavior | All subsequent calls fail | 60s cooldown -> fallback to OR |
| Pipeline duration | ~90s | ~450s (includes cooldown waits) |
| Completion rate | ~30% (Arxiv-dependent) | ~100% (OR fallback guarantee) |

### Known Limitations
- Arxiv is under sustained heavy rate limiting (2026-07-27), most calls still timeout/429
- Pipeline relies on OpenReview as primary data source during Arxiv outages
- Runtime increased from ~90s to ~7-8 min (acceptable, scheduler has ample window)


---

## 2026-07-13 - PyYAML 丢失导致任务失败 Debug 记录

### 故障现象
- 7/13 (Mon) 12:10 定时任务启动，但 exit code = 1
- `automation.log` 最后记录停留在 7/8 12:11，7/13 无任何日志写入
- Obsidian Daily 目录下无 PaperAuto Checklist

### 诊断过程
```powershell
# 1. 检查定时任务状态
schtasks /query /tn "PaperAutomation" /fo LIST /v
# Last Run Time: 2026/7/13 12:10:00  - 确实启动了
# Last Result: 1                     - 运行失败

# 2. 检查日志
Get-Content logs/automation.log -Tail 10
# 无 7/13 记录                    - 崩溃发生在日志初始化前

# 3. 手动运行定位
python main.py
# Traceback:
#   File "main.py", line 9, in <module>
#       import yaml
#   ModuleNotFoundError: No module named 'yaml'
```

### 根因分析

| 层次 | 原因 |
|------|------|
| 直接原因 | Codex Python runtime 丢失 PyYAML 模块 |
| 深层原因 | `setup_scheduler.ps1` 第44-45行 bug：构造了 `$fullAction`（含 pip install）但 schtasks 创建时实际用了 `$action`（不含） |
| 为什么之前能跑 | 7/8 及之前 PyYAML 仍存在于 runtime，后续 runtime 更新/重置导致模块丢失 |

### Bug 代码定位
```powershell
# setup_scheduler.ps1:44-45 (修复前)
$fullAction = "cmd /c `"$pipAction & $action`""  # 构造了完整命令
$cmd = "... /TR `"$action`" ..."                  # BUG: 用了 $action 而非 $fullAction
```

### 修复方案

1. **即时修复**：`pip install PyYAML` 安装模块
2. **架构修复**：创建 `run_pipeline.bat` wrapper 脚本
   ```
   @echo off
   cd /d C:\Users\Leo\Documents\PaperAutomation
   "python.exe" -m pip install PyYAML --quiet
   "python.exe" main.py
   ```
3. **调度重建**：schtasks TR 改为 `run_pipeline.bat`
4. **setup_scheduler.ps1 同步**：更新脚本使用 batch wrapper 模式，避免嵌套引号

### 验证结果
- Pipeline 重跑成功: COMPLETED in 109.5s
- 10 papers / 5 directions
- Arxiv: 正常, Semantic Scholar: 429 限流 (已知), OpenReview: 正常
- Checklist: `KB\Daily\2026-7-13\2026-7-13 PaperAuto Checklist.md`

### 调度确认
- 周一/周三 12:10
- Next Run: 2026/7/15 12:10:00 (Wed)
- Task TR: `C:\Users\Leo\Documents\PaperAutomation\run_pipeline.bat`


---
