# 第六章：知识图谱（Knowledge Graph）

> 纯向量搜索告诉你「A 和 B 相似」，但 Link 告诉你「A 引用了 B」。这种关系在代码理解、笔记关联、实体关系推理中至关重要。

---

## 6.1 为什么需要知识图谱

### 纯向量搜索的局限性

向量搜索（Embedding + Cosine Similarity）擅长找到**语义相似**的内容，但它丢失了原始文本中的关系信息。

举例：当你查询「Alice Chen 工作过的公司」时，纯向量搜索只能找到语义上与这个查询相似的文本块——但无法区分「Alice 创立了公司」和「Alice 投资了公司」。两种关系截然不同，但在向量空间中可能距离很近。

### Link 的本质

Link（链接）是 GBrain 知识图谱的**边（Edge）**。它表达的不是「相似」，而是「引用」或「关联」：

```markdown
[[people/alice-chen]] 在 [[companies/gamma-ai]] 担任 CTO。
```

这条文本解析后生成一条 Link：`people/alice-chen` → `companies/gamma-ai`，关系类型为 `works_at`。

当你查询「Alice 的公司」时，GBrain 可以沿着 Link 遍历图，而不是靠向量相似度猜测。

### 知识图谱在代码理解中的价值

在 **Cathedral II** 版本中，GBrain 进一步将知识图谱扩展到代码领域：

- **代码调用边**（`code_edges_chunk` / `code_edges_symbol`）：函数 A 调用了函数 B
- **两遍检索**（Two-Pass Retrieval）：先通过关键词/向量找到锚点（anchor），再通过代码边扩展到结构邻居

这使得「查找某个函数的所有调用者」这类查询成为可能——这是纯向量搜索根本无法回答的问题。

---

## 6.2 Link 的类型系统

GBrain 的 Link 有以下类型：

### 链接类型

| link_type | 含义 | 典型场景 |
|-----------|------|----------|
| `founded` | 创始人关系 | Person → Company |
| `invested_in` | 投资关系 | Person → Company |
| `advises` | 顾问关系 | Person → Company |
| `works_at` | 雇佣关系 | Person → Company |
| `attended` | 参与关系 | Person → Meeting |
| `mentions` | 提及关系 | Media / Concept → Person |
| `references` | 引用关系 | Article → Concept |

### 链接来源

| link_source | 说明 |
|--------------|------|
| `markdown` | 从正文中的 `[[wikilink]]` 或 `[text](path)` 自动提取 |
| `frontmatter` | 从 YAML 元数据字段（如 `investors: [fund-a]`）提取 |
| `manual` | 用户通过 `add_link` API 手动创建 |

### 特殊链接类型

**Wikilinks**：`[[page-title]]` 或 `[[page-title|显示文本]]` — Obsidian 风格的内部链接语法。

**Qualified Wikilinks**：`[[source-id:path]]` — 带数据源限定的链接，用于多数据源场景（v0.17+）。

**代码链接**：Cathedral II 特有，通过 `code_edges_chunk` 和 `code_edges_symbol` 表存储函数调用关系。

---

## 6.3 Link 的自动提取

### 核心函数：`extractPageLinks()`

`link-extraction.ts` 中的 `extractPageLinks()` 是 Link 提取的核心。这是一个**纯函数**，输入页面内容，输出链接候选：

```typescript
export async function extractPageLinks(
  slug: string,          // 当前页面 slug
  content: string,        // Markdown 正文
  frontmatter: Record<string, unknown>,  // YAML 元数据
  pageType: PageType,     // 页面类型（person/company/meeting...）
  resolver: SlugResolver, // slug 解析器（可能是 DB 查询）
): Promise<PageLinksResult>
```

### 正则 vs AST 解析

有人会问：为什么不直接用正则提取 `[[wikilink]]`？

因为正则无法处理以下边界情况：

1. **嵌套结构**：`[[outer [[inner]] text]]` — 内层 wikilink 不能被当作外层的一部分
2. **转义字符**：`[[title with \] bracket]]` — 右括号被转义，不是真实边界
3. **代码块内的 slug**：`const link = "[[people/alice-chen]]"` — 代码中的 wikilink 不应被提取
4. **Qualified 前缀**：`[[twitter:people/alice-chen]]` — 需要先于普通 wikilink 处理

GBrain 的策略是**正则 + 掩码（masking）**：

```typescript
// 1. 先提取 qualified wikilinks，标记其范围
const qualifiedRanges: Array<[number, number]> = [];
while ((match = qualPattern.exec(stripped)) !== null) {
  qualifiedRanges.push([match.index, match.index + match[0].length]);
}

// 2. 用空格替换已匹配范围，防止二次匹配
const unmasked = maskRanges(stripped, qualifiedRanges);

// 3. 在掩码后的文本上执行普通 wikilink 正则
while ((match = wikiPattern.exec(unmasked)) !== null) { ... }
```

### 具体算法：识别 `[[title]]` 并映射到 page id

```{mermaid}
flowchart LR
    A["原始文本"] --> B[stripCodeBlocks<br/>移除代码块]
    B --> C["Qualified Wikilink 正则"]
    C --> D{匹配成功?}
    D -->|是| E["记录范围<br/>sourceId = match[1]"]
    D -->|否| F["掩码该范围"]
    F --> G["普通 Wikilink 正则"]
    G --> H{"匹配成功?"}
    H -->|是| I["slug = match[1]<br/>sourceId = null"]
    H -->|否| J["继续"]
    E --> K["返回 EntityRef[]"]
    I --> K
```

**提取后的 EntityRef 包含：**

```typescript
interface EntityRef {
  name: string;      // 显示名称
  slug: string;      // 页面 slug（如 "people/alice-chen"）
  dir: string;       // 顶级目录（如 "people"）
  sourceId?: string; // qualified wikilink 时有值
}
```

---

## 6.4 图查询 API

`BrainEngine` 接口提供了一组图查询方法：

### 获取出链：`getLinks(pageId)`

获取某页面的所有**出链**（outgoing edges）——该页面引用的其他页面。

```typescript
getLinks(pageId: number): Promise<Link[]>
```

### 获取入链：`getBacklinks(pageId)`

获取某页面的所有**入链**（incoming edges）——引用了该页面的其他页面。这回答了「谁引用了我」这个问题：

```typescript
getBacklinks(pageId: number): Promise<Link[]>
```

### 图遍历：`traverseGraph()`

从某个节点出发，按指定深度遍历图：

```typescript
traverseGraph(
  startSlug: string,
  depth: number,       // 最大深度
  direction: 'out' | 'in' | 'both',
): Promise<GraphNode[]>
```

### 寻找孤立页面：`findOrphanPages()`

找出没有被任何页面引用的孤立页面：

```typescript
findOrphanPages(): Promise<string[]>
```

这对于知识管理很有用——孤立页面可能是过时内容，或者需要建立关联。

### 示例：知识图谱查询

```{mermaid}
graph TB
    P1["people/alice-chen<br/>Person"]
    C1["companies/gamma-ai<br/>Company"]
    C2["companies/beta-vc<br/>Company"]
    M1["meetings/ai-forum-2025<br/>Meeting"]

    P1 -->|"works_at"| C1
    P1 -->|"invested_in"| C2
    P1 -->|"attended"| M1
    C1 -->|"founded"| P1
    C2 -->|"invested_in"| C1

    P1 -->|getLinks| OUT["返回: works_at→gamma-ai<br/>invested_in→beta-vc<br/>attended→ai-forum-2025"]
    C1 -->|getBacklinks| IN["返回: alice-chen works_at<br/>beta-vc invested_in"]
```

---

## 6.5 链接修复（Backlinks Fix）

### 断链的成因

当通过 Git 操作笔记时（删除页面、重命名 slug），数据库中的链接可能失效：

```
git mv people/alice-chen.md people/alice-chen-old.md
# 数据库中指向 people/alice-chen 的链接全部失效
```

### 检测断链：`gbrain backlinks check`

扫描所有 Links，验证每条链接的目标页面是否存在：

```{mermaid}
flowchart TD
    A["gbrain backlinks check"] --> B[遍历 links 表]
    B --> C{目标 slug 存在?}
    C -->|是| D["继续"]
    C -->|否| E["记录断链<br/>from_slug → to_slug"]
    D --> F{还有更多链接?}
    D -->|否| G[输出断链报告]
    E --> F
```

### 自动修复：`gbrain backlinks fix`

修复策略有两种：

1. **重命名**：如果目标页面被重命名，更新链接指向新 slug
2. **删除**：如果目标页面已删除，删除该链接

```{mermaid}
flowchart TD
    A["gbrain backlinks fix"] --> B{目标 slug 存在?}
    B -->|存在| C["保持链接"]
    B -->|不存在| D{"同名重命名<br/>在 git history 中?"}
    D -->|是| E["更新 to_slug<br/>指向新位置"]
    D -->|否| F["删除该链接"]
    C --> G[输出修复报告]
    E --> G
    F --> G
```

修复在事务中执行，失败时自动回滚，确保数据一致性。

---

## 本章小结

知识图谱是 GBrain 区别于纯向量笔记系统的核心差异：

1. **Link 表达关系**：不是「相似」而是「引用」，保留了原始文本中的语义关系
2. **自动提取**：`link-extraction.ts` 的纯函数设计，从 Markdown 和 frontmatter 中自动发现链接
3. **关系推断**：根据上下文动词自动分类（founded/invested_in/works_at/...）
4. **图查询 API**：支持出链、入链、图遍历、孤立页面检测
5. **断链修复**：Git 操作后自动检测并修复失效链接

在 Cathedral II 中，知识图谱进一步延伸到代码领域——函数调用关系构成了代码理解的基础，使「查找函数调用者」这类查询成为可能。
