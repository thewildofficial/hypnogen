"""Core audio processing functionality."""
from hypnogen.core.epochs import (
    EPOCH_BOUNDARIES,
    EPOCH_NAMES,
    generate_boundary_event,
    generate_gain_envelope,
    get_epoch_at_position,
    get_epoch_boundaries_in_samples,
    get_layer_gain,
    select_boundary_events,
)
from hypnogen.core.export import (
    create_render_metadata,
    export_session,
    export_stems,
    write_metadata,
    write_wav,
)
from hypnogen.core.mixer import (
    DEFAULT_GAIN_DB,
    apply_gain_db,
    apply_limiter,
    mix_layers,
)
from hypnogen.core.parser import parse_script, validate_marking_density
from hypnogen.core.swarm import (
    apply_constant_power_pan,
    generate_swarm,
    schedule_affirmations,
    validate_affirmation,
    validate_affirmations,
)
from hypnogen.core.render import render_session
from hypnogen.core.tts import list_voices, synthesize, synthesize_batch
from hypnogen.core.llm import (
    AVAILABLE_MODELS,
    LLMError,
    generate_affirmations,
    generate_script,
    get_api_key,
)

__all__ = [
    "parse_script",
    "validate_marking_density",
    "validate_affirmation",
    "validate_affirmations",
    "apply_constant_power_pan",
    "schedule_affirmations",
    "generate_swarm",
    "synthesize",
    "synthesize_batch",
    "list_voices",
    "EPOCH_BOUNDARIES",
    "EPOCH_NAMES",
    "get_layer_gain",
    "generate_gain_envelope",
    "generate_boundary_event",
    "select_boundary_events",
    "get_epoch_at_position",
    "get_epoch_boundaries_in_samples",
    "DEFAULT_GAIN_DB",
    "apply_gain_db",
    "apply_limiter",
    "mix_layers",
    "write_wav",
    "export_stems",
    "create_render_metadata",
    "write_metadata",
    "export_session",
    "LLMError",
    "generate_affirmations",
    "generate_script",
    "get_api_key",
    "AVAILABLE_MODELS",
    "render_session",
]
