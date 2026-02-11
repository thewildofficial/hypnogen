#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Feature Branch: macos-tts-acceleration-migration
# Creates atomic commits from working directory changes on master.
# =============================================================================

echo "=== Creating feature branch ==="
git checkout -b feature/macos-tts-acceleration-migration

# ---------------------------------------------------------------------------
# Commit 1: build: fix pyproject.toml package discovery
# ---------------------------------------------------------------------------
echo "=== Commit 1/10: pyproject.toml ==="
git add pyproject.toml
git commit -m "$(cat <<'EOF'
build: fix pyproject.toml package discovery

Add explicit package discovery with include/exclude to avoid setuptools
errors caused by multiple top-level directories (cosyvoice, dia, f5-tts, etc.).

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 2: feat(benchmarks): add baseline benchmark harness
# ---------------------------------------------------------------------------
echo "=== Commit 2/10: benchmarks ==="
git add \
  hypnogen/benchmarks/__init__.py \
  hypnogen/benchmarks/__main__.py \
  hypnogen/benchmarks/bench_render.py \
  hypnogen/benchmarks/compare.py \
  tests/test_benchmarks_smoke.py
git commit -m "$(cat <<'EOF'
feat(benchmarks): add baseline benchmark harness

Benchmark infrastructure for measuring TTS render performance.
Includes bench_render, comparison tooling, and smoke tests.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 3: feat(core): create unified render-core entry point
# ---------------------------------------------------------------------------
echo "=== Commit 3/10: render-core ==="
git add \
  hypnogen/core/render.py \
  hypnogen/core/__init__.py \
  hypnogen/cli.py \
  hypnogen/web.py \
  tests/test_render_core_smoke.py \
  tests/test_cli.py \
  tests/test_web.py \
  tests/test_calibration.py \
  _run_tests.py
git commit -m "$(cat <<'EOF'
feat(core): create unified render-core entry point

Single render_session() function callable by CLI, Gradio, and HTTP.
Refactor cli.py and web.py to delegate to render-core.
Update tests accordingly.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 4: feat(api): define stable Render Job contract (Pydantic)
# ---------------------------------------------------------------------------
echo "=== Commit 4/10: api models ==="
git add \
  hypnogen/api/__init__.py \
  hypnogen/api/models.py \
  hypnogen/api/schema.md \
  tests/test_api_models.py
git commit -m "$(cat <<'EOF'
feat(api): define stable Render Job contract (Pydantic)

Pydantic models for the HTTP API render job lifecycle.
Includes schema documentation and model validation tests.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 5: feat(api): implement FastAPI render worker
# ---------------------------------------------------------------------------
echo "=== Commit 5/10: api app + worker ==="
git add \
  hypnogen/api/app.py \
  hypnogen/api/worker.py \
  tests/test_api_smoke.py
git commit -m "$(cat <<'EOF'
feat(api): implement FastAPI render worker

FastAPI application with job submission, status polling, and result
retrieval endpoints. Background worker processes render jobs.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 6: feat(tts): add provider pattern for optimizations
# ---------------------------------------------------------------------------
echo "=== Commit 6/10: tts providers ==="
git add \
  hypnogen/core/tts_providers/__init__.py \
  hypnogen/core/tts_providers/base.py \
  hypnogen/core/tts_providers/pytorch.py \
  hypnogen/core/tts_providers/multiprocess.py \
  hypnogen/core/tts_providers/quantized.py \
  hypnogen/core/tts.py \
  tests/test_tts_providers.py
git commit -m "$(cat <<'EOF'
feat(tts): add provider pattern for optimizations

Base, PyTorch, multiprocess, and quantized TTS provider
implementations behind a unified interface. Enables runtime
selection of optimization strategy.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 7: feat(macos): scaffold SwiftUI macOS app
# ---------------------------------------------------------------------------
echo "=== Commit 7/10: macos scaffold ==="
git add \
  macos/Hypnogen.xcodeproj/project.pbxproj \
  macos/Hypnogen.xcodeproj/xcshareddata/xcschemes/Hypnogen.xcscheme \
  macos/Hypnogen/HypnogenApp.swift \
  macos/Hypnogen/ContentView.swift \
  macos/Hypnogen/Models/Constants.swift \
  macos/Hypnogen/Models/RenderJob.swift \
  macos/Hypnogen/Models/Project.swift \
  macos/Hypnogen/Services/APIClient.swift \
  macos/Hypnogen/Services/ProjectStore.swift \
  macos/Hypnogen/ViewModels/OutputsLibraryViewModel.swift \
  macos/Hypnogen/ViewModels/RenderQueueViewModel.swift \
  macos/Hypnogen/ViewModels/ProjectsViewModel.swift \
  macos/Hypnogen/Views/ProjectsView.swift \
  macos/Hypnogen/Views/RenderQueueView.swift \
  macos/Hypnogen/Views/OutputsLibraryView.swift \
  macos/Hypnogen/Views/ProjectEditorView.swift
git commit -m "$(cat <<'EOF'
feat(macos): scaffold SwiftUI macOS app

Initial Xcode project with core navigation: projects, render queue,
outputs library. MVVM architecture with APIClient and ProjectStore
services.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 8: feat(macos): add onboarding and guidance system
# ---------------------------------------------------------------------------
echo "=== Commit 8/10: macos onboarding ==="
git add \
  macos/Hypnogen/Views/OnboardingView.swift \
  macos/Hypnogen/Views/FeatureTourView.swift \
  macos/Hypnogen/Views/TipsGlossaryView.swift \
  macos/Hypnogen/Views/TroubleshootingView.swift \
  macos/Hypnogen/Resources/OnboardingContent.swift \
  macos/Hypnogen/ViewModels/OnboardingViewModel.swift
git commit -m "$(cat <<'EOF'
feat(macos): add onboarding and guidance system

Feature tour, tips glossary, and troubleshooting views.
OnboardingContent provides structured guidance data.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 9: feat(macos): add calibration flow
# ---------------------------------------------------------------------------
echo "=== Commit 9/10: macos calibration ==="
git add \
  macos/Hypnogen/Views/CalibrationView.swift \
  macos/Hypnogen/Services/AudioPlayer.swift \
  macos/Hypnogen/Models/CalibrationResult.swift \
  macos/Hypnogen/ViewModels/CalibrationViewModel.swift
git commit -m "$(cat <<'EOF'
feat(macos): add calibration flow

Audibility calibration with Yes/No frequency testing.
AudioPlayer service for tone generation, CalibrationViewModel
drives the step-by-step flow.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# ---------------------------------------------------------------------------
# Commit 10: test(macos): add XCUITest automation
# ---------------------------------------------------------------------------
echo "=== Commit 10/10: macos UI tests ==="
git add \
  macos/HypnogenUITests/HypnogenUITests.swift \
  macos/HypnogenUITests/ScreenshotHelper.swift \
  macos/HypnogenUITests/OnboardingTests.swift \
  macos/HypnogenUITests/ProjectTests.swift \
  macos/HypnogenUITests/LibraryTests.swift \
  macos/HypnogenUITests/RenderTests.swift
git commit -m "$(cat <<'EOF'
test(macos): add XCUITest automation

UI automation tests for onboarding, projects, library, and render
flows. ScreenshotHelper captures test evidence.

Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-opencode)

Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>
EOF
)"

# =============================================================================
# Verification
# =============================================================================
echo ""
echo "=== Verification ==="
echo ""
echo "--- Commit history ---"
git log --oneline
echo ""
echo "--- Remaining uncommitted files ---"
git status --short
echo ""
echo "=== Done. 10 atomic commits on feature/macos-tts-acceleration-migration ==="
