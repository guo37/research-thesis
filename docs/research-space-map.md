# Research Space Map

Use this repository as the executable research workspace. Use Obsidian or external notes as the higher-level knowledge index, but keep runnable code, experiment configs, generated reports, and current thesis planning here.

## Three Research Areas

### 1. Experiments

Purpose: make every experiment reproducible across Windows home, Windows work, and Mac.

Current folders:

- `configs/`: parameter files for experiment scripts.
- `scripts/`: executable research scripts.
- `tests/`: fixtures and sanity checks.
- `data/scienceqa/processed/`: processed tables worth syncing for current analysis.
- `data/scienceqa/annotation/`: annotation candidate sets and batch files.
- `reports/`: generated experiment reports and interpretation.

Rules:

- Keep `data/**/cache/` local only.
- Keep raw or downloaded datasets out of Git unless they are tiny fixtures.
- For each new major experiment, create `configs/expN_*.yaml`, `reports/expN_*`, and a short run note.
- Put small stable fixtures in `tests/fixtures/`.

### 2. Thesis And Paper Writing

Purpose: maintain the research line and thesis deliverables.

Current files:

- `PAPER_OUTLINE_REVISED.md`
- `论文重构_最终主线与实施方案.md`
- `研究重构_文献综述与技术路线.md`

Recommended next folders when the writing volume grows:

```text
paper/
  proposal/
  midterm/
  thesis/
  literature/
  review/
```

Rules:

- Keep the latest thesis line in one canonical outline file.
- Keep literature notes linked to Zotero citation keys.
- Use generated reports as evidence, not as final thesis prose.

### 3. Group Meetings

Purpose: produce a repeatable two-week research update.

Recommended folder:

```text
meetings/
  2026-07-xx/
    summary.md
    slides.pptx
    figures/
```

Rules:

- Every meeting summary should answer: last progress, evidence/results, blockers, next two-week plan.
- If slides are committed, Git LFS will handle `.pptx`.

## Sync Policy

Commit to Git:

- Code, configs, tests, Markdown notes, small CSV reports, annotation batches.

Do not commit to Git:

- `*.pem`, `.env*`, downloaded caches, model checkpoints, large raw datasets, virtual environments.

Use Git LFS later for:

- PPT/Word/PDF deliverables, model weights, archived zipped datasets.

Use DVC later for:

- Versioned raw datasets, large experiment outputs, model checkpoints, reproducibility pipelines.

