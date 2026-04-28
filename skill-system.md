# 第九章：Skill 系统——AI Agent 的可扩展技能单元

## 9.1 为什么需要 Skill

LLM 的本质是通用推理引擎——它能回答问题、写文章、写代码，但它并不知道你的工作场景中具体需要什么。一个通用的 LLM 无法自动知道：当用户说「save this」时，应该去抓取网页内容、提取作者信息、建立双向链接并写入知识库。

Skill 解决的就是这个 gap。Skill = **提示词（system prompt）+ 工具定义（tools）+ 执行步骤（instructions）**的三位一体封装。它让 LLM 在特定场景下拥有精确的行动能力，而不是每次都靠 prompt engineering 临时凑。

如果把 LLM 比作浏览器内核，那 Skill 就是浏览器插件（Extension）：同样的内核，通过不同的插件获得完全不同的能力。Skill 和插件的类比非常贴切——插件有独立的配置文件、能访问宿主提供的 API、有明确的触发条件、安装后即刻生效。

在 GBrain 的设计哲学里，Skill 不仅仅是「让 AI 更好用」，更是**让 AI 的行为可预期、可测试、可复用**的关键机制。

## 9.2 Skill 的结构

每个 Skill 对应 `skills/<name>/SKILL.md` 文件，采用 YAML frontmatter + Markdown body 的格式。YAML frontmatter 定义 Skill 的元数据，Markdown body 定义 Skill 的行为规范。

```yaml
---
name: idea-ingest
version: 1.0.0
description: |
  Ingest links, articles, tweets, and ideas into the brain.
triggers:
  - "share a link"
  - "save this"
  - "read this"
tools:
  - search
  - query
  - get_page
  - put_page
  - add_link
  - add_timeline_entry
mutating: true
writes_pages: true
writes_to:
  - people/
  - concepts/
  - sources/
---
```

核心字段说明：

| 字段 | 含义 |
|------|------|
| `name` | 唯一标识符，kebab-case 格式，如 `idea-ingest`、`repo-architecture` |
| `description` | 一段话描述 Skill 的用途，供 LLM 判断何时调用 |
| `triggers` | 触发短语列表，LLM 根据这些判断用户是否在请求这个 Skill |
| `tools` | 该 Skill 可以调用的 GBrain Operation 列表，如 `put_page`、`search` 等 |
| `mutating` | 标记 Skill 是否会修改 brain 状态（用于安全审核） |
| `writes_pages` | 标记 Skill 是否会创建 brain 页面 |
| `writes_to` | 列出 Skill 可能写入的目录，用于权限控制 |

SKILL.md 的 Markdown body 则定义了 Skill 的完整行为规范，包含 **Contract**（保证事项）、**Phases**（执行步骤）、**Output Format**（输出格式）、**Anti-Patterns**（常见错误）四个标准章节。

```{mermaid}
graph TD
    subgraph Skill内部结构
        Y["YAML Frontmatter<br/>name / triggers / tools / mutating"]
        C["Contract<br/>保证事项"]
        P["Phases<br/>执行步骤"]
        O["Output Format<br/>输出格式"]
        A["Anti-Patterns<br/>禁忌列表"]
    end
    Y --> C
    C --> P
    P --> O
    O --> A
```

这种结构化格式有几个关键优势：第一，Contract 让 Skill 的行为有边界，不会在超出范围时产生奇怪的效果；第二，Anti-Patterns 明确列出 Skill 不应该做的事，形成双向约束；第三，YAML frontmatter 使 Skill 的元数据可以被程序解析，从而实现 Skill 的自动发现、路由和安全审核。

## 9.3 内置 Skill 解析

GBrain 出厂自带一套经过验证的 Skill，覆盖了从信息摄入到知识输出的完整流程。以下解析几个核心 Skill 的设计思路。

### idea-ingest：零散想法的结构化沉淀

`idea-ingest` 是 GBrain 的信息摄入入口 Skill。当用户分享一个链接、说「save this」或「read this」时，这个 Skill 被触发。它的核心设计理念是：**摄入不是下载，而是翻译**。

所谓翻译，是指摄入不是把网页内容原封不动存进 brain，而是将内容转换为符合 GBrain 数据模型的知识单元。具体来说，`idea-ingest` 保证：
- 每条摄入的内容都有 genuin analysis（真实分析），而不是仅仅总结
- 作者必须有独立的 people 页面（MANDATORY）
- 所有提及的人和公司都建立双向链接
- 原始来源通过 `file_upload` 保留作为溯源依据
- 每个事实都有 inline `[Source: ...]` 引用

这个设计思路背后的哲学是：信息如果不能和已有知识建立联系，就只是一堆字符。`idea-ingest` 通过强制 entity propagation 和 cross-linking，确保每条新信息都成为知识图谱中的一个节点，而不是孤立的碎片。

### query：三层搜索的答案合成

`query` 是 GBrain 的查询 Skill，负责回答用户关于 brain 内容的问题。它的设计核心是**三层搜索 + 引用追溯**。

三层搜索是指：
1. **关键词搜索**（FTS）—— 精确匹配人名、日期、专业术语
2. **向量搜索**（Embedding）—— 语义相似性，处理概念性问题
3. **图遍历**（Graph）—— 处理关系型问题，如「谁认识谁」「A 和 B 之间有什么关系」

`query` 不会凭空回答，它必须 grounded in brain content。每一个 claim 必须 trace back to a specific page slug。当多个来源冲突时，按照 user statement > compiled truth > timeline > external 的优先级处理，并且要明确标注冲突，而非默默选其一。

这个 Skill 的设计体现了 GBrain 的核心承诺：LLM 是知识图的界面层，而不是知识源本身。所有答案最终都来自用户积累的 brain 内容，LLM 只是一个好用的检索和合成引擎。

### meeting-ingestion：会议记录的全链路处理

`meeting-ingestion` 处理会议记录摄入，设计理念是：**会议的价值不在会议本身，在于它涉及的每一个实体**。

传统的信息摄入往往止步于「创建一条记录」。`meeting-ingestion` 的 Contract 要求：
1. 参会者每个人都有 people 页面（创建或更新）
2. 讨论到的每个公司、项目都要 entity propagation
3. 同一个事件要出现在所有相关实体的 timeline 上（timeline merge）
4. meeting 页面必须等到 enrich skill 处理完所有实体才算完全摄入

这意味着处理一场会议，实际上会触发对 dozen 甚至 hundred 相关实体的更新。表面上是「摄入一个会议」，实际上是「以会议为入口对知识图谱做一次全面体检」。

### media-ingest：多模态内容的统一抽象

`media-ingest` 处理视频、音频、PDF、书籍、截图、GitHub 仓库等内容。它的设计理念是：**媒体格式不同，但知识处理的逻辑相同**。

不同格式的 intake 路径不同（YouTube 需要 Whisper 转录，PDF 需要 OCR，GitHub 需要 clone + README 分析），但 downstream 的处理完全一致：
- 都是创建 brain page
- 都进行 entity extraction（人员、公司检测）
- 都建立双向 back-link
- 都按 primary subject 归档（视频内容不归档到 `media/videos/`，而归档到对应的 subject 目录）

这种设计让 GBrain 的多模态能力建立在统一的 entity 处理管道上，而不是为每种媒体格式单独写一个 intake pipeline。

### repo-architecture：知识归档的决策协议

`repo-architecture` 是一个元 Skill（meta-skill），它不摄入内容，而是为其他 Skill 提供归档决策。它的核心职责是回答：「这个内容应该放在哪个目录？」

它的设计理念是：**按 primary subject 归档，而不是按格式或来源**。这是最常见的错误来源——把所有 PDF 都丢进 `sources/`，把所有视频都丢进 `media/`。真正的归档逻辑要看内容的 primary subject：一个关于公司分析的 PDF 应该放在 `companies/`，一个关于产品设计的视频应该放在 `concepts/`。

`repo-architecture` 提供了一个清晰的决策树：about a person → `people/`，about a company → `companies/`，a reusable concept → `concepts/`，a meeting → `meetings/`。这个决策树是所有 ingest 类 Skill 的公共依赖。

## 9.4 Skill 的触发机制

Skill 的触发分为两种模式：显式触发（Explicit）和隐式触发（Implicit）。

```{mermaid}
flowchart TD
    A["用户输入"] --> B{触发类型判断}
    B -->|"显式触发<br/>MCP / CLI 手动调用"| C["直接路由到目标 Skill"]
    B -->|"隐式触发<br/>LLM 推理决策"| D["Signal Detector 分析"]
    D --> E["对话内容语义分析"]
    E --> F["意图分类 + 实体检测"]
    F --> G{"Skill 候选列表"}
    G --> H["MECE 检查<br/>避免重叠"]
    H --> I["最终 Skill 路由"]
    
    style C fill:#b8d4e3
    style I fill:#d4e8c0
```

**显式触发**：用户通过 MCP 协议或 CLI 工具直接调用特定 Skill。比如通过 MCP 工具调用 `idea-ingest` Skill 并传入 URL 参数。这种方式适用于确定性高的场景，用户明确知道需要什么操作。

**隐式触发**：LLM 根据对话上下文自行判断应该激活哪个 Skill。这依赖于 Skill 的 `triggers` 字段和 `description` 字段。LLM 在收到用户消息时，会将消息内容与所有 Skill 的触发短语进行匹配，选择最合适的一个。

`signal-detector` 是一个特殊的始终运行（always-on）的 Skill。每个进入的消息都会触发它，它在后台并行地做两件事：

1. **原始想法捕获**：检测用户表达的新想法、观察、论点、框架，存入 `originals/` 目录
2. **实体提及检测**：检测消息中提到的人和公司，自动创建或丰富对应的 brain page

`signal-detector` 设计为永远不阻塞主响应——它作为 cheap sub-agent 并行 spawn，完成后只记录一行信号日志。这种设计确保 ambient capture 不会影响正常对话的响应延迟。

触发决策流程的核心约束是 **MECE**（Mutually Exclusive, Collectively Exhaustive）——每个 Skill 的触发条件互不重叠，且覆盖所有用户意图。当多个 Skill 同时匹配时，需要冲突处理机制：通过 intent classification 进行优先级排序，或者将任务委托给最具体的 Skill。

## 9.5 Skill 之间的协作

Skill 不是孤立的单元，它们可以嵌套调用、共享状态、相互协作。

**嵌套调用**：一个 Skill 在执行过程中可以调用其他 Skill。例如 `meeting-ingestion` 在处理参会者时，会调用 `enrich` Skill 来创建或丰富 people page；在创建 meeting page 后，会触发 auto-link post-hook 自动建立链接。Skill 的嵌套深度没有硬性限制，但需要避免循环依赖。

**共享状态**：所有 Skill 共享同一个 BrainEngine 实例，这意味着它们访问同一个 brain 数据库。当 `signal-detector` 在后台创建了一个 person page，`query` Skill 在前台查询时可以立即看到这个新创建的 page。Skill 之间通过 brain 的 page 层级结构实现数据共享，而不是通过进程内状态传递。

**冲突处理**：当多个 Skill 同时触发同一请求时（例如 `idea-ingest` 和 `media-ingest` 都试图处理同一个 URL），GBrain 通过 resolver 的 MECE 检查来预防冲突。如果 resolver 发现两个 Skill 竞争同一个 trigger phrase，会报告错误让维护者介入。

Skill 协作的一个关键设计是 **entity propagation 传播链**：当一个 Skill 创建了新的 brain page 时，它必须同步更新所有相关实体的页面和 timeline。这个约束保证了知识图谱的一致性——每条信息都会沿着它涉及的实体链路传播，而不是停留在孤立的页面里。