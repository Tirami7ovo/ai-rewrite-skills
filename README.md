# AI Rewrite Skills

一套用于 AI 协同重写的通用技能：从旧系统提取有证据的规格，依据规格重新实现，再对行为差异、交付条件和实际运行结果进行验证。

五个技能可以**分别安装、独立调用、按需组合**。它们接受项目已有的文档、代码、测试和运行记录，不要求从第一步开始，也不绑定语言、系统架构、模型厂商或测试框架。

## 选择技能

| 当前需要 | 技能 | 主要产出 |
| --- | --- | --- |
| 把旧系统整理成可用于重写的需求依据 | [legacy-spec-distillation](skills/legacy-spec-distillation/SKILL.md) | PRD、功能清单、外部接口约定、状态与恢复规则、功能到 E2E 对应表 |
| 根据已经确认的规格实现新版本 | [spec-driven-rewrite](skills/spec-driven-rewrite/SKILL.md) | 新实现、规格映射、验证结果与未决范围 |
| 检查新旧行为和重写结果的质量 | [rewrite-parity-audit](skills/rewrite-parity-audit/SKILL.md) | 行为差异报告、缺陷/安全报告、修复复审结论 |
| 判断候选版本能否交付或切换 | [rewrite-release-validation](skills/rewrite-release-validation/SKILL.md) | 验收证据、发布判断、适用的彩排与回退记录 |
| 处理上线后的回归和性能问题 | [rewrite-stabilization](skills/rewrite-stabilization/SKILL.md) | 问题处置、回归验证、可比较的性能证据与观察结论 |

一种组合方式是：规格蒸馏 → 依据规格重写 → 独立审计 → 修复及复审 → 发布验证 → 上线稳定。已有合格规格、代码或报告时，可直接选用相应技能。

## 贯穿整个流程的约定

每条结论关联来源及版本；证据不足写明“待确认”。模型置信度、多个模型意见一致，以及看起来合理的推测，都不能代替证据。

| 行为标记 | 含义 | 验收依据 |
| --- | --- | --- |
| 确认保留 | 已确定必须保留的业务规则和兼容要求 | 原有已确认行为与约束 |
| 确认调整 | 已认可要修正的缺陷或要改变的行为 | 单独记录的目标行为和新验收标准 |
| 尚待确认 | 材料冲突、历史逻辑无法解释或目标依据不足 | 保留缺口，只暂停依赖它的实现与验收 |

功能与 E2E 建立对应关系、用例覆盖了某条规则、测试在某版本上执行通过，是不同的事实。重写保留测试中的业务知识；测试代码可以适配，验收含义不能为了通过而被悄悄放宽。

## 安装

先克隆仓库，再将需要的完整技能目录复制到所用工具的技能目录。每个技能目录包含自己的入口、模板与元数据，不需要安装同仓库的其他技能。

```sh
git clone https://github.com/Tirami7ovo/ai-rewrite-skills.git
```

Codex 默认个人技能目录为 `~/.codex/skills`；设置了 `CODEX_HOME` 时使用该目录下的 `skills`。例如在 Linux/macOS 的 shell 中安装蒸馏技能：

```sh
skill_dir="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skill_dir"
cp -R ai-rewrite-skills/skills/legacy-spec-distillation "$skill_dir/"
```

Windows PowerShell 示例：

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex\skills' }
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
Copy-Item -Recurse -LiteralPath '.\ai-rewrite-skills\skills\legacy-spec-distillation' -Destination $skillRoot
```

如目标目录已经存在同名技能，先比较本地修改再更新。要安装其他技能，将示例中的目录名替换为上表中的名称即可。

其他支持 `SKILL.md` 的工具可使用相同技能目录，并遵循该工具自己的技能安装位置。`agents/openai.yaml` 是 Codex 的可选界面元数据，不是方法论运行依赖。是否支持自动触发或子代理，由具体运行环境决定。

## 调用示例

```text
使用 $legacy-spec-distillation，从提供的协议、旧代码、测试和运行记录中整理重写交接包。
每条结论注明证据和版本，区分确认保留、确认调整和尚待确认。
```

```text
使用 $spec-driven-rewrite，按已有 PRD 和验收用例重写指定模块。
沿用已批准的行为变更；待确认项只阻塞相关范围。
```

```text
使用 $rewrite-parity-audit，对照旧版本、批准的行为变更和候选版本进行只读审计。
分别报告行为差异、缺陷与安全问题，并标明证据等级。
```

```text
使用 $rewrite-release-validation，依据现有测试和运行证据判断候选版本是否可发布。
本次只做验证和发布判断；生产操作以已经给出的授权范围为准。
```

```text
使用 $rewrite-stabilization，分析新版本的回归与性能变化。
给出可比较的基线、当前证据和有边界的处理方案。
```

## 资料

- [方法来源及原十二步的映射](docs/methodology.md)
- [设计说明](docs/design.md)
- [验证记录与适用边界](docs/validation.md)

本仓库把实践经验整理为工作指导。适用范围、验证结果和未解决问题需要在具体项目中记录，技能本身不证明某次重写已经正确或适合上线。
