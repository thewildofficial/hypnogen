"""Tests for calibration UI and level selection."""

import numpy as np
import pytest
import gradio as gr
from unittest.mock import patch, MagicMock
from pathlib import Path

def test_calibration_levels_constant():
    """CALIBRATION_LEVELS is defined with 5 options."""
    from hypnogen.web import CALIBRATION_LEVELS
    assert len(CALIBRATION_LEVELS) == 5
    assert CALIBRATION_LEVELS[0][0] == -30
    assert CALIBRATION_LEVELS[4][0] == -6

def test_ui_has_calibration_accordion():
    """UI has an accordion for calibration."""
    from hypnogen.web import create_ui
    app = create_ui()
    accordions = [b for b in app.blocks.values() if isinstance(b, gr.Accordion)]
    calib_found = any("calibration" in (a.label or "").lower() for a in accordions)
    assert calib_found, "Calibration accordion not found"

def test_ui_has_calibration_samples():
    """UI has 5 audio components for calibration samples."""
    from hypnogen.web import create_ui
    app = create_ui()
    # Find the calibration accordion first
    accordions = [b for b in app.blocks.values() if isinstance(b, gr.Accordion)]
    calib_accordion = next(a for a in accordions if "calibration" in (a.label or "").lower())
    
    # Check for 5 audio components within the UI
    audio_components = [b for b in app.blocks.values() if isinstance(b, gr.Audio)]
    # 1 for output, 5 for calibration = 6 total
    assert len(audio_components) >= 6

def test_ui_has_level_selection():
    """UI has a radio button group for level selection."""
    from hypnogen.web import create_ui
    app = create_ui()
    radios = [b for b in app.blocks.values() if isinstance(b, gr.Radio)]
    level_found = any("level" in (r.label or "").lower() or "audibility" in (r.label or "").lower() for r in radios)
    assert level_found, "Level selection radio not found"

@patch("hypnogen.web.synthesize")
def test_generate_calibration_samples(mock_synthesize):
    """generate_calibration_samples returns 5 audio paths."""
    from hypnogen.web import generate_calibration_samples
    
    mock_audio = np.zeros(24000, dtype=np.float32)
    mock_synthesize.return_value = (mock_audio, 24000)
    
    samples = generate_calibration_samples("af_heart")
    assert len(samples) == 5
    for s in samples:
        assert isinstance(s, str)
        assert s.endswith(".wav")
        assert Path(s).exists()

@patch("hypnogen.web.mix_layers")
@patch("hypnogen.web.synthesize")
def test_generate_audio_uses_selected_level(mock_synthesize, mock_mix):
    """generate_audio passes the selected subliminal level to mix_layers."""
    from hypnogen.web import generate_audio
    
    mock_audio = np.zeros(24000, dtype=np.float32)
    mock_synthesize.return_value = (mock_audio, 24000)
    mock_mix.return_value = np.zeros((24000, 2), dtype=np.float32)
    
    # Default level
    generate_audio("Script", "Affirmation", "af_heart", "af_heart", False, 42)
    # Check that mix_layers was called with swarm gain
    args, kwargs = mock_mix.call_args
    assert kwargs["gain_db"]["swarm"] == -18.0
    
    # Custom level
    generate_audio("Script", "Affirmation", "af_heart", "af_heart", False, 42, subliminal_level_db=-12.0)
    args, kwargs = mock_mix.call_args
    assert kwargs["gain_db"]["swarm"] == -12.0
