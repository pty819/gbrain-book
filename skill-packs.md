# 第十章：SkillPack 机制——Skill 的打包、分发与安装标准

## 10.1 什么是 SkillPack

Skill 是单个可执行单元，SkillPack 则是**多个 Skill 的集合 + 元数据**，是 GBrain 的 Skill 分发格式。

把 Skill 和 SkillPack 的关系类比为 npm package 和 registry：单个 Skill 像一个 npm package，而 SkillPack 像一个包含多个相关 package 的 bundle。一个 SkillPack 可以包含十几个互相依赖的 Skill，以及它们共用的模板、规则和配置文件。

GBrain 的出厂 Skill 以 SkillPack 形式发布，定义在仓库根目录的 `openclaw.plugin.json` 中：

```json
{
  "name": "gbrain",
  "version": "0.19.0",
  "skills": [
    "skills/brain-ops",
    "skills/briefing",
    "skills/idea-ingest",
    "skills/meeting-ingestion",
    "skills/query",
    "skills/signal-detector",
    ...
  ],
  "shared_deps": [
    "skills/conventions",
    "skills/_brain-filing-rules.md",
    "skills/_brain-filing-rules.json",
    "skills/_output-rules.md"
  ],
  "excluded_from_install": [
    "skills/setup",
    "skills/migrate",
    "skills/publish"
  ]
}
```

这个 JSON 本身就是 SkillPack 的 manifest——它定义了哪些 Skill 需要安装，哪些是共享依赖（所有 Skill 都需要的公共资源），以及哪些是安装时排除的内部 Skill。

## 10.2 SkillPack 的结构

一个完整的 SkillPack 有以下目录结构：

```
skillpack-name/
├── manifest.json          # SkillPack 元数据（版本、描述、依赖）
├── skills/                 # Skill 集合
│   ├── skill-a/
│   │   └── SKILL.md
│   ├── skill-b/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── skill-b.mjs
│   └── shared-scripts/     # Skill 间共享的代码
├── conventions/            # 通用规范（back-link 规则等）
├── _brain-filing-rules.md  # 归档决策协议
└── _output-rules.md       # 输出格式规范
```

manifest 文件是 SkillPack 的入口。GBrain 在安装时会解析 manifest，确定需要安装哪些 Skill 以及它们之间的依赖关系。

**共享资源（shared_deps）** 是 SkillPack 设计中一个关键概念。多个 Skill 共同依赖 `_brain-filing-rules.md` 中的归档协议和 `conventions/` 中的质量规范。这些共享资源集中管理，避免每个 Skill 都自己维护一份副本，从而保证行为一致性。当一个 Skill 需要归档一个新页面时，它不是自己想当然，而是查 `skills/_brain-filing-rules.md` 中的决策树，确保和所有其他 Skill 使用完全相同的归档逻辑。

**excluded_from_install** 字段则处理一种特殊场景：某些 Skill（如 `setup`、`migrate`、`publish`）是 GBrain 内部管理用的，不应该被安装到 agent 工作区。通过 manifest 声明排除，比在每个 Skill 里单独标记「这不是给外部用的」更清晰。

## 10.3 Skillify：代码生成 Skill

Skillify 是 GBrain 的 Skill 生成引擎——输入一段自然语言描述，输出一个可执行的 Skill 代码框架。

Skillify 的核心入口是 `src/core/skillify/generator.ts` 中的 `planScaffold()` 函数。这个函数接收：

- `name`：Skill 名称（必须 kebab-case）
- `description`：一句话描述
- `triggers`：触发短语列表
- `writesPages` / `mutating`：行为标记

然后生成以下文件：

| 文件 | 用途 |
|------|------|
| `skills/<name>/SKILL.md` | Skill 定义文件（YAML frontmatter + 行为规范） |
| `skills/<name>/scripts/<name>.mjs` | 可执行的脚本文件 |
| `skills/<name>/routing-eval.jsonl` | 路由测试数据 |
| `test/<name>.test.ts` | 单元测试文件 |

生成的 SKILL.md 是一个包含 `SKILLIFY_STUB` 占位符的模板：

```yaml
---
name: new-skill
version: 0.1.0
description: ...
triggers:
  - "TBD-trigger — replace with phrases users actually type"
---

# new-skill

<!-- SKILLIFY_STUB: replace before running check-resolvable --strict -->

## The rule

Replace this stub with the hard rule that prevents recurrence of
the failure that triggered this skill.

## How to use

Run the deterministic script: `bun scripts/<name>.mjs`
```

**设计哲学**是让 Skill 创建的门槛降到最低。非程序员可以用自然语言描述「这个 Skill 要做什么」，系统自动生成符合规范的代码框架。同时，`SKILLIFY_STUB` 占位符机制确保每个生成的 Skill 都有明确的实现标记——`gbrain check-resolvable --strict` 会扫描所有 Skill，当发现任何 Skill 仍包含 `SKILLIFY_STUB` 标记时会报错，确保没有 Skill 以未实现状态进入生产环境。

生成脚本文件时也携带 `SKILLIFY_STUB` 注释，测试文件则提供基础的测试框架。这种「生成→验证→强制实现」的流程，比让开发者自己搭建完整的 Skill 骨架要高效得多。

## 10.4 Skill 的安装和更新

SkillPack 的安装流程如下：

```{mermaid}
flowchart TD
    A["gbrain skillpack install<br/>&lt;pack-name&gt;"] --> B["解析 openclaw.plugin.json<br/>或远程 manifest"]
    B --> C["加载 Skill 列表 + shared_deps"]
    C --> D["创建 skills/ 目录结构"]
    D --> E["安装每个 Skill 的 SKILL.md"]
    E --> F{"shared_deps 存在?"}
    F -->|"是"| G["复制共享资源到本地"]
    F -->|"否"| H["下载缺失的共享资源"]
    G --> H
    H --> I["更新 manifest.json 记录已安装版本"]
    I --> J["运行 check-resolvable<br/>验证可达性"]
    J --> K{"check-resolvable 通过?"}
    K -->|"失败"| L["报告冲突/重复/孤立问题"]
    K -->|"通过"| M["Skill 安装完成"]
    
    style L fill:#ffcccc
    style M fill:#ccffcc
```

版本管理采用 **Semantic Versioning（语义化版本）**。当 Skill 作者发布新版本时：

1. 安装时检测本地版本和远程版本
2. 如果远程版本 > 本地版本，提示用户可以更新
3. 更新过程保留旧版本备份，支持回滚
4. `excluded_from_install` 中的 Skill 永远不会被自动更新

更新检测逻辑和 npm 类似：解析 manifest 中的 `version` 字段，比较本地已安装版本和 registry 中的最新版本。当 `version` 从 `1.0.0` 变为 `1.1.0` 时是 minor update（向后兼容），从 `1.0.0` 变为 `2.0.0` 时是 major update（可能破坏兼容性）。

## 10.5 Skill 生态

GBrain 的 Skill 生态分为三层：内置（Built-in）、社区（Community）、企业（Enterprise）。

**内置 Skill** 是 GBrain 出厂自带的 Skill，定义在 `openclaw.plugin.json` 的 `skills` 字段中。这些 Skill 经过严格测试，覆盖了 brain 的完整工作流程：

| Skill | 职责 |
|-------|------|
| `brain-ops` | Brain 的核心操作（put_page、get_page、sync 等） |
| `query` | 自然语言查询与答案合成 |
| `idea-ingest` | 链接、文章、推文摄入 |
| `meeting-ingestion` | 会议记录全链路处理 |
| `media-ingest` | 多模态内容摄入 |
| `signal-detector` | Ambient 想法与实体捕获 |
| `skillify` | Skill 的代码生成 |
| `skill-creator` | Skill 的创建工作流 |
| `repo-architecture` | 归档决策协议 |
| `enrich` | 实体信息自动丰富 |

**社区 Skill** 是开放给社区开发和分享的 Skill。通过 GitHub 或 npm 分发，任何人都可以创建 Skill 并发布。社区 Skill 需要通过 `gbrain check-resolvable` 验证，确保不与内置 Skill 冲突、不产生孤立路由。MECE 检查会扫描所有已注册 Skill 的触发短语，确保没有重叠覆盖。

**企业私有 Skill** 是企业内部知识库封装的 Skill。企业可以将内部流程、特定领域知识、私有数据处理逻辑封装为 Skill，通过 SkillPack 的私有 registry 分发。私有 Skill 享受和内置 Skill 同等的保护——不会被意外覆盖，拥有独立的版本控制流程。

Skill 的可扩展性是 GBrain 区别于传统知识管理系统的核心差异。传统系统的功能是固定的，用户只能在预设功能内工作；而 GBrain 的 Skill 系统让任何人都可以创建新的能力单元，通过 SkillPack 分发给其他用户。这意味着 GBrain 不是一个功能有限的工具，而是一个可以无限扩展的能力平台。