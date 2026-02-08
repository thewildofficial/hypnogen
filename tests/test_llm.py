"""Tests for LLM module with Gemini and NVIDIA support."""

import os
from unittest.mock import MagicMock, patch

import pytest

from hypnogen.core.llm import (
    AVAILABLE_MODELS,
    GEMINI_FLASH_MODEL,
    GEMINI_PRO_MODEL,
    KIMI_MODEL,
    LLMError,
    generate_affirmations,
    generate_script,
    get_api_key,
)


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
    @patch("hypnogen.core.llm._call_nvidia_api")
    def test_generate_script_fallback_to_kimi(self, mock_nvidia, mock_gemini):
        """generate_script falls back to Kimi if Gemini fails."""
        mock_gemini.side_effect = Exception("Gemini error")
        mock_nvidia.return_value = "Fallback script"

        with patch.dict(os.environ, {"GEMINI_KEY": "test", "NVIDIA_API_KEY": "test"}):
            result = generate_script("relax", 10, "ericksonian")

        assert result == "Fallback script"
        mock_nvidia.assert_called_once()


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
