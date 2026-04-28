# 第一章：认识 GBrain——个人知识大脑

## 1.1 从「AI 健忘症」说起

如果你用 ChatGPT 问了一个问题，关掉对话再打开同一个 AI——它已经忘了你们聊过什么。这不是 bug，是 LLM 的本质：**每次对话都是独立的上下文窗口**，训练时见过的数据不会出现在推理时。

这对聊天机器人无所谓，但对**需要长期服务**的场景是致命缺陷。一个 AI 销售助手需要记住三个月的客户跟进记录，一个代码审查 Agent 需要理解整个代码库的调用关系——这些都超出了单轮对话的承载范围。

**LLM 没有持久记忆。**

这就是 **Agent Memory** 问题。

### 业界的三种解法

| 方案 | 代表技术 | 核心思路 | 局限 |
|------|----------|----------|------|
| **向量检索（RAG）** | Pinecone / ChromaDB / Weaviate | 把文档切成块，存向量，检索时拼进 prompt | 缺乏结构关联，版本管理弱 |
| **记忆框架** | MemGPT / AutoGen | 让 LLM 自己管理"记忆层级" | 重量级依赖，侵入性强 |
| **本地知识库** | Obsidian / Logseq | Markdown 文件 + 双链笔记 | 搜索能力弱，无 AI 原生支持 |

这些方案各有取舍，但有一个共同问题：**数据和算法是分离的**。你的笔记存在 Notion，语义向量存在 Pinecone，同步靠手动——这不是一个"大脑"，是一堆拼凑的工具。

---

## 1.2 GBrain 的思路：把记忆当成 Git 仓库

GBrain 走了一条少有人走的路：**把记忆当成一个本地 Git 仓库来管理**。

这不是隐喻。具体来说：

- **数据存在本地**：在 `~/.gbrain/` 目录下，用 Markdown 文件存储你的笔记和知识
- **版本控制靠 Git**：每次修改都有 diff，你随时可以回溯、合并、分支
- **同步靠推送拉取**：和 GitHub 协作一样，可以多人同步
- **一切都可调试**：用 `git log` 看历史，用 `git diff` 看变化

**你的知识，不再被困在 AI 厂商的服务器里。**

这个设计哲学带来的实际好处是：

```
本地优先 → 数据永远属于你，不会因为厂商涨价就失去访问权
Git 原生 → 版本控制是内置的，不需要额外的备份工具
Skill 可扩展 → 像 VSCode 插件一样安装新功能
Cathedral II → 代码结构感知，能理解函数调用关系，而不只是关键词匹配
```

---

## 1.3 GBrain 在这个领域的定位

GBrain **不是通用 RAG 工具**，不是企业知识库解决方案，也不是另一个笔记软件插件。

**GBrain 是一个「个人知识大脑」**——专为个人开发者设计的 AI 搜索和记忆系统，目标是用自然语言快速找到你积累的所有信息：笔记、代码、文档、聊天记录、项目经验。

### 和主流方案的核心区别

| 维度 | GBrain | MemGPT | Oceanic / 其他 RAG |
|------|--------|--------|---------------------|
| **数据存储** | 本地 Markdown + Git | 虚拟内存管理（抽象） | 第三方向量数据库 |
| **版本控制** | 原生 Git | 无 | 通常无 |
| **代码理解** | ✅ Cathedral II 两遍检索 | ❌ | ❌ |
| **同步协作** | Git 原生（多人） | 无 | 依赖外部方案 |
| **部署复杂度** | 单文件 / Docker | 高（需要 LLM 代理框架） | 中（需要维护向量 DB） |

### Cathedral II：代码结构感知

v0.20.0 引入的 **Cathedral II** 是 GBrain 的重大升级——它不只做关键词和向量匹配，而是**理解代码之间的调用关系**。

当你搜索 "How do I authenticate users?" 时，传统的 RAG 可能返回一段包含 "authenticate" 的注释。而 Cathedral II 能追踪：

```
search for "authenticate"
    ↓
find chunks referencing the authenticate function
    ↓
follow code_edges_chunk to callers / callees
    ↓
return the actual call graph context
```

这叫**两遍检索（Two-Pass Retrieval）**：

```{mermaid}
flowchart TD
    A["Pass 1: Keyword/Vector 锚点搜索"] --> B["expandAnchors() 扩展边"]
    B --> C["直接边: code_edges_chunk"]
    B --> D["符号边: code_edges_symbol"]
    C --> E["Pass 2: 结构邻居收集"]
    D --> E
    E --> F["hydrateChunks() 补全元数据"]
    F --> G["SearchResult with call-graph context"]
```

结果不是一段文字，而是一个**有结构的知识片段**——你知道它在哪里被调用，为什么存在，能追到定义它的位置。

---

## 1.4 整体架构预览

GBrain 的代码分布在 `src/` 下的 **171 个 TypeScript 文件**，核心模块如下：

```{mermaid}
graph TD
    subgraph A["接入层"]
        CLI["CLI<br>cli.ts 736行"]
        MCP["MCP 服务<br>mcp/server.ts"]
        API["API 调用"]
    end

    subgraph B["操作注册层"]
        OPS["Operation 注册表<br>operations.ts"]
        ENG["BrainEngine 接口<br>engine.ts 347行"]
    end

    subgraph C["引擎实现层"]
        PG["PGLiteEngine<br>pglite-engine.ts 1439行"]
        POST["PostgresEngine<br>postgres-engine.ts 1582行"]
    end

    subgraph D["存储层"]
        PGL["PGLite WASM<br>零配置嵌入式"]
        VEC["pgvector<br>1536维向量"]
        PGDB["Postgres<br>生产级"]
    end

    CLI --> OPS
    MCP --> OPS
    OPS --> ENG
    ENG --> PG
    ENG --> POST
    PG --> PGL
    PG --> VEC
    POST --> PGDB
    POST --> VEC
```

**数据模型**：

> GBrain 的核心实体：Page（页面）、Chunk（分块）、Link（链接）。通过 Page 与 Chunk 的 1:N 关系组织内容，通过 Link 构建知识图谱，通过 Embedding 实现语义检索。
>
> ```{mermaid}
> erDiagram
>     pages ||--o{ content_chunks : "has"
>     pages ||--o{ links : "from"
>     pages ||--o{ links : "to"
>     content_chunks ||--o{ code_edges_chunk : "calls"
>     content_chunks ||--o{ code_edges_symbol : "defines"
>     code_edges_chunk }o--|| code_edges_symbol : "resolves"
> ```

---

## 1.5 本书结构

如果你想系统学习 GBrain，建议按以下顺序阅读：

### 第一部分：核心概念（第 2-4 章）

| 章节 | 内容 | 关键文件 |
|------|------|----------|
| **第 2 章** | 数据模型——Page、Chunk、Link 的定义与关系 | `core/types.ts` |
| **第 3 章** | BrainEngine 接口——整个系统的核心抽象 | `core/engine.ts` |
| **第 4 章** | Markdown 格式——GBrain 的文件存储格式 | `core/markdown.ts` |

### 第二部分：核心功能（第 5-8 章）

| 章节 | 内容 | 关键文件 |
|------|------|----------|
| **第 5 章** | 混合搜索——关键词 + 向量 + RRF 融合 | `core/search/hybrid.ts` |
| **第 6 章** | 链接与知识图谱——Wikilink、Frontmatter 提取 | `core/link-extraction.ts` |
| **第 7 章** | 双引擎实现——PGLite vs Postgres | `core/pglite-engine.ts` / `postgres-engine.ts` |
| **第 8 章** | 嵌入向量系统——OpenAI Embedding 集成 | `core/embedding.ts` |

### 第三部分：高级特性（第 9-12 章）

| 章节 | 内容 | 关键文件 |
|------|------|----------|
| **第 9 章** | Cathedral II 两遍检索——代码结构感知 | `core/search/two-pass.ts` |
| **第 10 章** | Resolver 系统——外部数据集成 | `core/resolvers/` |
| **第 11 章** | Minions 后台作业——自动化调度 | `core/minions/` |
| **第 12 章** | MCP 协议集成——AI Agent 调用 | `mcp/server.ts` |

---

## 1.6 源码阅读路线

如果你想深入理解 GBrain 的实现，下面是一个经过验证的阅读顺序。

### 关键文件清单

**按阅读优先级排序：**

```
⭐⭐⭐ 必读（理解全局）
  core/engine.ts         — BrainEngine 接口，347行，所有操作的抽象
  core/operations.ts    — Operation 注册表，CLI/MCP 统一入口
  core/types.ts          — 核心类型定义，Page/Chunk/Link 数据结构

⭐⭐ 重要（理解实现）
  core/pglite-engine.ts  — PGLite 引擎实现，1439行
  core/postgres-engine.ts — Postgres 引擎实现，1582行
  core/search/hybrid.ts  — 混合搜索管线
  core/markdown.ts       — Markdown 解析与序列化

⭐ 进阶（理解高级特性）
  core/search/two-pass.ts — Cathedral II 两遍检索
  core/resolvers/       — Resolver 插件系统
  core/minions/         — 后台作业队列
  core/migrate.ts       — 数据库迁移框架
```

### 阅读顺序建议

```
1. 从 cli.ts 入口开始 —— 理解命令分发到 Operation 的流程
2. 看 operations.ts —— 理解 Operation 的注册和执行机制
3. 看 engine.ts —— 理解 BrainEngine 的接口设计
4. 选一个引擎实现深入 —— pglite-engine.ts（代码量少一些）
5. 看 search/hybrid.ts —— 理解查询如何经过多个搜索阶段
6. 看 markdown.ts —— 理解 GBrain 的文件格式
```

### 调试技巧

**断点调试**：
```typescript
// 在 operations.ts 的 handler 入口加断点，可以看到所有操作的参数
// 在 hybrid.ts 的 hybridSearch() 入口加断点，可以看到搜索管线的中间结果
```

**日志级别**：
GBrain 使用结构化日志，通过 `GBRAIN_LOG_LEVEL=debug` 可以看到 SQL 查询和向量计算细节。

**测试数据**：
项目内有 `test/` 目录，用 `bun test` 可以跑单元测试。集成测试需要启动一个 PGLite 实例——代码在 `tests/e2e/` 目录。

---

## 下章预告

第二章我们将深入 **数据模型**——了解 GBrain 如何用 TypeScript 类型定义 Page、Chunk、Link 这些核心概念，以及为什么这些选择会影响整个系统的扩展方向。

---

*GBrain v0.20.0 Cathedral II · 171 个 TypeScript 文件 · 源码路径：`/home/liyifan/gbrain/src/`*