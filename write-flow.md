# 第五章：写入流程（Write Flow）

> 本章追踪一条笔记从创建到被存储的完整生命周期——这是 GBrain 最核心的数据流。

---

## 5.1 从 `put_page` 开始

当你调用 `gbrain put` 或者通过 MCP 工具 `brain_put` 写入一条笔记时，请求首先到达 **Operation 注册表**（`operations.ts`）。Operation 是 GBrain 的统一操作抽象——所有功能（CLI、MCP、代码调用）都通过同一套注册机制暴露。

```typescript
const put_page: Operation = {
  name: 'put_page',
  description: 'Write/update a page (markdown with frontmatter).',
  params: {
    slug: { type: 'string', required: true },
    content: { type: 'string', required: true },
  },
  handler: async (ctx, p) => {
    // 核心逻辑
  },
};
```

`put_page` 的 handler 做了几件关键的事：

1. **权限检查**：`viaSubagent=true` 时强制要求写入路径前缀为 `wiki/agents/${subagentId}/`
2. **提前预检**：没有 `OPENAI_API_KEY` 时跳过 embedding 步骤，避免无意义的重试
3. **调用 `importFromContent`**：这是写入流程的实际执行者，封装在事务中

最终，handler 通过 `BrainEngine` 接口完成数据持久化。`BrainEngine` 是 PGLite 引擎和 Postgres 引擎的共同接口——上层代码完全不感知底层是嵌入式 WASM 数据库还是远程 Postgres：

```{mermaid}
sequenceDiagram
    participant CLI as gbrain put
    participant MCP as MCP brain_put
    participant Op as operations.ts
    participant Engine as BrainEngine
    participant DB as PGLite/Postgres

    CLI->>Op: put_page(slug, content)
    MCP->>Op: put_page(slug, content)
    Op->>Engine: putPage(slug, pageInput)
    Engine->>Engine: parseMarkdown()
    Engine->>Engine: extractPageLinks()
    Engine->>Engine: extractTimelineEntries()
    Engine->>Engine: upsertChunks()
    Engine->>Engine: addLinksBatch()
    Engine->>Engine: addTimelineEntriesBatch()
    Engine->>DB: COMMIT
```

---

## 5.2 内容解析链路

`put_page` 接收的 `content` 是完整的 Markdown 文本，包含 YAML frontmatter、 正文和时间线区域。解析链路如下：

```
putPage(content)
    ↓
parseMarkdown(content) → { frontmatter, compiled_truth, timeline, type, title }
    ↓
extractPageLinks(compiled_truth + timeline) → LinkCandidate[]
extractTimelineEntries(timeline) → TimelineEntry[]
    ↓
importFromContent() 在事务中写入 Page + Links + TimelineEntries
```

### 为什么需要 AST 解析？

有人会问：提取链接用正则不就行了吗？还真不行。GBrain 使用 `gray-matter` 库解析 YAML frontmatter，这不只是简单的"找 `---` 分隔符"——gray-matter 处理了：

- **嵌套引号**（`NESTED_QUOTES` 错误检测）
- **NULL 字节**检测（`NULL_BYTES` 错误，二进制损坏指示器）
- **Slug 不匹配**检测（`SLUG_MISMATCH`，frontmatter 中的 slug 与路径不一致）

对于正文，GBrain 需要区分：
- `<!-- timeline -->` sentinel 之前的正文（`compiled_truth`）
- `<!-- timeline -->` sentinel 之后的时间线内容（`timeline`）
- 代码块内的文字（链接提取时会跳过，避免把代码示例中的 slug 当作引用）

### 链接提取：`link-extraction.ts` 的纯函数设计

这是 GBrain 中设计最优雅的模块之一。`extractPageLinks()` 是一个**纯函数**——输入 Markdown 文本，输出链接数组，完全没有副作用，不访问数据库。

```typescript
// 核心签名
export async function extractPageLinks(
  slug: string,
  content: string,
  frontmatter: Record<string, unknown>,
  pageType: PageType,
  resolver: SlugResolver,
): Promise<PageLinksResult>
```

**为什么这样设计？**

1. **易于测试**：不需要 mock 数据库，直接用文本断言
2. **可组合**：可以在任何上下文调用（写入时、批量提取时）
3. **无状态**：同一段文本无论调用多少次都产生相同结果

**提取的链接类型：**

| 来源 | 示例 | 类型 |
|------|------|------|
| Markdown 链接 | `[Alice Chen](../people/alice-chen)` | `markdown` |
| Wikilink | `[[people/alice-chen]]` | `markdown` |
| Qualified Wikilink | `[[twitter:person/alice-chen]]` | `markdown` |
| Bare slug 引用 | `see people/alice-chen for context` | `markdown` |
| Frontmatter 字段 | `investors: [fund-a, fund-b]` | `frontmatter` |

**关系类型推断**（`inferLinkType`）是另一层纯函数逻辑。根据源页面类型和上下文中的动词，GBrain 自动推断链接关系：

- `founded` — 创始人关系（"founded", "co-founded"）
- `invested_in` — 投资关系（"led the seed", "invests in", "portfolio company"）
- `advises` — 顾问关系（"advises", "advisory board"）
- `works_at` — 雇佣关系（"engineer at", "joined as", "CTO of"）
- `attended` — 会议参与（meeting 类型页面）

```typescript
// 推断优先级：founded > invested_in > advises > works_at > role prior > mentions
if (FOUNDED_RE.test(context)) return 'founded';
if (INVESTED_RE.test(context)) return 'invested_in';
```

### 时间线提取

时间线内容从 Markdown 中 `<!-- timeline -->` sentinel 处分割后，传入 `parseTimelineEntries()`。这个函数同样是纯函数，返回 `TimelineEntry[]`。

---

## 5.3 分块（Chunking）

解析后的 `compiled_truth` 和 `timeline` 文本在写入数据库之前需要**分块**（chunking）。这是因为：

1. **Token 限制**：OpenAI embedding 模型有 8192 token 的输入限制
2. **检索精度**：小块可以更精准地匹配查询意图
3. **重叠保真**：重叠分块保证边界内容不会丢失上下文

### Chunker 接口

```typescript
interface Chunker {
  chunk(page: PageInput, chunkIndexOffset?: number): ChunkInput[];
}
```

GBrain 实现了三种 Chunker：

| Chunker | 文件 | 适用场景 | 分块策略 |
|---------|------|----------|----------|
| **Recursive** | `chunkers/recursive.ts` | 普通文本 | 5级分隔符递进：段落→行→句子→从句→单词 |
| **Code** | `chunkers/code.ts` | 源代码文件 | tree-sitter AST 感知，按函数/类/方法分块 |
| **Semantic** | `chunkers/semantic.ts` | 语义分块 | 基于 Embedding 相似度自动切分 |

### Recursive Chunker 的分层策略

```typescript
const DELIMITERS: string[][] = [
  ['\n\n'],                          // L0: 段落
  ['\n'],                            // L1: 行
  ['. ', '! ', '? ', '.\n', '!\n', '?\n'], // L2: 句子
  ['; ', ': ', ', '],               // L3: 从句
  [],                                // L4: 单词（whitespace split）
];
```

从最高层（段落）开始尝试切分，如果切分后仍有块超过目标大小，就递归到下一层（行），依此类推。这种方式保证了分块尽量在自然语言边界处断裂。

### 重叠分块（Overlap）

连续块之间有 50 个单词的重叠（默认配置），这样即使查询恰好落在块边界附近，也能找到相关上下文：

```
Chunk 0: [word_0 ... word_299]
Chunk 1: [word_250 ... word_549]  ← 重叠 word_250-299
Chunk 2: [word_500 ... word_799]  ← 重叠 word_500-549
```

### 污点标记（Dirty Chunks）

当页面内容更新时，不是所有 chunk 都需要重新 embedding。GBrain 通过 `content_hash` 追踪：只有内容发生变化的 chunk 会被标记为"污点"（stale），等待重新向量化。

```sql
-- 污点查询：embedded_at IS NULL 的 chunk
SELECT slug, chunk_index, chunk_text FROM content_chunks
WHERE embedded_at IS NULL;
```

---

## 5.4 向量化（Embedding）

分块后的文本通过 `embedding.ts` 转换为向量。GBrain 使用 **OpenAI `text-embedding-3-large`** 模型，输出 **1536 维**向量。

### 批量向量化

`embedBatch()` 一次最多处理 100 条文本，通过一条 API 请求完成：

```typescript
const BATCH_SIZE = 100;

export async function embedBatch(texts: string[]): Promise<Float32Array[]> {
  for (let i = 0; i < texts.length; i += BATCH_SIZE) {
    const batch = texts.slice(i, i + BATCH_SIZE);
    const batchResults = await embedBatchWithRetry(batch);
    results.push(...batchResults);
  }
  return results;
}
```

### 失败重试策略

单个 chunk 失败不影响整页写入。`embedBatchWithRetry` 实现了**指数退避**：

- 基础延迟：4 秒
- 最大延迟：120 秒
- 最多重试：5 次
- 429 响应时优先尊重 `Retry-After` header

```typescript
function exponentialDelay(attempt: number): number {
  const delay = BASE_DELAY_MS * Math.pow(2, attempt);
  return Math.min(delay, MAX_DELAY_MS);
}
```

### 向量存储

向量以 `pgvector` 类型存入 PGLite/Postgres 的 `content_chunks` 表：

```sql
ALTER TABLE content_chunks ADD COLUMN embedding vector(1536);
```

`Float32Array` 直接作为参数传入，由 `pgvector` 扩展处理序列化。

---

## 5.5 双写：数据库 + 文件系统

GBrain 的一个核心设计是**双重存储**：

1. **内存数据库**（PGLite/Postgres）— 用于 AI 搜索
2. **文件系统**（`.md` 文件）— 用于 Git 版本控制

### 写入流程

`put_page` handler 写入的是**内存数据库**。`sync.ts` 负责在适当时机将内存状态导出为文件系统中的 `.md` 文件：

```{mermaid}
flowchart LR
    A[put_page] --> B[parseMarkdown]
    B --> C[importFromContent]
    C --> D[upsertChunks + addLinksBatch]
    D --> E[数据库 COMMIT]
    E --> F[sync.ts 写 .md 文件]
    F --> G[Git 提交]
```

### 一致性保证

两者的一致性通过以下机制保证：

1. **原子事务**：数据库写入在事务内完成，失败自动回滚
2. **Slug 作为主键**：Page 的 slug 同时用于数据库和文件系统路径
3. **Markdown 文件格式**：GBrain 的文件格式是自描述的（包含 frontmatter），可以直接从文件恢复数据库状态

`gbrain sync` 命令会解析 `git diff --name-status -M`，将文件系统的变更（新增/修改/删除/重命名）同步到数据库，实现双向一致。

---

## 5.6 完整数据流图

```{mermaid}
flowchart TD
    subgraph Input["入口"]
        CLI[gbrain put]
        MCP[MCP brain_put]
    end

    subgraph Parse["解析层"]
        MD[markdown.ts<br/>parseMarkdown]
        LE[link-extraction.ts<br/>extractPageLinks]
        TE[link-extraction.ts<br/>parseTimelineEntries]
    end

    subgraph Chunk["分块层"]
        CH[分块决策]
        REC[Recursive<br/>Chunker]
        CODE[Code<br/>Chunker]
        SEM[Semantic<br/>Chunker]
    end

    subgraph Embed["向量化层"]
        EMB[embedding.ts<br/>embedBatch]
        RET[失败重试<br/>指数退避]
        PG[pgvector<br/>1536维向量]
    end

    subgraph Store["存储层"]
        DB[(PGLite /<br/>Postgres)]
        FS[.md 文件]
    end

    CLI --> MCP
    MCP --> Operation[operations.ts<br/>put_page handler]
    Operation --> MD
    MD --> LE
    MD --> TE
    LE --> CH
    TE --> CH
    CH --> REC
    CH --> CODE
    CH --> SEM
    REC --> EMB
    CODE --> EMB
    SEM --> EMB
    EMB --> RET
    RET --> PG
    PG --> DB
    DB --> FS

    MD -->|compiled_truth + timeline| CH
    Operation -->|importFromContent| DB
    DB -->|sync.ts| FS
```

**数据转换节点说明：**

| 节点 | 输入 | 输出 |
|------|------|------|
| `parseMarkdown` | 原始 Markdown 文本 | `{ frontmatter, compiled_truth, timeline, type, title }` |
| `extractPageLinks` | `compiled_truth + frontmatter` | `LinkCandidate[]` |
| `parseTimelineEntries` | `timeline` 文本 | `TimelineEntry[]` |
| `RecursiveChunker` | 长文本 | `ChunkInput[]`（300词/块，50词重叠） |
| `embedBatch` | `string[]` | `Float32Array[]`（1536维） |

---

## 本章小结

写入流程是 GBrain 最核心的数据流，涉及：

1. **Operation 抽象层**：CLI 和 MCP 共享同一 handler
2. **纯函数解析**：Markdown 解析和链接提取无副作用、易测试
3. **智能分块**：根据内容类型选择不同策略，保持上下文连续性
4. **弹性向量化**：批量 API 调用 + 指数退避重试，单点失败不阻塞整页
5. **双重存储**：数据库驱动 AI 搜索，文件系统对接 Git 版本控制

理解这条链路，是理解 GBrain 全部高级功能（搜索、知识图谱、代码理解）的基础。
