"""Tests for Web UI module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import gradio as gr
import numpy as np
import pytest


class TestCreateUI:
    """Test create_ui function."""

    def test_create_ui_returns_gradio_blocks(self):
        """create_ui() returns a Gradio Blocks instance."""
        from hypnogen.web import create_ui

        app = create_ui()
        assert isinstance(app, gr.Blocks)

    def test_create_ui_has_title(self):
        """create_ui() sets app title to Hypnogen."""
        from hypnogen.web import create_ui

        app = create_ui()
        assert app.title == "Hypnogen"


class TestUIComponents:
    """Test UI components exist and are properly configured."""

    def test_ui_has_script_input(self):
        """UI has a TextArea for script input."""
        from hypnogen.web import create_ui

        app = create_ui()
        # Check that there's a TextArea with "Script" in the label
        textareas = [b for b in app.blocks.values() if isinstance(b, gr.Textbox)]
        script_found = any("script" in (t.label or "").lower() for t in textareas)
        assert script_found, "Script input TextArea not found"

    def test_ui_has_affirmations_input(self):
        """UI has a TextArea for affirmations input."""
        from hypnogen.web import create_ui

        app = create_ui()
        textareas = [b for b in app.blocks.values() if isinstance(b, gr.Textbox)]
        aff_found = any("affirmation" in (t.label or "").lower() for t in textareas)
        assert aff_found, "Affirmations input TextArea not found"

    def test_ui_has_voice_dropdown(self):
        """UI has Dropdowns for shepherd and swarm voice selection."""
        from hypnogen.web import create_ui

        app = create_ui()
        dropdowns = [b for b in app.blocks.values() if isinstance(b, gr.Dropdown)]
        shepherd_found = any("shepherd" in (d.label or "").lower() for d in dropdowns)
        swarm_found = any("swarm" in (d.label or "").lower() for d in dropdowns)
        assert shepherd_found, "Shepherd voice dropdown not found"
        assert swarm_found, "Swarm voice dropdown not found"

    def test_ui_has_seed_input(self):
        """UI has a Number input for seed."""
        from hypnogen.web import create_ui

        app = create_ui()
        numbers = [b for b in app.blocks.values() if isinstance(b, gr.Number)]
        seed_found = any("seed" in (n.label or "").lower() for n in numbers)
        assert seed_found, "Seed input not found"

    def test_ui_has_randomize_voices_checkbox(self):
        from hypnogen.web import create_ui

        app = create_ui()
        checkboxes = [b for b in app.blocks.values() if isinstance(b, gr.Checkbox)]
        randomize_found = any("randomize" in (c.label or "").lower() for c in checkboxes)
        assert randomize_found, "Randomize voices checkbox not found"

    def test_ui_has_generate_button(self):
        """UI has a Generate button."""
        from hypnogen.web import create_ui

        app = create_ui()
        buttons = [b for b in app.blocks.values() if isinstance(b, gr.Button)]
        generate_found = any("generate" in (b.value or "").lower() for b in buttons)
        assert generate_found, "Generate button not found"

    def test_ui_has_audio_output(self):
        """UI has an Audio output component."""
        from hypnogen.web import create_ui

        app = create_ui()
        audio_outputs = [b for b in app.blocks.values() if isinstance(b, gr.Audio)]
        assert len(audio_outputs) > 0, "Audio output not found"

    def test_ui_has_file_download(self):
        """UI has a File download component."""
        from hypnogen.web import create_ui

        app = create_ui()
        file_outputs = [b for b in app.blocks.values() if isinstance(b, gr.File)]
        assert len(file_outputs) > 0, "File download not found"


class TestGenerateAudio:
    """Test generate_audio function."""

    @pytest.fixture
    def mock_synthesize(self):
        """Mock TTS synthesize to avoid downloading model."""
        mock_audio = np.zeros(24000, dtype=np.float32)
        with patch("hypnogen.web.synthesize") as mock:
            mock.return_value = (mock_audio, 24000)
            yield mock

    def test_generate_audio_returns_audio_tuple_and_filepath(self, mock_synthesize):
        """generate_audio returns ((audio_array, sample_rate), filepath)."""
        from hypnogen.web import generate_audio

        script = "Welcome to relaxation."
        affirmations = "I am calm\nI am peaceful"
        shepherd_voice = "af_heart"
        swarm_voice = "af_heart"
        randomize = False
        seed = 42

        result = generate_audio(script, affirmations, shepherd_voice, swarm_voice, randomize, seed)

        # Should return tuple: (audio_tuple, filepath, info)
        assert isinstance(result, tuple)
        assert len(result) == 3

        audio_tuple, filepath, info = result
        # audio_tuple should be (sample_rate, audio_array)
        assert isinstance(audio_tuple, tuple)
        assert len(audio_tuple) == 2
        sr, audio = audio_tuple
        assert isinstance(sr, int)
        assert isinstance(audio, np.ndarray)

        # filepath should be a string path to WAV file
        assert isinstance(filepath, str)
        assert filepath.endswith(".wav")

    def test_generate_audio_creates_temp_file(self, mock_synthesize):
        """generate_audio creates a temporary WAV file for download."""
        from hypnogen.web import generate_audio

        script = "Welcome."
        affirmations = "I am calm"
        shepherd_voice = "af_heart"
        swarm_voice = "af_heart"
        randomize = False
        seed = 42

        _, filepath, _ = generate_audio(script, affirmations, shepherd_voice, swarm_voice, randomize, seed)

        assert Path(filepath).exists(), f"Temp file not created: {filepath}"

    def test_generate_audio_handles_none_seed(self, mock_synthesize):
        """generate_audio works with seed=None (random)."""
        from hypnogen.web import generate_audio

        script = "Welcome."
        affirmations = "I am calm"
        shepherd_voice = "af_heart"
        swarm_voice = "af_heart"
        randomize = False
        seed = None

        result = generate_audio(script, affirmations, shepherd_voice, swarm_voice, randomize, seed)
        assert result is not None

    def test_generate_audio_validates_affirmations(self, mock_synthesize):
        """generate_audio skips invalid affirmations."""
        from hypnogen.web import generate_audio

        script = "Welcome."
        affirmations = "I am calm\nI was happy\nI am peaceful"
        shepherd_voice = "af_heart"
        swarm_voice = "af_heart"
        randomize = False
        seed = 42

        result = generate_audio(script, affirmations, shepherd_voice, swarm_voice, randomize, seed)
        assert result is not None

    def test_generate_audio_with_embedded_commands(self, mock_synthesize):
        """generate_audio processes script with embedded commands."""
        from hypnogen.web import generate_audio

        script = 'You can <cmd pitch="-2">relax deeply</cmd> now.'
        affirmations = "I am calm"
        shepherd_voice = "af_heart"
        swarm_voice = "af_heart"
        randomize = False
        seed = 42

        result = generate_audio(script, affirmations, shepherd_voice, swarm_voice, randomize, seed)
        assert result is not None

    def test_generate_audio_with_randomize_voices(self, mock_synthesize):
        from hypnogen.web import generate_audio

        script = "Welcome."
        affirmations = "I am calm"

        result = generate_audio(script, affirmations, "af_heart", "af_heart", True, 42)
        assert result is not None
        _, _, info = result
        assert "Shepherd voice:" in info
        assert "Swarm voice:" in info

    def test_generate_audio_randomize_picks_different_voices(self, mock_synthesize):
        from hypnogen.web import generate_audio

        result = generate_audio("Welcome.", "I am calm", "af_heart", "af_heart", True, 42)
        _, _, info = result
        shepherd_voice = info.split("Shepherd voice: ")[1].split(" |")[0]
        swarm_voice = info.split("Swarm voice: ")[1]
        assert shepherd_voice != swarm_voice


class TestAppLaunch:
    """Test app can be configured for launch."""

    def test_app_can_be_created_without_launch(self):
        """App can be created without immediately launching."""
        from hypnogen.web import create_ui

        app = create_ui()
        # Should not raise, just create the app
        assert app is not None

    def test_main_module_exists(self):
        """Module can be run as __main__."""
        # Check that the module structure is correct
        import hypnogen.web as web_module

        assert hasattr(web_module, "create_ui")
        assert hasattr(web_module, "generate_audio")


class TestDefaults:
    """Test default script and affirmations are provided."""

    def test_default_script_exists(self):
        """DEFAULT_SCRIPT is defined."""
        from hypnogen.web import DEFAULT_SCRIPT

        assert isinstance(DEFAULT_SCRIPT, str)
        assert len(DEFAULT_SCRIPT) > 0

    def test_default_affirmations_exists(self):
        """DEFAULT_AFFIRMATIONS is defined."""
        from hypnogen.web import DEFAULT_AFFIRMATIONS

        assert isinstance(DEFAULT_AFFIRMATIONS, str)
        assert len(DEFAULT_AFFIRMATIONS) > 0

    def test_default_script_has_embedded_command(self):
        """DEFAULT_SCRIPT contains at least one <cmd> tag."""
        from hypnogen.web import DEFAULT_SCRIPT

        assert "<cmd" in DEFAULT_SCRIPT

    def test_default_affirmations_has_multiple_lines(self):
        """DEFAULT_AFFIRMATIONS contains multiple affirmations."""
        from hypnogen.web import DEFAULT_AFFIRMATIONS

        lines = [l.strip() for l in DEFAULT_AFFIRMATIONS.strip().splitlines() if l.strip()]
        assert len(lines) >= 3, "Should have at least 3 default affirmations"


class TestWebLLMIntegration:

    def test_ui_has_goal_input(self):
        from hypnogen.web import create_ui

        app = create_ui()
        textareas = [b for b in app.blocks.values() if isinstance(b, gr.Textbox)]
        goal_found = any("goal" in (t.label or "").lower() for t in textareas)
        assert goal_found, "Goal input not found in UI"

    def test_ui_has_generate_script_button(self):
        from hypnogen.web import create_ui

        app = create_ui()
        buttons = [b for b in app.blocks.values() if isinstance(b, gr.Button)]
        gen_script_found = any("generate script" in (b.value or "").lower() for b in buttons)
        assert gen_script_found, "Generate Script button not found"

    def test_ui_has_generate_affirmations_button(self):
        from hypnogen.web import create_ui

        app = create_ui()
        buttons = [b for b in app.blocks.values() if isinstance(b, gr.Button)]
        gen_aff_found = any("generate affirmation" in (b.value or "").lower() for b in buttons)
        assert gen_aff_found, "Generate Affirmations button not found"

    def test_ui_has_style_dropdown(self):
        from hypnogen.web import create_ui

        app = create_ui()
        dropdowns = [b for b in app.blocks.values() if isinstance(b, gr.Dropdown)]
        style_found = any("style" in (d.label or "").lower() for d in dropdowns)
        assert style_found, "Style dropdown not found"

    def test_ui_has_model_dropdown(self):
        from hypnogen.web import create_ui

        app = create_ui()
        dropdowns = [b for b in app.blocks.values() if isinstance(b, gr.Dropdown)]
        model_found = any("model" in (d.label or "").lower() for d in dropdowns)
        assert model_found, "AI Model dropdown not found"

    def test_ui_has_depth_dropdown(self):
        from hypnogen.web import create_ui

        app = create_ui()
        dropdowns = [b for b in app.blocks.values() if isinstance(b, gr.Dropdown)]
        depth_found = any("depth" in (d.label or "").lower() for d in dropdowns)
        assert depth_found, "Induction Depth dropdown not found"

    def test_ui_has_density_dropdown(self):
        from hypnogen.web import create_ui

        app = create_ui()
        dropdowns = [b for b in app.blocks.values() if isinstance(b, gr.Dropdown)]
        density_found = any("density" in (d.label or "").lower() for d in dropdowns)
        assert density_found, "Embedded Command Density dropdown not found"

    def test_ui_has_focus_input(self):
        from hypnogen.web import create_ui

        app = create_ui()
        textareas = [b for b in app.blocks.values() if isinstance(b, gr.Textbox)]
        focus_found = any("theme" in (t.label or "").lower() or "focus" in (t.label or "").lower() for t in textareas)
        assert focus_found, "Theme/Focus input not found"

    def test_ui_has_custom_instructions_input(self):
        from hypnogen.web import create_ui

        app = create_ui()
        textareas = [b for b in app.blocks.values() if isinstance(b, gr.Textbox)]
        custom_found = any("custom" in (t.label or "").lower() or "instruction" in (t.label or "").lower() for t in textareas)
        assert custom_found, "Custom Instructions input not found"

    def test_ui_has_duration_input(self):
        from hypnogen.web import create_ui

        app = create_ui()
        numbers = [b for b in app.blocks.values() if isinstance(b, gr.Number)]
        duration_found = any("duration" in (n.label or "").lower() for n in numbers)
        assert duration_found, "Target Duration input not found"

    @patch("hypnogen.web.llm_generate_script")
    def test_ai_generate_script_calls_llm(self, mock_llm):
        from hypnogen.web import ai_generate_script

        mock_llm.return_value = "And now... <cmd>relax deeply</cmd>..."
        result = ai_generate_script(
            "build confidence", "ericksonian", 10,
            "medium", "medium", "", "", "Gemini Pro",
        )
        assert isinstance(result, str)
        assert "relax" in result
        mock_llm.assert_called_once()

    @patch("hypnogen.web.llm_generate_affirmations")
    def test_ai_generate_affirmations_calls_llm(self, mock_llm):
        from hypnogen.web import ai_generate_affirmations

        mock_llm.return_value = ["I am calm", "I feel strong"]
        result = ai_generate_affirmations("reduce stress", 10)
        assert isinstance(result, str)
        assert "I am calm" in result
        assert "I feel strong" in result
        mock_llm.assert_called_once()

    def test_ai_generate_script_empty_goal_raises(self):
        from hypnogen.web import ai_generate_script

        with pytest.raises(gr.Error):
            ai_generate_script("", "ericksonian", 10, "medium", "medium", "", "", "Gemini Pro")

    def test_ai_generate_affirmations_empty_goal_raises(self):
        from hypnogen.web import ai_generate_affirmations

        with pytest.raises(gr.Error):
            ai_generate_affirmations("", 10)

    @patch("hypnogen.web.llm_generate_script")
    def test_ai_generate_script_llm_error_raises_gr_error(self, mock_llm):
        from hypnogen.core.llm import LLMError
        from hypnogen.web import ai_generate_script

        mock_llm.side_effect = LLMError("API timeout")
        with pytest.raises(gr.Error):
            ai_generate_script("relax", "ericksonian", 10, "medium", "medium", "", "", "Gemini Pro")

    def test_ui_has_generate_both_button(self):
        from hypnogen.web import create_ui

        app = create_ui()
        buttons = [c for c in app.blocks.values() if isinstance(c, gr.Button)]
        button_texts = [b.value for b in buttons]
        assert "Generate Both" in button_texts

    @patch("hypnogen.web.llm_generate_script")
    @patch("hypnogen.web.llm_generate_affirmations")
    def test_ai_generate_both_calls_both_llm_functions(self, mock_aff, mock_script):
        from hypnogen.web import ai_generate_both

        mock_script.return_value = "Test script content"
        mock_aff.return_value = ["I am calm", "I am focused"]

        script, aff_text = ai_generate_both(
            "relax", "ericksonian", 20,
            10, "medium", "medium", "", "", "Gemini Pro",
        )

        mock_script.assert_called_once_with(
            goal="relax", duration_minutes=10, style="ericksonian",
            depth="medium", command_density="medium",
            focus_theme="", custom_instructions="",
        )
        mock_aff.assert_called_once_with(goal="relax", count=20)
        assert script == "Test script content"
        assert aff_text == "I am calm\nI am focused"

    def test_ai_generate_both_empty_goal_raises(self):
        from hypnogen.web import ai_generate_both

        with pytest.raises(gr.Error):
            ai_generate_both("", "ericksonian", 20, 10, "medium", "medium", "", "", "Gemini Pro")

    @patch("hypnogen.web.llm_generate_script")
    def test_ai_generate_both_llm_error_raises_gr_error(self, mock_llm):
        from hypnogen.core.llm import LLMError
        from hypnogen.web import ai_generate_both

        mock_llm.side_effect = LLMError("API timeout")
        with pytest.raises(gr.Error):
            ai_generate_both("relax", "ericksonian", 20, 10, "medium", "medium", "", "", "Gemini Pro")
