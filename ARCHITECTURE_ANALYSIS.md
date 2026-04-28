# GBrain 源码架构分析报告

> 版本: v0.20.0 (Cathedral II)  
> 分析时间: 2026-04-28  
> 源码路径: `/home/liyifan/gbrain/src/`

---

## 一、整体架构概览

GBrain 是一个**本地优先的个人知识管理 + AI 搜索大脑**。它的核心设计哲学是：

1. **本地存储优先** — 数据存储在本地 PGLite（嵌入式）或 Postgres（远程）数据库中
2. **Git 原生** — 通过文件系统（Markdown 文件）+ Git diff 进行版本控制和同步
3. **双引擎支持** — 同一套 API 同时支持 PGLite（零配置）和 Postgres（生产级）
4. **操作层抽象** — 所有功能（CLI/MCP/直接调用）都通过统一的 `Operation` 系统暴露

### 1.1 目录结构

```
src/
├── cli.ts                  # CLI 入口（736 行）
├── version.ts              # 版本号
├── mcp/
│   ├── server.ts           # MCP (Model Context Protocol) 服务端
│   └── tool-defs.ts        # MCP 工具定义生成器
├── core/
│   ├── engine.ts           # BrainEngine 接口定义（核心抽象）
│   ├── pglite-engine.ts    # PGLite 引擎实现（嵌入式 WASM）
│   ├── postgres-engine.ts  # Postgres 引擎实现（pgvector 支持）
│   ├── types.ts            # 核心类型定义（Page/Chunk/SearchResult 等）
│   ├── operations.ts       # 操作注册表 + 参数校验（CLI/MCP 核心）
│   ├── embedding.ts        # OpenAI Embedding 服务
│   ├── markdown.ts         # Markdown 解析/序列化
│   ├── link-extraction.ts  # 链接 + 时间线提取（重要纯函数库）
│   ├── sync.ts             # Git diff 解析 + Slug 工具
│   ├── storage.ts          # 存储后端抽象
│   ├── storage/            # 存储实现（local / s3 / supabase）
│   ├── search/             # 搜索实现（混合搜索管线）
│   │   ├── hybrid.ts       # 混合搜索（关键词 + 向量 + RRF 融合）
│   │   ├── keyword.ts      # 关键词搜索（SQL trigram）
│   │   ├── vector.ts       # 向量搜索（cosine similarity）
│   │   ├── dedup.ts        # 结果去重（按页面 + 余弦相似度）
│   │   ├── expansion.ts    # 查询扩展
│   │   ├── two-pass.ts     # 两遍检索（代码结构感知）
│   │   ├── sql-ranking.ts  # SQL 层面的排名增强
│   │   └── source-boost.ts # 来源 boosting
│   ├── resolvers/          # Resolver 系统（外部数据查找）
│   │   ├── interface.ts    # Resolver 接口定义
│   │   ├── registry.ts     # Resolver 注册表
│   │   └── builtin/        # 内置 Resolver 实现
│   ├── minions/            # 后台作业系统（队列/Worker）
│   ├── enrichment-service.ts # 实体 enrichment 服务
│   ├── chunkers/           # 文本分块策略
│   │   ├── recursive.ts    # 递归文本分块
│   │   ├── code.ts         # 代码文件分块（tree-sitter）
│   │   └── semantic.ts     # 语义分块
│   ├── output/             # 输出验证 + 写入
│   ├── skillpack/          # SkillPack 打包/安装
│   ├── skillify/           # Skillify 代码生成
│   ├── migrate.ts          # 数据库迁移框架（核心！）
│   ├── config.ts           # 配置加载
│   └── ...
└── commands/               # CLI 命令（50+ 个）
    ├── init.ts
    ├── query.ts / ask.ts
    ├── import.ts / export.ts
    ├── embed.ts
    ├── sync.ts
    ├── serve.ts
    ├── agent.ts
    ├── doctor.ts
    ├── cycle.ts
    ├── jobs.ts
    └── migrations/         # 各版本迁移脚本
```

---

## 二、核心模块详解

### 2.1 `BrainEngine` 接口 —— 核心抽象层

**文件**: `core/engine.ts` (347 行)

#### 职责
`BrainEngine` 是整个系统的**核心接口抽象**，定义了 GBrain 数据层的完整操作契约。它是：
- 双引擎（PGLite / Postgres）的共同接口
- 所有上层操作（CLI、MCP、代码调用）的唯一数据访问入口
- 迁移、安全验证、超时控制等横切关注点的统一 hook 位置

#### 关键接口方法

| 类别 | 方法 | 说明 |
|------|------|------|
| **生命周期** | `connect()` / `disconnect()` / `initSchema()` / `transaction()` | 数据库连接管理 |
| **页面 CRUD** | `getPage()` / `putPage()` / `deletePage()` / `listPages()` | 页面基本操作 |
| **搜索** | `searchKeyword()` / `searchVector()` / `getEmbeddingsByChunkIds()` | 搜索入口 |
| **Chunk** | `upsertChunks()` / `getChunks()` / `countStaleChunks()` / `listStaleChunks()` | 内容块管理 |
| **链接** | `addLink()` / `addLinksBatch()` / `getLinks()` / `getBacklinks()` | 知识图谱边 |
| **图遍历** | `traverseGraph()` / `traversePaths()` / `getBacklinkCounts()` / `findOrphanPages()` | 知识图谱 |
| **时间线** | `addTimelineEntry()` / `addTimelineEntriesBatch()` / `getTimeline()` | 时间线 |
| **代码边** | `addCodeEdges()` / `deleteCodeEdgesForChunks()` / `getCallersOf()` / `getCalleesOf()` | Cathedral II 代码理解 |
| **版本** | `createVersion()` / `getVersions()` / `revertToVersion()` | 版本控制 |
| **统计** | `getStats()` / `getHealth()` | 健康检查 |
| **代码搜索** | `searchKeywordChunks()` | Chunk 级关键词搜索（A2 两遍检索用） |

#### 数据流
```
CLI/MCP Call
    ↓
Operation Handler (operations.ts)
    ↓
BrainEngine Interface
    ↓
PGLiteEngine OR PostgresEngine (实现类)
    ↓
SQL (postgres.js / PGlite)
    ↓
Postgres/PGLite + pgvector
```

---

### 2.2 双引擎实现 —— `PGLiteEngine` vs `PostgresEngine`

#### `PGLiteEngine` (`core/pglite-engine.ts`, 1439 行)

**特点**: 嵌入式 WASM 数据库，零配置

```
PGlite.create({ extensions: { vector, pg_trgm } })
    ↓
PGLITE_SCHEMA_SQL (内嵌 DDL)
    ↓
runMigrations() (增量迁移)
```

**关键机制**:
- 文件锁 (`pglite-lock.ts`) 防止并发访问
- `PGLITE_SCHEMA_SQL` 是**内嵌的完整 DDL**（不是文件引用），包含所有表结构
- `vector` 扩展支持 pgvector 向量操作
- `pg_trgm` 支持 trigram 模糊匹配

#### `PostgresEngine` (`core/postgres-engine.ts`, 1582 行)

**特点**: 远程生产级数据库，支持 pgvector

**关键机制**:
- 连接池管理（支持 PgBouncer 事务模式）
- Session 级超时控制 (`statement_timeout`)
- Prepared statement 处理（PgBouncer 兼容性）
- 支持副本连接用于只读查询
- `SCHEMA_SQL` 同样内嵌在 `schema-embedded.ts` 中

**共同设计**:
- 两者共享相同的 SQL DDL（通过不同的 schema 字符串）
- 迁移系统统一：`runMigrations()` 在 `migrate.ts` 中
- 所有查询都通过 `BrainEngine` 接口抽象

---

### 2.3 搜索系统 (`core/search/`)

#### 混合搜索管线 (`hybrid.ts`)

**核心流程**:
```
hybridSearch(query, opts)
    ↓
┌─ 1. searchKeyword() ──────────────────────┐
│   SQL: trigram ILIKE + tsvector ranking    │
└────────────────┬───────────────────────────┘
    ↓
┌─ 2. searchVector() (如果有 OPENAI_API_KEY) ─┐
│   SQL: cosine similarity <embedding>       │
└────────────────┬───────────────────────────┘
    ↓
┌─ 3. Reciprocal Rank Fusion (RRF) ──────────┐
│   RRF_K = 60                               │
│   score = Σ 1/(K + rank)                   │
└────────────────┬───────────────────────────┘
    ↓
┌─ 4. Cosine Re-score ───────────────────────┐
│   blend = 0.7*rrf + 0.3*cosine             │
└────────────────┬───────────────────────────┘
    ↓
┌─ 5. Backlink Boost ────────────────────────┐
│   factor = 1 + 0.05*log(1 + backlink_count)│
└────────────────┬───────────────────────────┘
    ↓
┌─ 6. Deduplication ────────────────────────┐
│   per-page best chunk + cosine dedup       │
└────────────────┬───────────────────────────┘
    ↓
    Results (SearchResult[])
```

#### 搜索子模块

| 文件 | 职责 | 关键函数 |
|------|------|----------|
| `hybrid.ts` | 混合搜索编排 + RRF | `hybridSearch()`, `applyBacklinkBoost()` |
| `keyword.ts` | 关键词搜索入口 | `keywordSearch()` |
| `vector.ts` | 向量搜索入口 | `vectorSearch()` |
| `dedup.ts` | 去重策略 | `dedupResults()`, `deduplicateByCosine()` |
| `expansion.ts` | 查询扩展 | `expandQuery()` |
| `two-pass.ts` | **Cathedral II A2** 两遍检索 | `expandAnchors()`, `hydrateChunks()` |
| `sql-ranking.ts` | SQL 排名增强 | `buildSourceFactorCase()` |
| `source-boost.ts` | 来源 boosting | `resolveBoostMap()` |
| `intent.ts` | 查询意图检测 | `autoDetectDetail()` |

#### 两遍检索 (`two-pass.ts`)

**v0.20.0 Cathedral II 核心创新**:

```
Pass 1: Keyword/Vector 锚点搜索
    ↓
expandAnchors(walkDepth=1~2)
    ├─ 直接边: code_edges_chunk (to_chunk_id 已知)
    └─ 符号边: code_edges_symbol (需反向解析符号名)
    ↓
Pass 2: 结构邻居收集
    score = anchor_score * 1/(1 + hop_distance)
    ↓
hydrateChunks() → 补全 SearchResult 元数据
```

---

### 2.4 嵌入向量系统 (`core/embedding.ts`)

**设计目标**: OpenAI `text-embedding-3-large` (1536 维)

```
embed(text) → Float32Array
embedBatch(texts[], opts?) → Float32Array[]

重试策略:
  - 指数退避: 4s base, 120s cap, 最多 5 次
  - 429 时优先尊重 Retry-After header
  - 批量大小: 100 条/请求
  - 最大截断: 8000 字符
```

**关键常量**:
- `EMBEDDING_MODEL = 'text-embedding-3-large'`
- `EMBEDDING_DIMENSIONS = 1536`
- `EMBEDDING_COST_PER_1K_TOKENS = $0.00013`

---

### 2.5 存储系统 (`core/storage/`)

**接口定义** (`storage.ts`):
```typescript
interface StorageBackend {
  upload(path: string, data: Buffer, mime?: string): Promise<void>;
  download(path: string): Promise<Buffer>;
  delete(path: string): Promise<void>;
  exists(path: string): Promise<boolean>;
  list(prefix: string): Promise<string[]>;
  getUrl(path: string): Promise<string>;
}
```

**三后端实现**:

| 后端 | 文件 | 特点 |
|------|------|------|
| **Local** | `storage/local.ts` | 文件系统模拟，路径遍历保护 |
| **S3** | `storage/s3.ts` | AWS S3 / Cloudflare R2 / MinIO 兼容 |
| **Supabase** | `storage/supabase.ts` | TUS 可恢复上传（>100MB）+ 标准 POST |

**Supabase 上传策略**:
- `< 100MB`: 标准单次 POST
- `>= 100MB`: TUS 可恢复上传（6MB 分块，3 次重试）

---

### 2.6 知识图谱 / 链接系统 (`core/link-extraction.ts`)

**核心数据结构**:

```typescript
interface Link {
  from_slug: string;
  to_slug: string;
  link_type: string;       // e.g. "references", "attended", "invested_in"
  context: string;
  link_source?: 'markdown' | 'frontmatter' | 'manual';
  origin_slug?: string;   // frontmatter 来源页面
  origin_field?: string;  // frontmatter 字段名
}
```

**链接提取模式**:
1. **Markdown 链接**: `[Name](path)` — 正则 `ENTITY_REF_RE`
2. **Wikilink**: `[[path]]` 或 `[[path|Display]]` — 正则 `WIKILINK_RE`
3. **Qualified Wikilink**: `[[source:path]]` — 支持多数据源
4. **Frontmatter 字段**: 从 YAML 解析 `people`, `investors`, `attendees` 等字段

**时间线提取**: 类似方式从 `<!-- timeline -->` sentinel 分割

---

### 2.7 Resolver 系统 (`core/resolvers/`)

**设计目标**: 外部数据查找的插件化框架（X API / Perplexity / URL 检查等）

```
Resolver<I, O>
  ├── id: string (slug-cased, e.g. "x_handle_to_tweet")
  ├── cost: 'free' | 'rate-limited' | 'paid'
  ├── backend: string (e.g. "x-api-v2")
  ├── available(ctx): Promise<boolean>
  └── resolve(req): Promise<ResolverResult<O>>
```

**内置 Resolver**:
- `url-reachable.ts` — HTTP HEAD 检查 URL 可达性
- `x-api/handle-to-tweet.ts` — X (Twitter) API 查找

**注册机制** (`registry.ts`):
```typescript
class ResolverRegistry {
  register<I, O>(resolver: Resolver<I, O>): void;
  resolve<I, O>(id: string, input: I, ctx: ResolverContext): Promise<ResolverResult<O>>;
}
```

---

### 2.8 操作层 (`core/operations.ts`)

**核心设计**: 单一操作注册表，驱动 CLI + MCP

```typescript
export interface Operation {
  name: string;
  description: string;
  params: Record<string, ParamDef>;
  cliHints?: { name: string; positional?: string[]; stdin?: string; };
  handler: (ctx: OperationContext, params: Record<string, unknown>) => Promise<unknown>;
}
```

**`OperationContext`**:
```typescript
interface OperationContext {
  engine: BrainEngine;
  config: GBrainConfig;
  logger: Logger;
  dryRun: boolean;
  remote: boolean;   // 信任边界: false=CLI, true=MCP/agent
  cliOpts: CliOptions;
}
```

**安全模型**: `remote = true` 时启用严格文件路径限制（防止路径遍历）

---

### 2.9 Markdown 处理 (`core/markdown.ts`)

**解析格式**:
```
---
type: person
title: Alice Chen
tags: [founder, ai]
---
# Compiled Truth Content
<!-- timeline -->
# Timeline entries
```

**关键函数**:
- `parseMarkdown(content, filePath?, opts?)` → `ParsedMarkdown`
- `serializeMarkdown(frontmatter, compiled_truth, timeline, meta)` → `string`
- `splitBody(body)` — 在 `<!-- timeline -->` sentinel 处分割

**验证错误类型**:
- `MISSING_OPEN` / `MISSING_CLOSE` — frontmatter 分隔符
- `YAML_PARSE` — YAML 解析失败
- `SLUG_MISMATCH` — frontmatter slug 与路径不匹配
- `NULL_BYTES` — 二进制损坏
- `NESTED_QUOTES` — 常见 YAML 错误

---

### 2.10 Minions 后台作业系统 (`core/minions/`)

**架构**:
```
MinionQueue (队列)
    ↓
MinionWorker (Worker 进程)
    ↓
MinionHandler (处理函数)
    ↓
  ├── shell.ts / shell-audit.ts
  ├── subagent.ts / subagent-aggregator.ts
  └── supervisor.ts / supervisor-audit.ts
```

**关键组件**:
- `queue.ts` — 作业队列（基于数据库表）
- `worker.ts` — Worker 进程管理
- `backpressure-audit.ts` — 背压控制
- `rate-leases.ts` — 速率限制
- `quiet-hours.ts` — 静默时段

---

### 2.11 迁移系统 (`core/migrate.ts`)

**设计**: 版本化迁移，每版本一个 `up()` 函数

```typescript
interface Migration {
  version: number;
  up(sql: SQL): Promise<void>;
  down?(sql: SQL): Promise<void>;
}
```

**机制**:
- 迁移版本存储在 `schema_migrations` 表
- `runMigrations()` 在每次 `initSchema()` 时自动应用
- `ReservedConnection` 支持设置 session 级 GUC（如 `statement_timeout`）

---

### 2.12 CLI 入口 (`cli.ts`)

**命令分发模式**:
```
CLI_ONLY commands (不需要 DB)
    ├─ init, upgrade, check-update, integrations
    ├─ publish, lint, report, import, export
    └─ doctor, skillpack, resolvers, integrity

Shared operations (通过 Operation 系统)
    ├─ query / ask (自然语言查询)
    ├─ search (关键词搜索)
    ├─ get_page / put_page / delete_page
    └─ embed, sync, extract, graph-query, ...
```

**全局 Flag**:
- `--quiet` — 静默输出
- `--progress-json` — JSON 进度输出
- `--progress-interval` — 进度刷新间隔

---

### 2.13 MCP 服务端 (`mcp/server.ts`)

**协议**: Model Context Protocol (stdio 传输)

```
ListToolsRequest → buildToolDefs(operations) → ToolDef[]
CallToolRequest → validate → op.handler(ctx, params) → JSON
```

**信任边界**: `remote = true` — MCP 调用者被视为不可信，启用严格文件限制

---

### 2.14 导入系统 (`core/import-file.ts`)

**Cathedral II D2: Markdown 内嵌代码块提取**:

```typescript
// 从 markdown 提取 ```ts ```py ```go 等代码块
// 作为独立 chunk 追加到父页面，chunk_source = 'fenced_code'
extractFencedChunks(markdown, startChunkIndex) → ChunkInput[]
```

**支持语言**: TypeScript, JavaScript, Python, Ruby, Go, Rust, Java, C#, C++, PHP, Swift, Kotlin, Scala, Lua, Elixir, Elm, OCaml, Dart, Zig, Solidity, Shell, CSS, HTML, Vue, JSON, YAML, TOML

---

## 三、模块间依赖关系

```
cli.ts (入口)
  ├─→ operations.ts (操作注册表)
  │     ├─→ engine.ts (接口)
  │     │     ├─→ pglite-engine.ts
  │     │     │     ├─→ pglite-schema.ts
  │     │     │     └─→ migrate.ts
  │     │     └─→ postgres-engine.ts
  │     │           ├─→ schema-embedded.ts
  │     │           └─→ migrate.ts
  │     │
  │     ├─→ search/hybrid.ts
  │     │     ├─→ embedding.ts
  │     │     ├─→ search/keyword.ts
  │     │     ├─→ search/vector.ts
  │     │     ├─→ search/dedup.ts
  │     │     ├─→ search/two-pass.ts
  │     │     └─→ search/expansion.ts
  │     │
  │     ├─→ markdown.ts
  │     ├─→ link-extraction.ts
  │     └─→ storage.ts
  │           ├─→ storage/local.ts
  │           ├─→ storage/s3.ts
  │           └─→ storage/supabase.ts
  │
  ├─→ mcp/server.ts
  │     └─→ operations.ts (复用)
  │
  └─→ commands/* (独立命令)
        ├─→ sync.ts (git diff 解析)
        ├─→ import.ts / export.ts
        └─→ cycle.ts (自动循环)
```

---

## 四、关键数据流图

### 4.1 页面写入流程

```
put_page Operation
    ↓
parseMarkdown(content) → { frontmatter, compiled_truth, timeline }
    ↓
extractPageLinks(compiled_truth) → EntityRef[]
extractTimelineEntries(timeline) → TimelineEntry[]
    ↓
engine.putPage(slug, pageInput)
    ↓
engine.upsertChunks(slug, chunks[])
    ↓
engine.addLinksBatch(links[])
    ↓
engine.addTimelineEntriesBatch(entries[])
```

### 4.2 查询流程

```
query Operation (hybridSearch)
    ↓
autoDetectDetail(query) → 'low' | 'medium' | 'high'
    ↓
expandQuery(query) → expandedQueries[]
    ↓
┌─ searchKeyword(query) → RRF → dedup
└─ searchVector(embedding) → RRF → dedup
    ↓
applyBacklinkBoost()
    ↓
hybridSearch() → SearchResult[]
```

### 4.3 同步流程

```
gbrain sync
    ↓
git diff --name-status -M LAST..HEAD
    ↓
buildSyncManifest() → { added, modified, deleted, renamed }
    ↓
isSyncable() + isCodeFilePath() 分类
    ↓
pathToSlug() / pathToCodeSlug()
    ↓
┌─ added/modified → importFile() → upsert
└─ deleted → engine.deletePage()
    ↓
renamed → engine.updateSlug() + engine.rewriteLinks()
```

---

## 五、教材章节优先级排序

基于教学逻辑顺序和依赖关系，建议以下章节排序：

### 第一梯队：基础概念（必读）

| 优先级 | 章节 | 文件 | 理由 |
|--------|------|------|------|
| ⭐⭐⭐ | **数据模型** | `core/types.ts` | 所有功能的基础，Page/Chunk/Link 定义 |
| ⭐⭐⭐ | **引擎接口** | `core/engine.ts` | 整个系统的心脏，双引擎抽象 |
| ⭐⭐⭐ | **操作系统** | `core/operations.ts` | CLI/MCP 统一入口 |
| ⭐⭐⭐ | **Markdown 处理** | `core/markdown.ts` | GBrain 文件格式核心 |

### 第二梯队：核心功能（重要）

| 优先级 | 章节 | 文件 | 理由 |
|--------|------|------|------|
| ⭐⭐ | **混合搜索** | `core/search/hybrid.ts` | AI 搜索的核心实现 |
| ⭐⭐ | **嵌入向量** | `core/embedding.ts` | 语义搜索基础设施 |
| ⭐⭐ | **链接提取** | `core/link-extraction.ts` | 知识图谱的基础 |
| ⭐⭐ | **存储后端** | `core/storage*.ts` | 文件存储抽象 |
| ⭐⭐ | **CLI 入口** | `cli.ts` | 整体架构理解 |

### 第三梯队：高级功能（进阶）

| 优先级 | 章节 | 文件 | 理由 |
|--------|------|------|------|
| ⭐ | **Resolver 系统** | `core/resolvers/` | 外部数据集成 |
| ⭐ | **两遍检索** | `core/search/two-pass.ts` | Cathedral II 代码理解 |
| ⭐ | **代码分块** | `core/chunkers/code.ts` | tree-sitter 代码分析 |
| ⭐ | **Minions 系统** | `core/minions/` | 后台作业调度 |
| ⭐ | **迁移框架** | `core/migrate.ts` | 数据库版本管理 |

### 第四梯队：支撑系统（补充）

| 优先级 | 章节 | 文件 | 理由 |
|--------|------|------|------|
| 🔧 | **MCP 服务** | `mcp/server.ts` | AI Agent 集成 |
| 🔧 | **Enrichment** | `core/enrichment-service.ts` | 实体自动丰富 |
| 🔧 | **同步机制** | `core/sync.ts` | Git 原生同步 |
| 🔧 | **Chunkers** | `core/chunkers/*.ts` | 多种分块策略 |

---

## 六、核心设计模式

### 6.1 接口+实现分离
```
BrainEngine (接口) ← PGLiteEngine / PostgresEngine (实现)
```
同一套代码可切换嵌入式和远程数据库

### 6.2 操作注册表模式
```
operations[] → cli.ts / mcp/server.ts 统一消费
```
新操作只需注册到 `operations.ts`，自动获得 CLI + MCP 支持

### 6.3 纯函数优先
```
link-extraction.ts — 所有函数都是纯函数（无 DB 依赖）
search/*.ts — 数据转换管道
```
易于测试和组合

### 6.4 信任边界标记
```
OperationContext.remote: boolean
```
`false` = 本地 CLI（完全信任），`true` = MCP/Agent（严格限制）

### 6.5 内嵌 Schema
```
schema-embedded.ts / pglite-schema.ts
```
完整的 DDL 作为字符串内嵌在代码中，无需外部文件依赖

---

## 七、数据库 Schema 要点

**核心表**:
- `pages` — 页面主表（slug, type, title, compiled_truth, timeline, frontmatter JSONB）
- `content_chunks` — 页面内容块（embedding 1536 维向量，token_count，代码元数据）
- `links` — 知识图谱边（from/to/type/source/provenance，支持多源）
- `timeline_entries` — 时间线条目
- `tags` — 标签
- `code_edges_chunk` / `code_edges_symbol` — 代码调用图（Cathedral II）
- `sources` — 多源支持（v0.18.0+）
- `minion_jobs` — 后台作业队列
- `schema_migrations` — 迁移版本记录

---

## 八、配置与安全

### 8.1 配置加载 (`core/config.ts`)
```
~/.gbrain/config.json → 环境变量覆盖 → 代码默认值
```

### 8.2 安全机制
- **上传路径验证**: `validateUploadPath()` — 严格模式阻止符号链接逃脱
- **Slug 白名单验证**: `validatePageSlug()` — 只允许 `[a-z0-9-]/` 格式
- **文件名验证**: `validateFilename()` — 禁止隐藏文件、路径遍历符
- **信任边界**: `remote=true` 时 MCP 调用受限

---

*本报告基于 gbrain v0.20.0 Cathedral II 源码分析生成*
