# 第四章：数据模型（Data Model）

> 本章详细介绍 GBrain 的核心数据模型。理解这些实体及其关系，是掌握 GBrain如何组织知识的基础。

---

## 4.1 Page：记忆的基本单元

### 什么是 Page

**Page（页面）** 是 GBrain 中存储知识的基本单元。你可以把它想象成一篇文章、一张卡片、或者一个笔记。每个 Page 对应文件系统中的一个 Markdown 文件。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 全局唯一主键 |
| `slug` | text | URL-safe 的唯一标识符，如 `hello-world`、`project-architecture` |
| `title` | text | 人类可读的标题 |
| `type` | text | 页面类型，用于分类（person、project、event 等） |
| `compiled_truth` | text | 页面的正文内容（见下方格式） |
| `timeline` | text | 时间线部分内容 |
| `frontmatter` | JSONB | 解析后的 YAML 元数据 |
| `remote` | integer | **信任边界标记**：0=本地生成（trusted），1=外部导入（untrusted） |

#### Page 的 ER 关系

```{mermaid}
erDiagram
    pages ||--o{ content_chunks : "has"
    pages ||--o{ links : "from"
    pages ||--o{ links : "to"
    pages ||--o{ timeline_entries : "has"
```
| `created_at` | timestamptz | 创建时间戳 |
| `updated_at` | timestamptz | 最后更新时间戳 |

### Markdown 文件格式

GBrain 的 Markdown 文件有固定的结构：

```markdown
---
type: person
title: Alice Chen
tags: [founder, ai]
remote: 0
---
# Compiled Truth Content

这是页面的正文内容，支持完整的 Markdown 语法。

<!-- timeline -->
## Timeline entries

- 2024-01: 创立公司
- 2024-06: A轮融资
```

关键点：
- `---` 包裹的是 **frontmatter**（YAML 元数据）
- `<!-- timeline -->` 是时间线的分隔标记
- 其余部分都是 `compiled_truth`（正文内容）

### Slug 系统

**Slug** 是 GBrain 中用于唯一标识页面的字符串，由标题自动生成：

| 标题 | 生成的 Slug |
|------|------------|
| `Hello World!` | `hello-world` |
| `Project Architecture v2` | `project-architecture-v2` |
| `What's Next?` | `whats-next` |

Slug 的特点：
- **URL-safe**：只包含小写字母、数字和连字符
- **唯一性**：同一 brain 中不能有两个相同 slug 的页面
- **自动生成**：通常由 `sync.ts` 中的 `pathToSlug()` 函数从文件路径生成

---

## 4.2 Chunk：语义分块

### 为什么需要 Chunk

当你搜索「如何在 Rust 中处理错误」时，GBrain 需要找到最相关的段落，而不是整篇文章——因为整篇文章可能包含多个主题。

**Chunk（分块）** 就是解决这个问题：将一个 Page 的内容切分成多个语义上独立的片段，每个 Chunk 可以独立被检索和引用。

### Chunk 的结构

| 字段 | 说明 |
|------|------|
| `page_id` | 指向所属 Page 的外键 |
| `chunk_source` | 来源类型：`page`=页面文本分块，`fenced_code`=代码块提取 |
| `content` | 分块的实际文本内容 |
| `embedding` | 1536 维向量（`text-embedding-3-large` 模型） |
| `token_count` | content 的 token 数量（用于成本估算） |
| `start_char_index` / `end_char_index` | 在原始 Page 中的位置（用于回溯原文） |
| `is_dirty` | **污点标记**：为 `true` 时表示内容已修改，需要重新生成 embedding |

#### Chunk 与 Page 的关系

```{mermaid}
erDiagram
    pages ||--o{ content_chunks : "one-to-many"
```

### 分块策略（Chunker）

GBrain 支持多种分块策略，适用于不同类型的内容：

```{mermaid}
flowchart TD
    A["原始内容"]
    B{选择策略}
    C["Recursive 递归文本分块"]
    D["Code 代码文件分块"]
    E["Semantic 语义分块"]
    C1["按段落/句子递归切分"]
    D1["使用 tree-sitter 解析"]
    E1["使用 LLM 判断自然语义断点"]
    A --> B
    B --> C
    B --> D
    B --> E
    C --> C1
    D --> D1
    E --> E1
    C1 --> F
    D1 --> F
    E1 --> F
    F["Chunk 列表"]

#### 1. Recursive（递归文本分块）

默认的分块策略，递归地尝试按以下顺序切分：
1. 按 `\n\n` 双换行（段落）切分
2. 如果段落仍过长，按 `\n` 单换行切分
3. 如果句子仍过长，按固定 token 数切分

优点：简单、通用、保持基本语义连贯

#### 2. Code（代码分块）

针对代码文件的专用分块器，使用 **tree-sitter** 解析器：
- 按函数定义（function declaration）切分
- 按类定义（class declaration）切分
- 保留完整的函数上下文（包括 docstring、import 语句）

支持的语言：TypeScript, Python, Go, Rust, Java 等主流语言

#### 3. Semantic（语义分块）

使用 LLM 判断自然语义断点，产生质量更高的分块。适用于长篇文章或需要精确语义的场景。

缺点：需要额外 API 调用，成本较高

### Page 与 Chunk 的关系

```
┌─────────────────────────────────────────┐
│           Page: "Rust 错误处理指南"       │
├─────────────────────────────────────────┤
│                                         │
│  Chunk 1: "## Result 类型简介..."        │
│           (start: 0, end: 500)           │
│                                         │
│  Chunk 2: "## ? 运算符用法..."           │
│           (start: 500, end: 1200)        │
│                                         │
│  Chunk 3: "## 自定义错误类型..."          │
│           (start: 1200, end: 2000)       │
│                                         │
└─────────────────────────────────────────┘
```

**一对多关系**：一个 Page 包含多个 Chunk，每个 Chunk 持有对父 Page 的引用（`page_id`）。

### 污点追踪（Dirty Flag）

`is_dirty` 字段用于追踪哪些 Chunk 需要重新生成 embedding：

| 场景 | dirty 变化 | 说明 |
|------|-----------|------|
| 新建 Page | 新 Chunk 的 dirty=true | 需要立即嵌入 |
| 编辑 Page 内容 | 相关 Chunk 的 dirty=true | 下次 embed 命令处理 |
| 手动 `gbrain embed` | dirty 设为 false | 重新计算所有 embedding |
| 重命名 Page | 不影响 | slug 变化不影响 embedding |

这个机制确保：
- 只对实际变更的内容重新计算 embedding（节省 API 调用）
- 可以批量处理大量 dirty chunks

---

## 4.3 Link：知识图谱的边

### 边的类型

### Link 与 Page 的关系

```{mermaid}
erDiagram
    pages ||--o{ links : "from"
    pages ||--o{ links : "to"
```

| 链接类型 | 语法示例 | 说明 |
|---------|---------|------|
| Wikilink | `[[page-title]]` 或 `[[page-title\|显示文本]]` | 页面间链接 |
| Markdown 链接 | `[Text](path)` | 标准 Markdown 链接 |
| 时间线链接 | `<!-- timeline -->` 内条目 | 实体间时间关系 |
| Frontmatter 引用 | `people: [Alice, Bob]` | 结构化元数据中的引用 |

### 链接提取流程

```{mermaid}
flowchart LR
    A["Markdown 内容"] --> B["link-extraction.ts"]
    
    B --> C["Wikilink 正则"]
    B --> D["Markdown 链接正则"]
    B --> E["Frontmatter YAML 解析"]
    
    C --> F["Link 对象数组"]
    D --> F
    E --> F
    
    F --> G["addLinksBatch()"]
    G --> H["links 表"]
```

### Link 的数据结构

```typescript
interface Link {
  from_slug: string;      // 源页面 slug
  to_slug: string;        // 目标页面 slug
  link_type: string;      // 如 "references", "attended", "invested_in"
  context: string;        // 链接所在上下文（前后各20个字符）
  link_source: 'markdown' | 'frontmatter' | 'manual';
  origin_slug?: string;   // frontmatter 来源页面
  origin_field?: string;  // frontmatter 字段名
}
```

### 双向链接与 Backlinks

当页面 A 链接到页面 B 时：
- links 表中创建一条 `A → B` 的记录
- 可以通过 `getBacklinks(slug)` 查询所有指向某页面的链接

这构成了知识图谱的"双向通道"，支持图遍历查询。

---

## 4.4 Vector：嵌入向量

### 嵌入向量简介

**Vector（嵌入向量）** 是文本内容的数值表示，使得「语义相似性」可以通过数学计算（余弦相似度）来衡量。

### GBrain 的嵌入配置

GBrain 使用 OpenAI 的 `text-embedding-3-large` 模型：

| 配置项 | 值 |
|--------|-----|
| 模型 | `text-embedding-3-large` |
| 维度 | **1536 维** |
| 批量大小 | 100 条/请求 |
| 最大截断 | 8000 字符 |
| 重试策略 | 指数退避（4s base, 120s cap, 最多 5 次） |

### 向量存储

嵌入向量存储在 `content_chunks` 表的 `embedding` 列中：

```sql
-- 伪 SQL 表示
content_chunks.embedding pgvector(1536)
```

支持的向量操作：
```sql
-- 余弦相似度查询
SELECT id, content, 
       1 - (embedding <=> $1::vector) AS similarity
FROM content_chunks
WHERE page_id = $2
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

### 重要限制

> **⚠️ 自定义 Embedding 需要修改源码**
> 
> GBrain 硬编码了 `text-embedding-3-large`（1536 维向量）。如果需要使用其他嵌入模型（如本地模型、多模态模型），需要修改 `core/embedding.ts` 中的常量定义和相关的数据库 schema。

### 嵌入流程

```{mermaid}
flowchart TD
    A["Chunk 列表"] --> B["分批 (每批 100 条)"]
    B --> C["调用 OpenAI API"]
    C --> D{"请求成功?"}
    D -->|是| E["更新 embedding 列"]
    D -->|否| F{"达到重试上限?"}
    F -->|否| G["指数退避等待"]
    G --> C
    F -->|是| H["标记失败，记录日志"]
    E --> I["dirty = false"]
```

---

## 4.5 CodeEdge：Cathedral II 特有

### 代码调用图

**CodeEdge（代码边）** 是 Cathedral II 版本引入的，专门用于表示代码块之间的调用关系：

| 表 | 说明 |
|---|---|
| `code_edges_chunk` | 直接调用关系（from_chunk → to_chunk） |
| `code_edges_symbol` | 符号表（函数/类名 → 定义所在 Chunk） |

```{mermaid}
erDiagram
    content_chunks ||--o{ code_edges_chunk : "calls"
    code_edges_chunk }o--|| code_edges_symbol : "resolves"
    content_chunks ||--o{ code_edges_symbol : "defines"
```

### tree-sitter 解析

CodeEdge 通过 **tree-sitter** 解析代码，提取：

| 提取内容 | 说明 |
|---------|------|
| 函数定义 | `function foo() {}` |
| 函数调用 | `foo()` |
| 类定义 | `class Foo {}` |
| 导入语句 | `import { bar } from 'module'` |

### 两遍检索（Two-Pass Retrieval）

CodeEdge 支持 Cathedral II 的**两遍检索**（two-pass retrieval）：

```{mermaid}
flowchart TD
    A["查询: foo 函数的实现在哪里"]
    B["第一遍: 锚点搜索"]
    C["关键词/向量搜索找到 foo"]
    D["expandAnchors() 扩展"]
    E["通过 code_edges_chunk 找直接调用"]
    F["通过 code_edges_symbol 找符号引用"]
    G["第二遍: 结构邻居收集"]
    H["按跳数距离加权"]
    I["hydrateChunks() 补全元数据"]
    J["最终结果"]

    A --> B --> C --> D --> E --> G
    F --> G --> H --> I --> J
```

第一遍找到锚点（anchor），第二遍沿着调用图扩展，最终返回结构感知的检索结果。

---

## 4.6 数据库 Schema 概览

### 核心表关系

| 表 | 说明 |
|---|---|
| `pages` | 页面主表 |
| `content_chunks` | 页面分块 |
| `links` | 知识图谱边 |
| `code_edges_chunk` | 代码调用边 |
| `code_edges_symbol` | 符号表 |
| `timeline_entries` | 时间线条目 |
| `tags` / `page_tags` | 标签系统 |

```{mermaid}
erDiagram
    pages ||--o{ content_chunks : "1:N"
    pages ||--o{ links : "from"
    pages ||--o{ links : "to"
    pages ||--o{ timeline_entries : "1:N"
    content_chunks ||--o{ code_edges_chunk : "calls"
    content_chunks ||--o{ code_edges_symbol : "defines"
    code_edges_chunk }o--|| code_edges_symbol : "resolves"
    tags }o--o{ page_tags : "N:M"
    page_tags }o--|| pages : "N:M"
```

### 关键索引

| 表 | 索引类型 | 用途 |
|----|---------|------|
| `content_chunks` | `pgvector` (embedding) | 向量相似度搜索 |
| `content_chunks` | `gin` (frontmatter) | JSONB 字段查询 |
| `pages` | `gin` (slug gin_trgm_ops) | 模糊搜索 slug |
| `pages` | `btree` (updated_at) | 时间排序 |
| `links` | `btree` (from_page_id, to_page_id) | 图遍历 |
| `links` | `btree` (link_type) | 按类型过滤 |
| `code_edges_chunk` | `btree` (from_chunk_id) | 调用关系查询 |

### Schema 的内嵌设计

GBrain 的 SQL Schema 以字符串形式内嵌在代码中（`schema-embedded.ts` / `pglite-schema.ts`），而不是依赖外部文件：

```typescript
// 简化示例
const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS pages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  ...
);
CREATE EXTENSION IF NOT EXISTS vector;
...
`;
```

这样做的好处：
- **零依赖**：不需要读取外部 SQL 文件
- **版本化**：Schema 变更随代码版本管理
- **一致性**：部署时 Schema 与代码版本完全匹配

---

## 4.7 数据模型与检索的协作

### 写入流程

```{mermaid}
flowchart TD
    A["put_page Operation"]
    A --> B["parseMarkdown()"]
    B --> C["提取 frontmatter / compiled_truth / timeline"]
    C --> D["extractPageLinks()"]
    D --> E["Link 数组"]
    C --> F["chunkers 分块"]
    F --> G["Chunk 数组"]
    E --> H["engine.putPage()"]
    G --> H
    H --> I["pages 表 + content_chunks 表"]
    I --> J["embed() 生成向量"]
    J --> K["embedding 更新到 chunks 表"]
```

### 检索流程

```{mermaid}
flowchart LR
    A["hybridSearch()"]
    A --> B["searchKeyword()"]
    A --> C["searchVector()"]
    B --> D["RRF 融合"]
    C --> D
    D --> E["dedupResults()"]
    E --> F["applyBacklinkBoost()"]
    F --> G["SearchResult[]"]
```

---

## 4.8 小结

GBrain 的数据模型围绕「知识组织」这一核心需求设计：

| 实体 | 角色 | 关键设计 |
|------|------|---------|
| **Page** | 知识的基本单位 | slug 系统、Markdown 格式、remote 信任标记 |
| **Chunk** | 语义检索的粒度 | 多种分块策略、dirty 追踪、token 计数 |
| **Link** | 知识图谱的边 | 多种链接类型、自动提取、双向 backlinks |
| **Vector** | 语义相似性 | 1536 维嵌入、pgvector 存储 |
| **CodeEdge** | 代码调用关系 | tree-sitter 解析、两遍检索 |

这些实体共同构成了 GBrain 的知识表示层，支撑起从简单笔记到 AI 增强检索的完整能力。

---

*下一章我们将探讨 GBrain 的搜索系统，了解混合搜索（Hybrid Search）如何融合关键词搜索和向量搜索，提供精准的检索结果。*
