# Hypnogen Roadmap

## Feature Map

### Gradio Features -> macOS Equivalents

| Gradio feature (`hypnogen/web.py`) | macOS equivalent (`macos/Hypnogen/Views/*.swift`) | Status / notes |
| --- | --- | --- |
| Script textbox (`Hypnotic Script`) | `ProjectEditorView` script `TextEditor` | Parity |
| Affirmations textbox (one per line) | `ProjectEditorView` affirmations list editor | Parity |
| Shepherd + Swarm voice dropdowns | `ProjectEditorView` settings popover (`Voice`, `Swarm Voice`) | Parity |
| Seed input (`Random Seed`) | `ProjectEditorView` settings popover (`Seed`) | Parity |
| Generate Audio button | `ProjectEditorView` `Render` button | Parity |
| In-flight progress text + progress callback | `RenderQueueView` progress bar, stage label, ETA | Parity |
| Download WAV file output | `OutputsLibraryView` + Finder reveal of rendered mix | Near parity (inline playback still placeholder) |
| Subliminal audibility calibration accordion | `CalibrationView` guided flow + persisted calibration result | Parity (UX is native flow instead of inline accordion) |
| AI Generate Script / Generate Affirmations / Generate Both | No direct equivalent in current macOS views | Gap |
| AI controls (goal, model, style, depth, command density, focus, custom instructions, tone) | No direct equivalent in current macOS views | Gap |
| Randomize voices toggle | No direct equivalent in current macOS views | Gap |

### CLI Options -> Render API Fields

| CLI option (`hypnogen/cli.py`) | Render API field (`hypnogen/api/models.py`) | Mapping details |
| --- | --- | --- |
| `--script` | `script` | CLI reads file and sends raw script text |
| `--affirmations` | `affirmations` | CLI reads lines, validates, sends list |
| `--voice` | `voice` | Direct map |
| `--seed` | `seed` | Direct map |
| `--length-sec` | `length_sec` | Direct map |
| `--stems-dir` | `export_stems` | Presence of stems dir implies `export_stems=true` |
| `--out` | _(no API field)_ | Client-side destination for final mix artifact |
| `--sr` | _(no submit field)_ | Used by local render path; not in `RenderJobSubmit` |
| `--generate-script`, `--generate-affirmations`, `--use-llm`, `--goal`, `--style`, `--affirmation-count` | Indirect -> `script` and/or `affirmations` | Pre-submit generation options; API receives generated content |
| _(no current CLI option)_ | `swarm_voice` | API supports it; CLI currently does not expose dedicated flag |
| _(no current CLI option)_ | `gain_db` | API supports per-layer gain overrides; CLI currently does not expose dedicated flag |

### Render Stages -> UI Progress Stages

| Render-core stage (`hypnogen/core/render.py`) | Progress window | macOS UI presentation (`RenderQueueView`) |
| --- | --- | --- |
| `Parsing script...` | `0.00` | Job row in Active section, stage text shown under progress bar |
| `Shepherd TTS: N/M segments` | `0.02 -> 0.55` | Stage text updates live; percent + ETA shown |
| `Swarm TTS: N/M affirmations` | `0.55 -> 0.85` | Stage text updates live; percent + ETA shown |
| `Generating binaural bed...` | `0.88` | Stage text shown in active job row |
| `Mixing layers & applying epochs...` | `0.93` | Stage text shown in active job row |
| `Exporting WAV...` | `0.97` | Stage text shown in active job row |
| `Done!` | `1.00` | Job moves to Completed section with completed status icon |
| Failure/cancel lifecycle | terminal status | Failed shows error text; cancelled uses cancelled icon/state |

## Roadmap

### v0 - Local Dev Build (Current Baseline)

- macOS app with local worker control, project editing, render queue, and outputs library.
- Local FastAPI render-job contract and polling loop wired into macOS queue UI.
- Render-core pipeline unified behind `render_session()` and reused by CLI/Gradio/API worker.
- Calibration flow implemented on macOS with persisted subliminal gain preference.
- Artifacts produced locally (`mix.wav`, optional stems, `render.json`).

### v0.1 - Performance Iteration

- Optimize render throughput by profiling stage hotspots (Shepherd TTS, Swarm TTS, mixing/export).
- Add/expand deterministic benchmark gates to detect regressions before release.
- Improve model/runtime selection for faster local inference and lower startup latency.
- Tighten progress/ETA quality so queue estimates remain stable for longer sessions.
- Reduce repeated work via caching opportunities where deterministic inputs permit reuse.

### v1 - SaaS Deploy Target (Linux/CUDA)

- Deploy GPU-backed render workers (Linux/CUDA) behind the same Render Job API contract.
- Move artifacts from local paths to object storage + pre-signed URLs.
- Add production queueing, retries, and worker autoscaling policies.
- Introduce auth, tenancy boundaries, and usage controls suitable for hosted workloads.
- Add production observability (job metrics, stage latency, failure taxonomy, alerting).

### Future - Distribution (DMG / Notarization / App Store)

- Harden macOS release pipeline: code signing, notarization, and DMG packaging.
- Define update/distribution channels (direct DMG + optional in-app updater strategy).
- Evaluate App Store path (sandbox, entitlement constraints, review-safe architecture).
- Standardize release artifacts, release notes, and rollback strategy for desktop builds.

## Release Checklist

### Build Verification

- [ ] Create clean Python environment and install project dependencies.
- [ ] Validate API server starts and health checks respond.
- [ ] Run CLI smoke render (`generate`) and confirm expected artifacts.
- [ ] Run macOS build (`xcodebuild`) for the active target/scheme in CI-compatible mode.
- [ ] Verify end-to-end local flow: submit render -> queue progress -> artifacts visible.

### Testing Requirements

- [ ] Unit tests pass for parsing, validation, render-core helpers, and API models.
- [ ] Integration tests pass for submit/status/artifacts/cancel API lifecycle.
- [ ] macOS UI smoke checks pass for project editing, render queue, calibration, outputs.
- [ ] Failure-path tests covered (worker unavailable, invalid payloads, cancellation, TTS failures).
- [ ] Performance baseline compared against previous release threshold (no unacceptable regression).

### Documentation Updates

- [ ] Update `README.md` setup/run instructions for current local workflow.
- [ ] Keep API contract docs in sync with `RenderJobSubmit`/status/artifacts fields.
- [ ] Update roadmap/release notes to reflect shipped scope and known gaps.
- [ ] Document migration notes for changed defaults, flags, or field semantics.
