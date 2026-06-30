# Research Dashboard

Last updated: 2026-06-30

This is the working entry point for the thesis research workspace. Start here before opening experiment files, paper drafts, or meeting notes.

## Current Thesis Line

Topic direction:

> 面向教育资源检索的可信多模态知识推理研究

Core line:

> 教育知识结构约束跨模态对齐 + MNAR-aware 选择性补全 + 路径/对齐/可靠性约束解释生成。

Canonical planning files:

- [论文重构_最终主线与实施方案.md](../论文重构_最终主线与实施方案.md)
- [研究重构_文献综述与技术路线.md](../研究重构_文献综述与技术路线.md)
- [PAPER_OUTLINE_REVISED.md](../PAPER_OUTLINE_REVISED.md)

## Active Workstreams

| Workstream | Status | Next action |
| --- | --- | --- |
| RC2 missingness diagnosis | Exp0.2 first baseline complete | Add grouped stress test before thesis use |
| RC1 concept-aware retrieval | Planned | Define baselines and first runnable retrieval experiment |
| RC3 explanation generation | Planned | Build 100-sample explanation evaluation set after RC1/RC2 inputs are stable |
| Literature review | In progress | Expand to 30-40 papers, 10-12 per research content |
| Group meetings | Needs structure | Use the two-week meeting cycle and PPT templates |

## Core Indexes

- [Task board](task-board.md)
- [Experiment registry](experiment-registry.md)
- [Paper roadmap](paper-roadmap.md)
- [Meeting cycle](meeting-cycle.md)
- [Research space map](research-space-map.md)
- [Multi-device sync](multi-device-sync.md)

## Session Routine

1. Run `scripts/sync_start.ps1` or `scripts/sync_start.sh`.
2. Check [Task board](task-board.md).
3. Work on one active task only.
4. Record experiment commands, outputs, and interpretation.
5. Run `scripts/sync_finish.ps1` or `scripts/sync_finish.sh` before switching devices.

## Evidence Rules

- Claims about RC2 must cite Exp0/Exp0.1 outputs.
- Claims about RC1 must cite retrieval metrics and baseline comparisons.
- Claims about RC3 must cite explanation samples, path evidence, and evaluator results.
- Draft thesis prose should distinguish proven results from working assumptions.

## Current RC2 Decision

Exp0.1 currently supports a selective-completion framing:

- Most missing-image samples in the candidate set are labeled `structural_absence`.
- Manual review indicates the previous `ambiguous` rows are image-needed missing samples.
- The missing-image candidate set now has 230 `structural_absence` rows and 92 `accidental_missing` rows.
- Exp0.2 shows the binary gate is feasible on the original split.
- The next check should hold out topic or skill groups to test whether the gate generalizes beyond seen categories.
