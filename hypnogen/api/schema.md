# Render Job API Contract

Stable HTTP contract for the Hypnogen render pipeline.
Used by CLI, Gradio, SwiftUI macOS app, and future SaaS web client.

## Base URL

- **Local dev**: `http://127.0.0.1:8008`
- **SaaS (future)**: `https://api.hypnogen.io`

## Authentication

Not required for local mode. SaaS will use Bearer tokens (TBD).

---

## Endpoints

### `GET /health`

Health check. Returns 200 when the worker is ready.

**Response** `200 OK`

```json
{"status": "ok"}
```

---

### `POST /v1/render-jobs`

Submit a new render job. Returns immediately with a `job_id`; the render
executes asynchronously.

**Request Body** — `RenderJobSubmit`

| Field           | Type              | Required | Default      | Description                                         |
|-----------------|-------------------|----------|--------------|-----------------------------------------------------|
| `script`        | `string`          | Yes      | —            | Raw script text with optional XML tags              |
| `affirmations`  | `string[]`        | Yes      | —            | Affirmation strings for subliminal swarm (min 1)    |
| `voice`         | `string`          | No       | `"af_heart"` | TTS voice for shepherd (main narration) track       |
| `swarm_voice`   | `string \| null`  | No       | `null`       | TTS voice for swarm track (defaults to `voice`)     |
| `seed`          | `integer \| null` | No       | `null`       | Random seed for reproducibility                     |
| `length_sec`    | `integer \| null` | No       | `null`       | Session length in seconds (must be > 0 if set)      |
| `export_stems`  | `boolean`         | No       | `false`      | Export individual stem WAV files                     |
| `gain_db`       | `object \| null`  | No       | `null`       | Per-layer gain overrides in dB, e.g. `{"swarm": -24.0}` |

**Validation Rules**

- `script` must contain at least one non-whitespace character
- `affirmations` must have at least one element
- `length_sec` must be > 0 when provided

**Example Request**

```json
{
  "script": "Welcome to deep relaxation.\n<pause duration=\"2s\"/>\nLet go of all tension.",
  "affirmations": ["I am calm", "I am at peace", "I release all stress"],
  "voice": "af_heart",
  "seed": 42,
  "length_sec": 600,
  "export_stems": true
}
```

**Response** `202 Accepted`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0.0
}
```

---

### `GET /v1/render-jobs/{job_id}`

Poll job status. Use this endpoint to track progress and detect completion.

**Response** `200 OK` — `RenderJobStatus`

| Field      | Type              | Required | Default | Description                                           |
|------------|-------------------|----------|---------|-------------------------------------------------------|
| `job_id`   | `string`          | Yes      | —       | Unique job identifier                                 |
| `status`   | `JobStatus`       | Yes      | —       | One of: `pending`, `running`, `completed`, `failed`   |
| `stage`    | `string \| null`  | No       | `null`  | Human-readable stage, e.g. `"Shepherd TTS: 3/10 segments"` |
| `progress` | `float`           | No       | `0.0`   | Fractional progress `[0.0, 1.0]`                      |
| `eta_sec`  | `integer \| null` | No       | `null`  | Estimated seconds remaining                           |
| `error`    | `string \| null`  | No       | `null`  | Error message (only when `status == "failed"`)        |

**JobStatus Enum**

| Value       | Description                          |
|-------------|--------------------------------------|
| `pending`   | Job queued, waiting to start         |
| `running`   | Render in progress                   |
| `completed` | Render finished, artifacts available |
| `failed`    | Render failed, see `error` field     |

**Example Response (running)**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "stage": "Shepherd TTS: 5/12 segments",
  "progress": 0.42,
  "eta_sec": 87,
  "error": null
}
```

**Example Response (completed)**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "stage": null,
  "progress": 1.0,
  "eta_sec": null,
  "error": null
}
```

**Example Response (failed)**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "stage": null,
  "progress": 0.55,
  "eta_sec": null,
  "error": "TTS model download failed: connection timeout"
}
```

---

### `GET /v1/render-jobs/{job_id}/artifacts`

Retrieve artifact metadata for a completed job. In local mode, URLs are
filesystem paths. In SaaS mode, they become pre-signed download URLs.

**Response** `200 OK` — `RenderJobArtifacts`

| Field          | Type               | Required | Default | Description                                 |
|----------------|--------------------|----------|---------|---------------------------------------------|
| `job_id`       | `string`           | Yes      | —       | Unique job identifier                       |
| `mix_wav_url`  | `string`           | Yes      | —       | Path/URL to final mixed WAV                 |
| `stems`        | `object`           | No       | `{}`    | Map of stem name → path/URL                 |
| `metadata_url` | `string`           | Yes      | —       | Path/URL to `render.json`                   |
| `created_at`   | `string (ISO 8601)`| Yes      | —       | When artifacts were created                 |

**Example Response (with stems)**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "mix_wav_url": "/artifacts/550e8400/mix.wav",
  "stems": {
    "shepherd": "/artifacts/550e8400/shepherd.wav",
    "swarm": "/artifacts/550e8400/swarm.wav",
    "bed": "/artifacts/550e8400/bed.wav"
  },
  "metadata_url": "/artifacts/550e8400/render.json",
  "created_at": "2026-02-11T12:00:00Z"
}
```

**Example Response (no stems)**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "mix_wav_url": "/artifacts/550e8400/mix.wav",
  "stems": {},
  "metadata_url": "/artifacts/550e8400/render.json",
  "created_at": "2026-02-11T12:00:00Z"
}
```

---

## Error Responses

All endpoints return standard HTTP error codes with a JSON body:

```json
{
  "detail": "Human-readable error message"
}
```

| Code | When                                    |
|------|-----------------------------------------|
| 400  | Validation error (bad request body)     |
| 404  | Job not found                           |
| 409  | Job artifacts not yet available         |
| 422  | Unprocessable entity (Pydantic errors)  |
| 500  | Internal server error                   |

---

## Render Pipeline Stages

Progress stages reported via `RenderJobStatus.stage`:

1. `"Parsing script..."` — ~0%
2. `"Shepherd TTS: N/M segments"` — 2–55%
3. `"Swarm TTS: N/M affirmations"` — 55–85%
4. `"Generating binaural bed..."` — ~88%
5. `"Mixing layers & applying epochs..."` — ~93%
6. `"Exporting WAV..."` — ~97%
7. `"Done!"` — 100%

---

## File Layout (Local Mode)

When running locally, artifacts are stored under a project directory:

```
<project_dir>/
├── jobs/
│   └── <job_id>/
│       ├── request.json        # Serialized RenderJobSubmit
│       └── status.json         # Latest RenderJobStatus snapshot
└── artifacts/
    └── <job_id>/
        ├── mix.wav             # Final mixed output
        ├── shepherd.wav        # (if export_stems)
        ├── swarm.wav           # (if export_stems)
        ├── bed.wav             # (if export_stems)
        └── render.json         # Render metadata (seed, duration, voices, etc.)
```

---

## Pydantic Models

All models are defined in `hypnogen/api/models.py` and use Pydantic v2.

```python
from hypnogen.api.models import (
    RenderJobSubmit,
    RenderJobStatus,
    RenderJobArtifacts,
    JobStatus,
)
```
