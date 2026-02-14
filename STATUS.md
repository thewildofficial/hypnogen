# Hypnogen Project Status

Snapshot date: 2026-02-14

Active branch: `wop-benchmark`
Active execution plan: `.sisyphus/plans/macos-ui-coreml-tts-accel.md`

## Completed (Shipped)

- [x] Core local generation stack (CLI + Gradio + render-core + FastAPI worker contract)
- [x] Affirmation generation v2 (tone support, stronger validation, retry/repair flow)
- [x] Root docs baseline (`README.md`, `ROADMAP.md`, benchmark docs)
- [x] macOS app IA + major visual redesign rollout (dark-only design system)
- [x] CoreML provider hybrid path and benchmark harnesses committed

## In Progress (Current Pass)

- [x] Benchmark normalization fix for tuple/list `numpy` outputs (WAV encoding for sanity checks)
- [x] CoreML benchmark compute-unit wiring (`ALL`, `CPU_AND_GPU`, `CPU_ONLY`) from CLI to provider
- [x] FastAPI lifecycle migration to `lifespan` shutdown hook
- [x] Worker output handling refactor (single stdout/stderr pipe)
- [ ] Final benchmark evidence refresh on a validated Python 3.12 + model-ready machine

## Pending / Next Up

- [ ] Run and publish reproducible TTS matrix:
  - `pytorch` baseline
  - `coreml` with `ALL`, `CPU_AND_GPU`, `CPU_ONLY`
  - commit JSON outputs under `.sisyphus/benchmarks/`
- [ ] Reconcile benchmark evidence summary (`.sisyphus/evidence/tts-accel-report.md`) with latest artifacts
- [ ] Run full `xcodebuild test` with macOS automation permissions and close remaining UI verification gaps
- [ ] Decide and document default local TTS runtime path for macOS package:
  - Python `coremltools` path vs Swift-native decoder path

## Deferred (Planned, Not Yet Active)

- Drafted deployable frontend + hosted inference plan:
  - `.sisyphus/drafts/deployable-frontend-and-inference-deployment.md`
- Public/unlisted/private feed + tag-search product direction remains in draft scope

## Where Contributors Should Start

1. Read this file, then `ROADMAP.md`.
2. Pull current backlog from `ISSUES_BACKLOG.md`.
3. Use `.sisyphus/plans/` as implementation reference and `.sisyphus/notepads/*/issues.md` as blocker history.
