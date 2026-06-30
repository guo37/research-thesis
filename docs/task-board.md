# Research Task Board

Last updated: 2026-06-30

Use this file as the short operational queue. Keep large reasoning in the linked experiment, paper, or meeting files.

## Now

- [x] Complete Exp0.1 labeling for `data/scienceqa/annotation/missing_type_annotation_candidates.csv`.
- [x] Summarize Exp0.1 label distribution and decide whether RC2 remains `MNAR-aware selective completion`.
- [ ] If labels are still auto-assisted, manually review all low-confidence/ambiguous rows before using them as thesis evidence.
- [x] Implement Exp0.2 selective-completion gate: predict `structural_absence` vs `review_or_completion_needed`.
- [ ] Add grouped stress test for Exp0.2 by holding out topic or skill groups.
- [ ] Choose one canonical thesis outline file and mark older outline content as preliminary.
- [ ] Prepare the next two-week group meeting summary from Exp0 and Exp0.1.

## Next

- [ ] Apply the Exp0.2 gate to all missing-image ScienceQA samples after grouped validation.
- [ ] Expand literature review to 30-40 papers.
- [ ] Build the minimum education knowledge graph: concept, resource, belongs_to, same_skill, prerequisite, related.
- [ ] Define RC1 baselines: CLIP, CLIP + adapter, ordinary contrastive, random hard negative, same-subject hard negative, concept-aware hard negative.
- [ ] Define RC3 100-sample explanation evaluation set schema.

## Later

- [ ] Add RC1 retrieval experiment script and config.
- [ ] Add RC2 selective completion baseline and ablation plan.
- [ ] Add RC3 explanation generation script and evaluation report.
- [ ] Convert stable meeting summaries into thesis writing bullets.

## Parking Lot

- Add DVC if raw datasets or model checkpoints become too large for Git/Git LFS.
- Add a research-specific Codex skill after the dashboard and task board stabilize.
- Add Zotero citation-key workflow for literature notes.
