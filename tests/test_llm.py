"""Tests for LLM module with Gemini and NVIDIA support."""

import os
from unittest.mock import MagicMock, call, patch

import pytest

from hypnogen.core.llm import (
    AVAILABLE_MODELS,
    GEMINI_FLASH_MODEL,
    GEMINI_PRO_MODEL,
    KIMI_MODEL,
    TONE_GUIDANCE,
    LLMError,
    _classify_line,
    generate_affirmations,
    generate_script,
    get_api_key,
)
from hypnogen.core.swarm import validate_affirmation


class TestGetApiKey:
    """Test API key retrieval."""

    @patch.dict(os.environ, {"NVIDIA_API_KEY": "test-nvidia-key"})
    def test_get_api_key_returns_nvidia_key(self):
        """get_api_key returns NVIDIA_API_KEY for nvidia provider."""
        key = get_api_key("nvidia")
        assert key == "test-nvidia-key"

    @patch.dict(os.environ, {"GEMINI_KEY": "test-gemini-key"})
    def test_get_api_key_returns_gemini_key(self):
        """get_api_key returns GEMINI_KEY for gemini provider."""
        key = get_api_key("gemini")
        assert key == "test-gemini-key"

    def test_get_api_key_raises_if_nvidia_not_set(self):
        """get_api_key raises ValueError if NVIDIA_API_KEY not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                get_api_key("nvidia")

    def test_get_api_key_raises_if_gemini_not_set(self):
        """get_api_key raises ValueError if GEMINI_KEY not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                get_api_key("gemini")


class TestGenerateScript:
    """Test script generation with fallback."""

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_script_uses_gemini_pro_first(self, mock_gemini):
        """generate_script tries Gemini Pro first."""
        mock_gemini.return_value = "And now... <cmd>relax</cmd>..."

        with patch.dict(os.environ, {"GEMINI_KEY": "test", "NVIDIA_API_KEY": "test"}):
            result = generate_script("relax", 10, "ericksonian")

        assert isinstance(result, str)
        assert "relax" in result or "<cmd>" in result
        mock_gemini.assert_called()

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_script_includes_goal_in_prompt(self, mock_gemini):
        """generate_script includes goal in the prompt sent to API."""
        mock_gemini.return_value = "Script content"
        captured_messages = []

        def capture_call(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return "Script"

        mock_gemini.side_effect = capture_call

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            generate_script("build confidence", 5, "ericksonian")

        assert any("build confidence" in msg["content"] for msg in captured_messages)

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_script_includes_style(self, mock_gemini):
        """generate_script includes style in the prompt."""
        mock_gemini.return_value = "Script content"
        captured_messages = []

        def capture_call(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return "Script"

        mock_gemini.side_effect = capture_call

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            generate_script("relax", 5, "permissive")

        assert any("permissive" in msg["content"] for msg in captured_messages)

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_script_includes_depth_in_prompt(self, mock_gemini):
        mock_gemini.return_value = "Script content"
        captured_messages = []

        def capture_call(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return "Script"

        mock_gemini.side_effect = capture_call

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            generate_script("relax", 5, "ericksonian", depth="deep")

        prompt_text = " ".join(msg["content"] for msg in captured_messages)
        assert "deeply immersive" in prompt_text or "profound trance" in prompt_text

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_script_includes_density_in_prompt(self, mock_gemini):
        mock_gemini.return_value = "Script content"
        captured_messages = []

        def capture_call(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return "Script"

        mock_gemini.side_effect = capture_call

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            generate_script("relax", 5, "ericksonian", command_density="high")

        prompt_text = " ".join(msg["content"] for msg in captured_messages)
        assert "frequently" in prompt_text

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_script_includes_focus_theme(self, mock_gemini):
        mock_gemini.return_value = "Script content"
        captured_messages = []

        def capture_call(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return "Script"

        mock_gemini.side_effect = capture_call

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            generate_script("relax", 5, focus_theme="ocean meditation")

        prompt_text = " ".join(msg["content"] for msg in captured_messages)
        assert "ocean meditation" in prompt_text

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_script_includes_custom_instructions(self, mock_gemini):
        mock_gemini.return_value = "Script content"
        captured_messages = []

        def capture_call(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return "Script"

        mock_gemini.side_effect = capture_call

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            generate_script("relax", 5, custom_instructions="Include a body scan")

        prompt_text = " ".join(msg["content"] for msg in captured_messages)
        assert "body scan" in prompt_text

    @patch("hypnogen.core.llm._call_gemini_api")
    @patch("hypnogen.core.llm._call_nvidia_api")
    def test_generate_script_fallback_to_kimi(self, mock_nvidia, mock_gemini):
        """generate_script falls back to Kimi if Gemini fails."""
        mock_gemini.side_effect = Exception("Gemini error")
        mock_nvidia.return_value = "Fallback script"

        with patch.dict(os.environ, {"GEMINI_KEY": "test", "NVIDIA_API_KEY": "test"}):
            result = generate_script("relax", 10, "ericksonian")

        assert result == "Fallback script"
        mock_nvidia.assert_called_once()

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_script_fractionation_style(self, mock_gemini):
        mock_gemini.return_value = "Script content"
        captured_messages = []

        def capture_call(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return "Script"

        mock_gemini.side_effect = capture_call

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            generate_script("relax", 5, "fractionation")

        prompt_text = " ".join(msg["content"] for msg in captured_messages)
        assert "fractionation" in prompt_text.lower()
        assert "<drop>" in prompt_text
        assert "<snap/>" in prompt_text


class TestGenerateAffirmations:
    """Test affirmation generation."""

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_affirmations_returns_list(self, mock_gemini):
        """generate_affirmations returns a list of strings."""
        mock_gemini.return_value = "I am calm\nI am strong\nI am confident"

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            result = generate_affirmations("relax", 3)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(a, str) for a in result)

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_affirmations_includes_goal(self, mock_gemini):
        """generate_affirmations includes goal in prompt."""
        mock_gemini.return_value = "I am calm"
        captured_messages = []

        def capture_call(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return "I am calm"

        mock_gemini.side_effect = capture_call

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            generate_affirmations("reduce anxiety", 5)

        assert any("reduce anxiety" in msg["content"] for msg in captured_messages)

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_affirmations_filters_invalid(self, mock_gemini):
        """generate_affirmations filters out invalid affirmations."""
        # "I was happy" is past tense (invalid)
        mock_gemini.return_value = "I am calm\nI was happy\nI am strong"

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            result = generate_affirmations("relax", 3)

        assert "I am calm" in result
        assert "I am strong" in result
        assert "I was happy" not in result

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_affirmations_strips_whitespace(self, mock_gemini):
        """generate_affirmations strips whitespace from lines."""
        mock_gemini.return_value = "  I am calm  \n  I am strong  "

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            result = generate_affirmations("relax", 2)

        assert all(not a.startswith(" ") and not a.endswith(" ") for a in result)

    @patch("hypnogen.core.llm._call_gemini_api")
    def test_generate_affirmations_skips_empty_lines(self, mock_gemini):
        """generate_affirmations skips empty lines."""
        mock_gemini.return_value = "I am calm\n\nI am strong\n\n"

        with patch.dict(os.environ, {"GEMINI_KEY": "test"}):
            result = generate_affirmations("relax", 2)

        assert len(result) == 2
        assert "I am calm" in result
        assert "I am strong" in result


class TestLLMError:
    """Test LLMError exception."""

    def test_llm_error_is_exception(self):
        """LLMError is an Exception subclass."""
        assert issubclass(LLMError, Exception)

    def test_llm_error_can_be_raised(self):
        """LLMError can be raised and caught."""
        with pytest.raises(LLMError):
            raise LLMError("test error")


class TestConstants:
    """Test module constants."""

    def test_model_constants_defined(self):
        """Model constants are defined."""
        assert isinstance(KIMI_MODEL, str)
        assert isinstance(GEMINI_PRO_MODEL, str)
        assert isinstance(GEMINI_FLASH_MODEL, str)

    def test_available_models_defined(self):
        """AVAILABLE_MODELS is defined as list of tuples."""
        assert isinstance(AVAILABLE_MODELS, list)
        assert len(AVAILABLE_MODELS) > 0
        for name, value in AVAILABLE_MODELS:
            assert isinstance(name, str)
            assert isinstance(value, str)

    def test_tone_guidance_has_all_tones(self):
        """TONE_GUIDANCE contains all expected tone keys."""
        expected = {
            "calm therapeutic",
            "intense coach",
            "mystic-poetic",
            "clinical-precision",
            "minimalist",
        }
        assert set(TONE_GUIDANCE.keys()) == expected


class TestClassifyLine:
    """Test _classify_line helper for diversity checking."""

    def test_i_statement_lowercase(self):
        assert _classify_line("I am strong") == "I"

    def test_my_statement(self):
        assert _classify_line("My confidence grows") == "I"

    def test_me_statement(self):
        assert _classify_line("Me time is sacred") == "I"

    def test_you_statement(self):
        assert _classify_line("You are powerful") == "You"

    def test_your_statement(self):
        assert _classify_line("Your strength is immense") == "You"

    def test_reality_assertion(self):
        assert _classify_line("The world supports growth") == "Reality"

    def test_reality_assertion_another(self):
        assert _classify_line("Peace flows through everything") == "Reality"


class TestGenerateAffirmationsTone:
    """Test that tone parameter affects the prompt sent to LLM."""

    @patch("hypnogen.core.llm._call_api_with_fallback")
    def test_tone_included_in_prompt(self, mock_api):
        """Tone guidance text appears in the prompt for each tone."""
        mock_api.return_value = (
            "I am calm and centered\n"
            "You are at peace\n"
            "The universe supports me"
        )

        with patch.dict(os.environ, {"GEMINI_KEY": "t", "NVIDIA_API_KEY": "t"}):
            for tone, guidance in TONE_GUIDANCE.items():
                mock_api.reset_mock()
                generate_affirmations("relax", count=3, tone=tone)
                prompt_sent = mock_api.call_args[0][0][0]["content"]
                assert guidance in prompt_sent, (
                    f"Tone '{tone}' guidance not found in prompt"
                )

    @patch("hypnogen.core.llm._call_api_with_fallback")
    def test_default_tone_is_calm_therapeutic(self, mock_api):
        """Default tone is 'calm therapeutic'."""
        mock_api.return_value = (
            "I am calm\nYou are relaxed\nPeace surrounds me"
        )
        with patch.dict(os.environ, {"GEMINI_KEY": "t", "NVIDIA_API_KEY": "t"}):
            generate_affirmations("relax", count=3)
            prompt_sent = mock_api.call_args[0][0][0]["content"]
            assert TONE_GUIDANCE["calm therapeutic"] in prompt_sent


class TestGenerateAffirmationsRetryInvalidLines:
    """Test retry loop triggers when LLM returns invalid lines."""

    @patch("hypnogen.core.llm._call_api_with_fallback")
    def test_retries_when_too_few_valid_lines(self, mock_api):
        """Retries when most lines fail validation (e.g. contain 'will')."""
        # First call: mostly invalid (will, negations)
        bad_response = (
            "I will succeed tomorrow\n"
            "I am not afraid of anything\n"
            "I am calm and centered\n"
            "You are at peace\n"
            "The world is kind"
        )
        # Second call: all valid
        good_response = (
            "I am strong and powerful\n"
            "You deserve happiness\n"
            "My mind is clear\n"
            "Your heart is open\n"
            "Peace radiates outward"
        )
        mock_api.side_effect = [bad_response, good_response]

        with patch.dict(os.environ, {"GEMINI_KEY": "t", "NVIDIA_API_KEY": "t"}):
            result = generate_affirmations("confidence", count=5)

        # Should have called API twice (initial + 1 retry)
        assert mock_api.call_count == 2
        # All returned lines must pass validation
        for line in result:
            valid, _ = validate_affirmation(line)
            assert valid, f"Invalid line in output: {line}"

    @patch("hypnogen.core.llm._call_api_with_fallback")
    def test_stops_after_max_retries(self, mock_api):
        """Returns whatever valid lines exist after max 3 attempts."""
        # All 3 attempts return mostly invalid lines
        bad_response = (
            "I will be great\n"
            "I won't fail\n"
            "I am calm\n"
            "You are strong\n"
            "Joy exists everywhere"
        )
        mock_api.return_value = bad_response

        with patch.dict(os.environ, {"GEMINI_KEY": "t", "NVIDIA_API_KEY": "t"}):
            result = generate_affirmations("confidence", count=5)

        # Should have tried exactly 3 times total
        assert mock_api.call_count == 3
        # Should still return whatever valid lines were found
        for line in result:
            valid, _ = validate_affirmation(line)
            assert valid


class TestGenerateAffirmationsRetryDiversity:
    """Test retry loop triggers on non-diverse mix."""

    @patch("hypnogen.core.llm._call_api_with_fallback")
    def test_retries_when_all_i_statements(self, mock_api):
        """Retries when output is all I-statements (no diversity)."""
        all_i = (
            "I am calm\n"
            "I am strong\n"
            "I am confident\n"
            "I am happy\n"
            "I am focused"
        )
        diverse = (
            "I am calm\n"
            "I am strong\n"
            "You are confident\n"
            "Your focus is sharp\n"
            "Peace fills the room"
        )
        mock_api.side_effect = [all_i, diverse]

        with patch.dict(os.environ, {"GEMINI_KEY": "t", "NVIDIA_API_KEY": "t"}):
            result = generate_affirmations("confidence", count=5)

        assert mock_api.call_count == 2

    @patch("hypnogen.core.llm._call_api_with_fallback")
    def test_retries_when_all_you_statements(self, mock_api):
        """Retries when output is all You-statements."""
        all_you = (
            "You are calm\n"
            "You are strong\n"
            "You are confident\n"
            "You are happy\n"
            "Your life is great"
        )
        diverse = (
            "I am calm\n"
            "My strength grows\n"
            "You are confident\n"
            "Your focus is sharp\n"
            "Peace fills the room"
        )
        mock_api.side_effect = [all_you, diverse]

        with patch.dict(os.environ, {"GEMINI_KEY": "t", "NVIDIA_API_KEY": "t"}):
            result = generate_affirmations("confidence", count=5)

        assert mock_api.call_count == 2


class TestGenerateAffirmationsOutputValidation:
    """Test that final output always passes validate_affirmation."""

    @patch("hypnogen.core.llm._call_api_with_fallback")
    def test_all_returned_lines_pass_validation(self, mock_api):
        """Every line in the output passes validate_affirmation."""
        mock_api.return_value = (
            "I am calm and centered\n"
            "You deserve deep peace\n"
            "My confidence grows each day\n"
            "Your mind is sharp\n"
            "Strength flows through everything"
        )

        with patch.dict(os.environ, {"GEMINI_KEY": "t", "NVIDIA_API_KEY": "t"}):
            result = generate_affirmations("inner peace", count=5)

        assert len(result) > 0
        for line in result:
            valid, reason = validate_affirmation(line)
            assert valid, f"Line failed validation: '{line}' — {reason}"
