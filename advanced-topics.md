# 第十一章：高级主题（Advanced Topics）

> 本章覆盖 GBrain 中较为深入或特殊的主题，适合有一定基础的读者。不讲安装和 CLI 用法，直接深入内部设计。

---

## 11.1 Cathedral II 两遍检索深度解析

### 11.1.1 什么是两遍检索

**Cathedral II** 是 GBrain v0.20.0 引入的结构化检索机制，核心思想是：**先用快速但粗糙的方式找到候选 Chunk，再在候选 Chunk 内做精确匹配**。这个两遍设计专门解决传统 RAG 的「中间丢失」问题——当答案跨越多个 Chunk 时，单遍检索只能返回「最相关」的单个 Chunk，导致中间上下文丢失。

```{mermaid}
flowchart TD
    A["用户查询"] --> B["Pass 1: 向量/关键词搜索<br/>快速找到 Anchor Chunks"]
    B --> C["expandAnchors() 扩展结构邻居"]
    C --> D{"walkDepth > 0?"}
    D -->|是| E["遍历 code_edges_chunk<br/>顺着调用边扩展"]
    D -->|否| F["直接返回 anchors"]
    E --> G["遍历 code_edges_symbol<br/>通过符合名称扩展"]
    G --> H["Pass 2: hydrateChunks()<br/>补全元数据"]
    H --> I["返回带调用图上下文的 SearchResult"]
```

### 11.1.2 第一遍：锚点搜索

第一遍使用标准的混合搜索（Hybrid Search）找到初始候选集。这一步牺牲精度换速度：

- **向量搜索**：在高维向量空间中找语义相似的 Chunk（cosine similarity）
- **关键词搜索**：用 `pg_trgm` 做三字母组匹配，处理拼写错误和部分匹配
- **RRF 融合**：两种结果用 **Reciprocal Rank Fusion** 合并排序

```typescript
// search/two-pass.ts 核心接口
export interface TwoPassOpts {
  /** 1 或 2 — 最大 2，跳数控制爆炸半径 */
  walkDepth?: number;
  /** 限定符号名匹配，附加到锚点集 */
  nearSymbol?: string;
  /** 限定来源 ID，跨来源搜索 */
  sourceId?: string;
}
```

### 11.1.3 第二遍：结构邻居扩展

第一遍的结果叫 **Anchor Chunks**。第二遍通过代码边（code edges）扩展这些锚点：

- **直接边**（`code_edges_chunk`）：Chunk 之间的直接调用关系，`to_chunk_id` 非空
- **符号边**（`code_edges_symbol`）：通过函数/变量名关联，`to_symbol_qualified` 非空

每扩展一跳，score 乘以衰减系数 `1/(1+hop)`：

```typescript
// 跳数衰减示意
hop=0 (锚点自身): score * 1/(1+0) = score * 1.0
hop=1 (直接邻居): score * 1/(1+1) = score * 0.5
hop=2 (邻居的邻居): score * 1/(1+2) = score * 0.33
```

扩展有严格上限：**深度最多 2 跳，每跳最多 50 个邻居**。这是为了防止高扇出代码（如大型开源库）产生爆炸性检索。

### 11.1.4 解决「中间丢失」问题

传统 RAG 的「中间丢失」问题：

```
文档 D = [Chunk A] [Chunk B] [Chunk C] [Chunk D] [Chunk E]
用户问: "B 和 D 之间的关系"
单遍检索: 返回最相关的单个 Chunk，比如 C
结果: 缺少 B→C→D 的传递路径
```

Cathedral II 的解法：

```
Pass 1: 找到锚点 Chunk C（命中关键词 "relationship"）
Pass 2: 扩展 C 的结构邻居，发现 B 和 D 都与 C 有调用边
结果: 返回 [B, C, D] — 完整的传递路径
```

图感知还带来了**文档关系理解**：通过链接分析，A 页面的链接指向哪些 Chunk，帮助理解文档间的引用关系。

### 11.1.5 实现文件

核心实现：`search/two-pass.ts`

| 函数 | 作用 |
|------|------|
| `expandAnchors()` | 从锚点出发，沿边扩展 N 跳，返回 `ChunkWithScore[]` |
| `hydrateChunks()` | 根据 chunk_id 批量补全 `SearchResult` 元数据 |

---

## 11.2 后台作业系统（Minions）

### 11.2.1 为什么要 Minions

有些任务天然很慢，不应该阻塞主流程：

- 大页面向量化（Embedding）：可能涉及数万个 token
- Git sync：网络请求 + diff 计算
- 数据库迁移：大表 ALTER 操作

传统方案是引入 Redis 或 RabbitMQ 等外部队列。GBrain 的 Minions 选择了**更轻量的路**：用 PGLite 本身存储任务状态，不依赖额外的基础设施。

### 11.2.2 架构概览

```{mermaid}
flowchart LR
    subgraph 主流程
        A["主进程<br/>BrainEngine"] --> B["MinionQueue<br/>任务入队"]
    end
    
    subgraph Worker进程
        C["MinionWorker<br/>抢占式拉取"] --> D["Handler<br/>任务处理"]
        D --> E["结果回写<br/>PGLite"]
    end
    
    B -->|"poll 'waiting' 任务<br/>SETFORUPDATE SKIP LOCKED"| C
    E --> B
    
    style A fill:#e1f5ff
    style C fill:#fff3e0
    style E fill:#e8f5e9
```

### 11.2.3 队列实现：不用外部依赖

Minions 的任务队列本质是一张 PostgreSQL 表：

```sql
CREATE TABLE minions_jobs (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,           -- 任务类型: 'embedding', 'git-sync', 'migrate'
  queue TEXT NOT NULL DEFAULT 'default',
  status TEXT NOT NULL,          -- waiting/active/completed/failed/delayed/dead
  priority INTEGER DEFAULT 0,
  data JSONB NOT NULL,           -- 任务负载
  attempts_made INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  backoff_type TEXT DEFAULT 'exponential',
  backoff_delay INTEGER DEFAULT 1000,
  -- 等等...
);
```

Worker 抢占式拉取任务，用 `SELECT ... FOR UPDATE SKIP LOCKED` 确保多 Worker 不会抢到同一个任务：

```sql
SELECT * FROM minions_jobs
  WHERE status = 'waiting' AND queue = $1
  ORDER BY priority DESC, id ASC
  LIMIT 1
  FOR UPDATE SKIP LOCKED;
```

### 11.2.4 心跳机制

Worker 定期更新任务状态为 `active`，同时更新 `attempts_started` 时间戳。如果主进程发现某个 `active` 任务的 `attempts_started` 超过阈值（默认 60 秒），就认为该 Worker 已崩溃，将任务重新放回 `waiting` 队列等待重试。

```typescript
// 60 秒无心跳，任务重新入队
const STALLED_INTERVAL_MS = 60_000;
```

### 11.2.5 主要任务类型

| 任务类型 | Handler | 说明 |
|----------|---------|------|
| **大页面向量化** | `handlers/shell.ts` | 超过单次 embedding 上限的大页面，入队后台处理 |
| **Git sync** | `handlers/subagent.ts` | 定时从远程仓库拉取更新 |
| **迁移任务** | `handlers/shell.ts` | `gbrain apply-migrations` 触发的 schema 变更 |

---

## 11.3 Resolver 系统

### 11.3.1 Resolver 是什么

**Resolver** = 从外部数据源获取信息的模块。它是 GBrain 与外部世界交互的桥梁。

当你问「@alice 今天发了什么推文」，Resolver 负责：
1. 解析输入（`@alice` → X handle）
2. 调用 X API 获取数据
3. 格式化结果返回

### 11.3.2 统一接口设计

所有 Resolver 实现统一的 `resolve(input): Promise<Output>` 接口：

```typescript
// resolvers/interface.ts
export interface Resolver<I, O> {
  readonly id: string;           // 唯一标识，如 "x_handle_to_tweet"
  readonly cost: ResolverCost;   // 'free' | 'rate-limited' | 'paid'
  readonly backend: string;      // "x-api-v2", "brain-local", "head-check"

  // 上下文感知：能读取 brain 自身数据
  available(ctx: ResolverContext): Promise<boolean>;
  resolve(req: ResolverRequest<I>): Promise<ResolverResult<O>>;
}

export interface ResolverResult<O> {
  value: O;
  confidence: number;    // 0.0-1.0，LLM 回的有可能是推断的
  source: string;       // 来源标识
  fetchedAt: Date;
  costEstimate?: number; // 美元成本估算
}
```

关键设计原则：**confidence 机制**。LLM 提取的信息 confidence < 1.0，直接 API 响应的 confidence = 1.0。调用方用这个字段决定是否要人工确认。

### 11.3.3 调用链

```{mermaid}
flowchart TD
    A["LLM / Agent"] --> B["ResolverRegistry.resolve()"]
    B --> C{"available()?"}
    C -->|否| D["ResolverError: unavailable"]
    C -->|是| E["resolver.resolve()"]
    E --> F["返回 ResolverResult"]
    
    subgraph 内置 Resolver
        G["GitHub Resolver"]
        H["X (Twitter) Resolver"]
        I["Notion Resolver"]
        J["Brain-local Resolver"]
    end
    
    E --> G
    E --> H
    E --> I
    E --> J
```

### 11.3.4 内置 Resolver

| Resolver | 输入 | 输出 | 费用 |
|----------|------|------|------|
| `x_handle_to_tweet` | X handle | 用户最新推文 | API 费用 |
| `github_issue` | issue URL | issue 内容 + 评论 | API 费用 |
| `brain_local` | slug | brain 页面内容 | 免费 |
| `url_reachable` | URL | HTTP HEAD 检查结果 | 免费 |

### 11.3.5 自定义 Resolver

自定义 Resolver 需要：

1. 实现 `Resolver<I, O>` 接口
2. 在 `resolvers/registry.ts` 中注册

```typescript
// 示例：自定义 URL 检查 Resolver
const myResolver: Resolver<string, boolean> = {
  id: 'url_reachable',
  cost: 'free',
  backend: 'head-check',
  available: async (ctx) => !!ctx.config['networkEnabled'],
  resolve: async (req) => ({
    value: await checkUrl(req.input),
    confidence: 1.0,
    source: 'head-check',
    fetchedAt: new Date(),
  }),
};
```

---

## 11.4 迁移框架

### 11.4.1 为什么需要迁移框架

GBrain 使用 **PGLite**（嵌入式 PostgreSQL）或完整 **Postgres + pgvector**。随着版本迭代，数据库 schema 会发生变化。迁移框架确保 schema 演进时数据不丢失、升级平滑。

典型场景：
- 新增表或索引
- 修改字段类型
- 重建既有数据（如 `slugify_existing_pages`）

### 11.4.2 迁移设计

```typescript
// core/migrate.ts
interface Migration {
  version: number;       // 版本号，必须单调递增
  name: string;          // 人类可读名称
  sql: string;           // 迁移 SQL
  sqlFor?: {             // 引擎特定 SQL
    postgres?: string;   // Postgres 的版本（如 CONCURRENTLY）
    pglite?: string;     // PGLite 的版本
  };
  transaction?: boolean; // 是否在事务中执行（默认 true）
  handler?: (engine: BrainEngine) => Promise<void>; // TS 级数据转换
}
```

### 11.4.3 执行顺序

迁移按版本号顺序执行，每个迁移都在事务中运行：

```sql
-- 伪代码
BEGIN;
UPDATE schema_versions SET version = $new_version WHERE version = $old_version;
$sql
COMMIT;
```

如果 SQL 失败，版本号不变，下次启动时重试。

### 11.4.4 迁移命名约定

```
Version 1:  基线（schema.sql 创建所有表，IF NOT EXISTS）
Version 2:  slugify_existing_pages — 重命名既有页面 slug
Version 3:  unique_chunk_index — 去重 + 添加唯一索引
Version 4:  access_tokens_and_mcp_log — 新增访问令牌表
...
```

**规则**：从不修改已发布的迁移，只在末尾追加新迁移。每个迁移必须**幂等**（重复执行结果相同）。

---

## 11.5 安全机制

### 11.5.1 `remote` 字段的信任边界

`remote` 字段是 GBrain 安全模型的核心，它区分了两类调用者：

| 调用来源 | `remote` 值 | 含义 |
|----------|-------------|------|
| `cli.ts` 本地 CLI | `false` | 受信任的本地用户 |
| `mcp/server.ts` | `true` | 不受信任的外部 Agent |

**信任边界规则**：

- `remote = false`：允许文件系统全权访问，允许执行 shell 命令
- `remote = true`：启用严格的文件路径限制（ confinement），SSRF 防护激活

### 11.5.2 SQL Injection 防护

GBrain 使用 **参数化查询**（Parameterized Query）防止 SQL 注入：

```typescript
// ✅ 正确：参数绑定
await engine.executeRaw(
  `SELECT id FROM content_chunks WHERE symbol_name_qualified = $1`,
  [userInput]  // 参数绑定
);

// ❌ 错误：字符串拼接（绝对禁止）
await engine.executeRaw(
  `SELECT id FROM content_chunks WHERE symbol_name_qualified = '${userInput}'`
);
```

所有 `engine.executeRaw()` 调用都使用 `$1, $2` 参数占位符，由底层数据库驱动处理转义。

### 11.5.3 外部内容导入时的 Sanitization

当从外部（URL、API 响应）导入内容到 brain 时：

1. **HTML 净化**：使用 `marked` 解析 Markdown 时，禁用原始 HTML
2. **路径穿越防护**：文件路径必须位于 `root` 目录下，symlink 会被拒绝
3. **Frontmatter 验证**：不合法的 frontmatter 字段被丢弃

```typescript
// import-file.ts 中的净化逻辑示例
const sanitized = {
  ...frontmatter,
  // 移除危险字段
  _raw: undefined,
  __proto__: undefined,
  constructor: undefined,
};
```

---

## 11.6 MCP 服务端

### 11.6.1 什么是 MCP

**MCP（Model Context Protocol）** 是一种标准协议，让 AI Agent 可以调用外部工具。GBrain 作为 MCP Provider，把自身操作暴露为 MCP tools，供 Claude Desktop、Cursor 等 AI 工具调用。

### 11.6.2 服务端实现

```typescript
// mcp/server.ts
export async function startMcpServer(engine: BrainEngine) {
  const server = new Server(
    { name: 'gbrain', version: VERSION },
    { capabilities: { tools: {} } }
  );

  // 1. 暴露工具列表
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: buildToolDefs(operations),  // 从 operations.ts 导出工具定义
  }));

  // 2. 处理工具调用
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: params } = request.params;
    const ctx: OperationContext = {
      engine,
      remote: true,  // MCP 调用一律视为 untrusted
      // ...
    };
    const result = await op.handler(ctx, params);
    return { content: [{ type: 'text', text: JSON.stringify(result) }] };
  });

  await server.connect(new StdioServerTransport());
}
```

### 11.6.3 工具定义

`tool-defs.ts` 把 `operations.ts` 中的 Operation 映射为 MCP tool：

```typescript
// mcp/tool-defs.ts
export function buildToolDefs(ops: Operation[]): McpToolDef[] {
  return ops.map(op => ({
    name: op.name,
    description: op.description,
    inputSchema: {
      type: 'object',
      properties: Object.fromEntries(
        Object.entries(op.params).map(([k, v]) => [k, { type: v.type }])
      ),
      required: Object.entries(op.params)
        .filter(([, v]) => v.required)
        .map(([k]) => k),
    },
  }));
}
```

### 11.6.4 和直接 CLI 调用的区别

| 维度 | CLI 调用 | MCP 调用 |
|------|---------|---------|
| `remote` | `false`（受信任） | `true`（不受信任） |
| 文件限制 | 允许访问 home 目录 | 限制在 `root` 目录 |
| Shell 执行 | 允许 | 受限 |
| 用途 | 人类用户直接操作 | AI Agent 自动化调用 |

---

## 本章小结

本章深入介绍了 GBrain 的几个高级主题：

- **Cathedral II** 通过两遍检索解决了传统 RAG 的「中间丢失」问题，利用代码结构边扩展检索范围
- **Minions** 用 PGLite 本身做队列存储，实现了零外部依赖的后台作业系统
- **Resolver** 提供统一接口连接外部数据源，confidence 机制确保结果可靠性
- **迁移框架** 用版本号 + 幂等 SQL 保证 schema 演进安全
- **安全机制** 通过 `remote` 字段区分信任边界，参数化查询防注入
- **MCP** 把 GBrain 操作暴露为标准协议工具，供 AI Agent 调用

这些机制共同支撑了 GBrain 作为「个人知识大脑」的可靠性和可扩展性。

---

*GBrain v0.22.5 · 源码路径：`/home/liyifan/gbrain/src/`*
