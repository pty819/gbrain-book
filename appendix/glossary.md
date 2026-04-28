# 附录 B：术语表（Glossary）

> 按字母顺序排列。首次出现的术语附英文原文。

## A

- **Agent Memory**：Agent 记忆问题。LLM 每次对话是独立上下文窗口，训练数据不会出现在推理时，需要外部机制持久化记忆。

- **Async（异步）**：不阻塞主线程的执行模式。GBrain 的 Minions 后台作业、Resolver 外部调用都使用异步模式，避免慢操作卡住主流程。


## B

- **Backlink**：反向链接。在 GBrain 中，`links` 表存储从 A 页面到 B 页面的链接，`backlink` 指所有指向当前页面的链接，用于构建知识图谱。

- **BM25**：Best Matching 25，一种经典的信息检索算法，基于词频和文档长度归一化计算相关性评分。GBrain 的关键词搜索层使用 `pg_trgm` 实现类似 BM25 的效果。


## C

- **Cathedral II**：GBrain v0.20.0 引入的两遍结构化检索机制。详见第十一章。

- **Chunk / Chunking**：知识切分。将长文档或大页面拆分成适合检索的小块（Chunk）。GBrain 使用基于 token 计数的动态切分策略，保留必要的上下文边界。

- **Claude Code**：Anthropic 官方 CLI 工具，GBrain 的主要客户端之一。MCP 协议让 Claude Code 可以直接调用 GBrain 的工具操作。

- **Confidence**：置信度。Resolver 返回结果时附带 0.0-1.0 的置信度评分。直接 API 响应 confidence = 1.0，LLM 推断的结果 confidence < 1.0。


## E

- **Embedding / 向量化**：将文本转换为高维向量（1536 维）的过程。GBrain 使用 OpenAI `text-embedding-3-large` 模型，向量存储在 `content_chunks.embedding` 列中。


## H

- **Hybrid Search**：混合搜索。GBrain 结合向量搜索（语义相似性）和关键词搜索（精确匹配）两种检索方式，用 **RRF（Reciprocal Rank Fusion）** 融合结果。


## L

- **Link / Backlink**：页面间的引用关系。Wikilink 格式如 `[[page-slug]]` 在 GBrain 中被解析为 `links` 表记录，用于构建双向知识图谱。


## M

- **MCP (Model Context Protocol)**：模型上下文协议。一个标准化的协议，让 AI 模型（如 Claude）可以通过统一接口调用外部工具。GBrain 作为 MCP Provider 暴露操作。详见第十一章。

- **Mermaid**：图表格式。GBrain 的文档使用 Mermaid 语法绘制流程图、架构图。在本书中指图表格式，不是 GBrain 特性。

- **Minion**：后台作业系统。GBrain 的 BullMQ-inspired 任务队列，使用 PGLite 本身存储任务状态，不依赖外部队列服务。详见第十一章。


## O

- **Operation Registry**：操作注册表。GBrain 的所有操作（`put_page`、`search` 等）在 `operations.ts` 中注册，CLI 和 MCP 共用同一套操作定义。


## P

- **pg_trgm**：PostgreSQL 的三字母组（Trigram）扩展。支持基于字符串相似度的搜索，用于处理拼写错误和部分匹配。GBrain 的关键词搜索层使用 `pg_trgm` 实现模糊匹配。

- **PGLite**：@electric-sql/pglite，基于 WebAssembly 的嵌入式 PostgreSQL。GBrain 默认使用 PGLite 作为存储引擎，实现零配置的本地持久化。

- **Postgres + pgvector**：完整版 PostgreSQL 配合 pgvector 扩展。适合 1000+ 页面或多人同步的生产级部署，需要 Supabase 或自建 Postgres 实例。


## R

- **RAG (Retrieval Augmented Generation)**：检索增强生成。结合检索系统和 LLM 的生成能力。GBrain 是一个 RAG 系统，但特别强调代码结构感知（通过 Cathedral II）。

- **Reciprocal Rank Fusion (RRF)**：倒数排名融合。将多个排序结果合并成一个统一排名的算法。GBrain 的混合搜索用它融合向量搜索和关键词搜索的结果。

```
RRF_score(d) = Σ 1/(k + rank_i(d))
k = 60（常数）
rank_i(d) = 文档 d 在第 i 个结果列表中的排名
```

- **Resolver**：解析器模块。从外部数据源（GitHub、X、Notion 等）获取信息的组件。详见第十一章。


## S

- **Semantic Search**：语义搜索。基于向量相似度而非关键词匹配的搜索方式。能理解「如何认证用户」和「authentication method」的语义关联。

- **Skill / SkillPack**：技能单元。GBrain 的可扩展模块，包含提示词、工具定义和执行步骤。一个 Skill 相当于给 LLM 装了一个「插件」。详见第九章。


## T

- **Token**：文本处理的最小单位。GBrain 的 Chunk 大小以 token 数量计量，向量化模型（`text-embedding-3-large`）支持最多 8000 token 的输入。

- **Trigram / pg_trgm**：三字母组匹配。PostgreSQL 扩展 `pg_trgm` 将字符串切分成连续的三字母组，用于模糊字符串搜索。


## V

- **Vector Search**：向量搜索。在高维向量空间中寻找与查询向量最接近的 k 个 Chunk。GBrain 使用 cosine similarity 度量相似性，结果存入 `content_chunks.embedding` 列。


## W

- **Wikilink**：双链笔记格式。`[[page-slug]]` 格式的链接，GBrain 解析后存入 `links` 表。Wikilink 支持别名：`[[page-slug|显示文本]]`。


## 符号

- **`$1, $2`**：参数占位符。GBrain 所有 SQL 查询使用参数化查询，`$1` 等是占位符，由数据库驱动负责参数绑定和转义，防止 SQL 注入。


*GBrain v0.22.5 · 附录 B*
