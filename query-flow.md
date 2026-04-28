# 第七章：查询流程（Query Flow）

> 本章讲解 GBrain 如何处理用户的查询请求，从 CLI/MCP 入口到混合搜索管线，是理解整个系统智能化能力的核心。

---

## 7.1 查询入口

GBrain 提供两套查询接口，分别满足不同的使用场景。

### 7.1.1 CLI 入口

在命令行环境中，有两个相关命令：

```bash
# 混合搜索（语义 + 关键词融合）
gbrain query "如何实现 Rust 错误处理"

# 纯关键词搜索（无需 OpenAI API Key）
gbrain search "Rust 错误处理"
```

两者底层都通过 `operations.ts` 中注册的 Operation 分发：

| Operation | 描述 | 引擎调用 |
|-----------|------|----------|
| `query` | 混合搜索，向量 + 关键词 + 查询扩展 | `hybridSearch()` |
| `search` | 纯关键词搜索 | `engine.searchKeyword()` |

### 7.1.2 MCP 入口

通过 Model Context Protocol 暴露为 Tool，工具名与 Operation 同名：

- `query` — 对应 `brain_query`（MCP 协议中映射后的名字）
- `search` — 对应 `brain_search`

MCP 服务端（`mcp/server.ts`）通过 `buildToolDefs()` 将 Operation 列表自动转换为 MCP Tool 定义，无需手动维护：

```typescript
// mcp/tool-defs.ts
export function buildToolDefs(ops: Operation[]): McpToolDef[] {
  return ops.map(op => ({
    name: op.name,           // "query" / "search"
    description: op.description,
    inputSchema: { ... },     // 从 params 自动推导
  }));
}
```

### 7.1.3 Operation 注册表

所有查询操作在 `core/operations.ts` 中注册为标准 `Operation` 对象：

```typescript
// core/operations.ts
const query: Operation = {
  name: 'query',
  description: 'Hybrid search with vector + keyword + multi-query expansion',
  params: {
    query: { type: 'string', required: true },
    limit: { type: 'number' },
    detail: { type: 'string' },  // 'low' | 'medium' | 'high'
    walk_depth: { type: 'number' },
    near_symbol: { type: 'string' },
    // ...
  },
  handler: async (ctx, p) => {
    return hybridSearch(ctx.engine, p.query as string, { ... });
  },
};
```

`OperationContext` 携带关键上下文：

```typescript
interface OperationContext {
  engine: BrainEngine;       // 数据层抽象
  config: GBrainConfig;       // 配置
  logger: Logger;
  remote: boolean;            // 信任边界：CLI=false, MCP=true
}
```

`remote = true` 时启用严格文件路径限制，防止来自 MCP/Agent 的路径遍历攻击。

---

## 7.2 查询解析（Query Parsing）

用户输入是自然语言，GBrain 需要理解「查什么」才能在正确粒度上召回结果。

### 7.2.1 意图检测（Intent Classification）

`search/intent.ts` 实现了零延迟的启发式意图分类器，基于正则模式匹配判断查询类型：

```typescript
export type QueryIntent = 'entity' | 'temporal' | 'event' | 'general';

export function autoDetectDetail(query: string): 'low' | 'medium' | 'high' | undefined {
  return intentToDetail(classifyQueryIntent(query));
}
```

意图到 detail 级别的映射：

| 意图 | Detail 级别 | 说明 |
|------|-------------|------|
| `entity`（who is / what is） | `low` | 只要 compiled_truth（用户想要实体评估） |
| `temporal`（when / last meeting / timeline） | `high` | 需要 timeline 全文（用户想要时间线） |
| `event`（announced / launched / raised $） | `high` | 需要事件详情 |
| `general` | `undefined` | 使用默认 boost |

这套分类完全在进程内执行，没有 LLM 调用，没有额外延迟。

### 7.2.2 查询扩展（Query Expansion）

当 `expansion: true` 时（默认开启），原始查询会通过 `expandQuery()` 生成多个同义改写，提升召回率。

**实现**（`search/expansion.ts`）：

1. **安全清洗**：用户查询先通过 `sanitizeQueryForPrompt()` 去除代码块、XML 标签、prompt 注入模式
2. **LLM 生成**：调用 Claude Haiku 生成 2 个替代查询（用 tool_choice 约束输出格式）
3. **输出验证**：`sanitizeExpansionOutput()` 过滤非字符串、控制字符、超长输出

```typescript
export async function expandQuery(query: string): Promise<string[]> {
  // < 3 个词不扩展（信号不足）
  const wordCount = hasCJK ? query.replace(/\s/g, '').length : query.match(/\S+/g)?.length ?? 0;
  if (wordCount < 3) return [query];

  const alternatives = await callHaikuForExpansion(sanitized);
  // 返回: [原始查询, 替代1, 替代2]（最多3个）
  return [query, ...alternatives].slice(0, MAX_QUERIES);
}
```

安全设计（三层防御）：

- **M1**：结构化 prompt boundary，用户查询包裹在 `<user_query>` 标签内并声明为 untrusted data
- **M2**：输出验证（sanitizeExpansionOutput）防止 LLM 注入
- **M3**：隐私保护，sanitization 失败时只打印 warning 不记录查询内容

---

## 7.3 混合搜索管线（Hybrid Search Pipeline）

这是 GBrain 搜索能力的核心。`hybridSearch()` 函数（`search/hybrid.ts`）编排了一条完整的多阶段管线。

### 7.3.1 整体流程

```{mermaid}
flowchart TD
    UserQuery["用户查询"]
    Intent["意图检测<br/>autoDetectDetail()"]
    KW["关键词搜索<br/>searchKeyword()"]
    Vec["向量搜索<br/>searchVector()"]
    RRF["RRF 融合<br/>rrfFusion()"]
    Cosine["余弦重打分<br/>cosineReScore()"]
    Backlink["反链增强<br/>applyBacklinkBoost()"]
    Dedup["结果去重<br/>dedupResults()"]
    Output["SearchResult[]"]

    UserQuery --> Intent
    Intent --> KW
    Intent --> Vec
    KW --> RRF
    Vec --> RRF
    RRF --> Cosine
    Cosine --> Backlink
    Backlink --> Dedup
    Dedup --> Output

    style KW fill:#e1f5fe
    style Vec fill:#f3e5f5
    style RRF fill:#fff3e0
```

### 7.3.2 各阶段详解

#### 关键词搜索（Keyword Search）

基于 PostgreSQL `pg_trgm` 扩展的 trigram 模糊匹配。不需要 OpenAI API Key，始终可用。

```typescript
const keywordResults = await engine.searchKeyword(query, searchOpts);
```

SQL 层面包含：
- `tsvector` 权重排序（title > compiled_truth > chunk_text）
- 来源 Boost（`source-boost.ts` 的 slug 前缀权重）
- 硬排除（test/, archive/ 等噪音路径）

#### 向量搜索（Vector Search）

需要 `OPENAI_API_KEY`。使用 `text-embedding-3-large`（1536 维）将查询文本转为向量：

```typescript
const queryEmbedding = await embed(query);
const vectorResults = await engine.searchVector(queryEmbedding, searchOpts);
```

SQL 使用 `cosine_distance <=>` 操作符在 pgvector 中找到最接近的 Chunk。

#### 查询扩展增强

如果启用了 expansion，每个扩展查询都会独立做向量搜索：

```typescript
const embeddings = await Promise.all(queries.map(q => embed(q)));
vectorLists = await Promise.all(
  embeddings.map(emb => engine.searchVector(emb, searchOpts)),
);
```

融合后，`queries` 个向量搜索结果 + 1 个关键词搜索结果一起送入 RRF。

#### 无 API Key 降级

如果未配置 `OPENAI_API_KEY`，跳过向量搜索，keyword 结果直接走 backlink boost → dedup 流程。

---

## 7.4 两遍检索（Two-Pass Retrieval / Cathedral II）

> v0.20.0 Cathedral II 的核心创新，针对代码搜索场景。

两遍检索解决了一个核心矛盾：**向量搜索语义召回好，但精确关键词匹配弱**。

### 7.4.1 核心思想

```{mermaid}
flowchart LR
    Pass1["第一遍：锚点检索<br/>关键词/向量找到候选 Chunk"]
    CodeEdges["代码调用图遍历<br/>code_edges_chunk<br/>code_edges_symbol"]
    Pass2["第二遍：结构邻居收集<br/>score × 1/(1+hop)"]
    Final["混合结果"]

    Pass1 --> CodeEdges --> Pass2 --> Final
```

**第一遍**：普通混合搜索找到锚点（anchor）Chunk。

**第二遍**：从锚点出发，沿代码调用图（`code_edges_chunk` / `code_edges_symbol`）向外扩展 `walkDepth` 跳，将邻居 Chunk 纳入候选列表。

### 7.4.2 `two-pass.ts` 实现

```typescript
export async function expandAnchors(
  engine: BrainEngine,
  anchors: SearchResult[],
  opts: TwoPassOpts,
): Promise<ChunkWithScore[]> {
  const depth = Math.min(opts.walkDepth ?? 0, MAX_WALK_DEPTH); // 最大2跳

  const seen = new Map<number, ChunkWithScore>();
  // 初始化锚点
  for (const a of anchors) {
    seen.set(a.chunk_id, { chunk_id: a.chunk_id, score: a.score, hop: 0, source: 'anchor' });
  }

  // 跳数衰减：score × 1/(1+hop)
  for (let hop = 1; hop <= depth; hop++) {
    for (const chunkId of frontier) {
      const edges = await engine.getEdgesByChunk(chunkId, { direction: 'both', limit: 50 });
      for (const tid of directChunkIds) {
        if (!seen.has(tid)) {
          seen.set(tid, {
            chunk_id: tid,
            score: current.score * (1 / (1 + hop)),
            hop,
            source: 'neighbor',
          });
        }
      }
    }
  }

  return Array.from(seen.values());
}
```

关键参数：
- `walkDepth`：1 或 2（超过 2 跳的图邻居爆炸太大）
- `NEIGHBOR_CAP_PER_HOP = 50`：每跳最多 50 个邻居，防止扇出攻击

### 7.4.3 邻居_chunk_id 的两种来源

| 边类型 | `to_chunk_id` | 后续处理 |
|--------|---------------|----------|
| `code_edges_chunk` | 直接可用的 Chunk ID | 直接跟踪 |
| `code_edges_symbol` | `null`，只有 `to_symbol_qualified` | 需反向查询 symbol 对应的 Chunk |

```typescript
// 对 symbol 边做反向解析
const resolved = await engine.executeRaw(
  `SELECT id FROM content_chunks WHERE symbol_name_qualified = ANY($1::text[])`,
  [unresolvedTargets],
);
```

### 7.4.4 去重 Cap 的动态调整

普通混合搜索每页最多保留 2 个 Chunk。两遍检索时，cap 放宽到 `min(10, walkDepth × 5)`，确保来自同一文件的结构邻居不被错误裁剪。

---

## 7.5 结果重排（Rerank）

RRF 融合后的结果还需要经过多轮增强，才能输出最终排序。

### 7.5.1 余弦重打分（Cosine Re-Score）

RRF 排名反映的是「多搜索引擎的一致性」，但不够精确。`cosineReScore()` 用 query embedding 和 chunk embedding 的余弦相似度做精细调整：

```typescript
// hybrid.ts
const blended = 0.7 * normRrf + 0.3 * cosine;
```

权重分配：RRF 占 70%，余弦相似度占 30%。重打分在 dedup 之前执行，确保语义更好的 Chunk 能存活到去重阶段。

### 7.5.2 反链增强（Backlink Boost）

被更多页面引用的页面排名更高：

```typescript
// BACKLINK_BOOST_COEF = 0.05
r.score *= (1.0 + 0.05 * Math.log(1 + backlinkCount));
```

| 反链数 | Boost 系数 |
|--------|-----------|
| 0 | 1.0（无 boost） |
| 1 | ≈ 1.035 |
| 10 | ≈ 1.12 |
| 100 | ≈ 1.23 |

### 7.5.3 来源 Boost（Source Boost）

某些目录的页面天然比另一些更重要（`source-boost.ts`）：

| Slug 前缀 | Boost 因子 | 说明 |
|-----------|-----------|------|
| `originals/` | 1.5 | 原创高质量写作 |
| `concepts/` | 1.3 | 概念框架 |
| `writing/` | 1.4 | 长文 |
| `daily/` | 0.8 | 日常记录（降权） |
| `wintermute/chat/` | 0.5 | 聊天记录（大幅降权） |

通过 `GBRAIN_SOURCE_BOOST` 环境变量覆盖默认值。

### 7.5.4 Compiled Truth 保障

每个页面至少要有一个 `compiled_truth` 类型的 Chunk 出现在最终结果中。如果 dedup 过程中把某页的所有 compiled_truth 都去掉了，`guaranteeCompiledTruth()` 会从 pre-dedup 结果中找回最高分的 compiled_truth Chunk 替换进来。

---

## 7.6 完整查询时序图

```{mermaid}
sequenceDiagram
    participant CLI as CLI / MCP
    participant Op as operations.ts
    participant HS as hybrid.ts
    participant KW as search/keyword.ts
    participant Vec as search/vector.ts
    participant Emb as embedding.ts
    participant Exp as search/expansion.ts
    participant Dedup as search/dedup.ts
    participant Engine as BrainEngine

    CLI->>Op: query "如何实现 Rust 错误处理"
    Op->>HS: hybridSearch(engine, query, opts)

    Note over HS: 7.2 意图检测
    HS->>HS: autoDetectDetail(query)<br/>→ 'low' | 'medium' | 'high'

    Note over HS: 7.2 查询扩展
    HS->>Exp: expandQuery(query)
    Exp-->>HS: [原始查询, 替代1, 替代2]

    par 并行执行
        HS->>Emb: embed(查询1)<br/>embed(查询2)<br/>embed(查询3)
        Emb-->>HS: Float32Array[]
        HS->>Engine: searchVector(embedding, opts)
        Engine-->>HS: vectorResults[][]

        HS->>Engine: searchKeyword(query, opts)
        Engine-->>HS: keywordResults[]
    end

    Note over HS: 7.3 RRF 融合
    HS->>HS: rrfFusion([vectorLists..., keywordResults], RRF_K=60)

    Note over HS: 7.5 余弦重打分
    HS->>Engine: getEmbeddingsByChunkIds(chunkIds)
    Engine-->>HS: embeddingMap
    HS->>HS: cosineReScore() 0.7*normRRF + 0.3*cosine

    Note over HS: 7.5 反链增强
    HS->>Engine: getBacklinkCounts(slugs)
    Engine-->>HS: Map<slug, count>
    HS->>HS: applyBacklinkBoost()

    alt 两遍检索（walkDepth > 0）
        Note over HS: 7.4
        HS->>HS: expandAnchors(anchorSet, walkDepth)
        HS->>Engine: getEdgesByChunk(chunkId)
        HS->>HS: hydrateChunks(newChunkIds)
        HS->>HS: 重新 sort by score
    end

    Note over HS: 7.5 来源 Boost（SQL 层面注入）

    Note over HS: 7.3 结果去重
    HS->>Dedup: dedupResults(fused)
    Dedup-->>HS: SearchResult[]

    HS-->>Op: SearchResult[]
    Op-->>CLI: JSON response
```

### 关键数据结构

```typescript
interface SearchResult {
  slug: string;           // 页面 slug
  page_id: number;        // 页面 ID
  chunk_id?: number;      // Chunk ID（用于去重和 cosine re-score）
  chunk_text: string;     // Chunk 内容原文
  chunk_source: 'compiled_truth' | 'timeline' | 'fenced_code';
  chunk_index: number;    // Chunk 在页面内的序号
  score: number;          // 当前综合得分
  title: string;          // 页面标题
  type: PageType;         // 页面类型
  source_id: string;      // 来源标识（多源支持）
  stale: boolean;         // 是否过期
}

interface HybridSearchOpts {
  limit?: number;
  offset?: number;
  detail?: 'low' | 'medium' | 'high';  // 意图检测结果
  expansion?: boolean;                  // 启用查询扩展
  expandFn?: (q: string) => Promise<string[]>;
  rrfK?: number;                       // RRF 平滑参数
  walkDepth?: number;                  // 两遍检索跳数（0=关闭）
  nearSymbol?: string;                 // 符号名锚点
  symbolKind?: string;                 // 过滤：符号类型
  language?: string;                  // 过滤：编程语言
  dedupOpts?: {
    cosineThreshold?: number;          // 余弦相似度阈值（默认 0.85）
    maxTypeRatio?: number;             // 类型多样性（默认 0.6）
    maxPerPage?: number;               // 每页最大 Chunk 数
  };
}
```

---

## 本章小结

GBrain 的查询流程是一条精心编排的多阶段管线：

1. **入口统一**：CLI 和 MCP 共享同一套 Operation 注册表
2. **意图感知**：零成本启发式分类，决定 detail 粒度和 boost 策略
3. **混合搜索**：关键词 + 向量互补，RRF 融合多个排名列表
4. **两遍检索**：锚点 + 图遍历，专门解决代码结构感知问题
5. **多层增强**：余弦重打分 → 反链 → 来源 → compiled_truth 保障

下一章将对搜索管线的每个子模块做深度技术解析。
