# 附录 C：鸣谢与参考资料（Credits）

## C.1 项目信息

| 项目 | 信息 |
|------|------|
| **项目名称** | GBrain |
| **GitHub** | https://github.com/garrytan/gbrain |
| **当前版本** | v0.22.5 |
| **License** | MIT |
| **描述** | Postgres-native personal knowledge brain with hybrid RAG search |

GBrain 是一个开源的个人知识大脑项目，采用本地优先（local-first）设计，数据存储在本地 Markdown 文件中，通过 Git 进行版本控制。

---

## C.2 主要贡献者

| 贡献者 | 角色 | 备注 |
|--------|------|------|
| **Garry Tan** (garrytan) | 项目创始人 | 主要作者和维护者 |
| **GBrain 社区贡献者** | 代码贡献 | 通过 GitHub Issues 和 PR 参与 |

---

## C.3 技术依赖

GBrain 的核心依赖：

| 依赖 | 版本 | 用途 |
|------|------|------|
| `@electric-sql/pglite` | 0.4.3 | 嵌入式 PostgreSQL（WASM） |
| `pgvector` | 0.2.0 | 向量存储和相似度搜索 |
| `@modelcontextprotocol/sdk` | 1.0.0 | MCP 协议实现 |
| `openai` | 4.0.0+ | Embedding 生成 |
| `tree-sitter-wasms` | 0.1.13 | 代码解析 |
| `marked` | 18.0.0 | Markdown 解析 |

---

## C.4 参考资料与延伸阅读

### 核心文档

- [CLAUDE.md](https://github.com/garrytan/gbrain/blob/main/CLAUDE.md) — 项目架构参考，源码阅读指南
- [INSTALL_FOR_AGENTS.md](https://github.com/garrytan/gbrain/blob/main/INSTALL_FOR_AGENTS.md) — AI Agent 安装指南
- [ARCHITECTURE_ANALYSIS.md](https://github.com/garrytan/gbrain/blob/main/ARCHITECTURE_ANALYSIS.md) — 架构深度分析

### 技术主题

| 主题 | 参考资料 |
|------|---------|
| **RAG** | LangChain 文档，Pinecone Blog |
| **Vector Search** | pgvector 官方文档 |
| **MCP** | Anthropic MCP 官方文档 |
| **BullMQ** | BullMQ GitHub（Minions 设计参考） |
| **Reciprocal Rank Fusion** | `10.1145/1645953.1646033`（原始论文） |

---

## C.5 本书写作说明

### 目标读者

本书面向**个人开发者**，特别是希望构建个人知识管理系统的工程师。需要具备：
- TypeScript 基础
- 基本的数据库概念（SQL、PostgreSQL）
- 对 AI/LLM 应用有基本了解

### 写作风格

- **技术博客风格**：直入主题，不讲废话
- **首次出现的术语附英文**：帮助读者阅读英文文档
- **不讲安装/CLI用法**：聚焦内部设计和实现原理

### 源码阅读建议

```
推荐阅读顺序：
1. cli.ts — 理解命令分发到 Operation 的流程
2. operations.ts — 理解 Operation 的注册和执行机制
3. engine.ts — 理解 BrainEngine 的接口设计
4. pglite-engine.ts — 理解嵌入式存储实现
5. search/hybrid.ts — 理解混合搜索管线
6. search/two-pass.ts — 理解 Cathedral II 实现
```

### 文档更新

本书随 GBrain 版本迭代更新。当前基于 **v0.22.5**。

---

## C.6 反馈与勘误

- 发现错误请提交 GitHub Issue
- 文档源码：https://github.com/garrytan/gbrain-book

---

*GBrain v0.22.5 · 附录 C · 本书由 GBrain 社区编写*
