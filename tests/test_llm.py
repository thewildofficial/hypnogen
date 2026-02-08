"""Tests for LLM client (Kimi K2.5 via NVIDIA API)."""

import os
from unittest.mock import MagicMock, patch

import pytest


# --- Test get_api_key ---

def test_get_api_key_returns_key_from_env():
    """get_api_key returns API key when NVIDIA_API_KEY is set."""
    from hypnogen.core.llm import get_api_key
    
    with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-api-key-123"}):
        key = get_api_key()
        assert key == "test-api-key-123"


def test_get_api_key_raises_if_not_set():
    """get_api_key raises ValueError when NVIDIA_API_KEY is not set."""
    from hypnogen.core.llm import get_api_key
    
    with patch.dict(os.environ, {}, clear=True):
        # Also need to remove from environ if it was set
        with patch.object(os, 'environ', {}):
            with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
                get_api_key()


# --- Test _call_api ---

@patch('hypnogen.core.llm.httpx.post')
def test_call_api_sends_correct_headers(mock_post):
    """_call_api sends Authorization and Accept headers."""
    from hypnogen.core.llm import _call_api
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "test response"}}]
    }
    mock_post.return_value = mock_response
    
    _call_api([{"role": "user", "content": "test"}], api_key="my-api-key")
    
    # Check headers
    call_kwargs = mock_post.call_args
    headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
    assert headers["Authorization"] == "Bearer my-api-key"
    assert "Accept" in headers


@patch('hypnogen.core.llm.httpx.post')
def test_call_api_sends_correct_payload(mock_post):
    """_call_api sends correct payload structure with model and messages."""
    from hypnogen.core.llm import _call_api
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "response text"}}]
    }
    mock_post.return_value = mock_response
    
    messages = [{"role": "user", "content": "Hello"}]
    _call_api(messages, api_key="key", max_tokens=1024, temperature=0.7)
    
    call_kwargs = mock_post.call_args
    json_data = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
    
    assert json_data["model"] == "moonshotai/kimi-k2.5"
    assert json_data["messages"] == messages
    assert json_data["max_tokens"] == 1024
    assert json_data["temperature"] == 0.7
    assert "chat_template_kwargs" in json_data


@patch('hypnogen.core.llm.httpx.post')
def test_call_api_returns_content(mock_post):
    """_call_api returns message content from response."""
    from hypnogen.core.llm import _call_api
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "The answer is 42"}}]
    }
    mock_post.return_value = mock_response
    
    result = _call_api([{"role": "user", "content": "test"}], api_key="key")
    assert result == "The answer is 42"


@patch('hypnogen.core.llm.httpx.post')
def test_call_api_raises_on_http_error(mock_post):
    """_call_api raises LLMError on HTTP error status."""
    from hypnogen.core.llm import _call_api, LLMError
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = Exception("HTTP Error")
    mock_post.return_value = mock_response
    
    with pytest.raises(LLMError):
        _call_api([{"role": "user", "content": "test"}], api_key="key")


@patch('hypnogen.core.llm.httpx.post')
def test_call_api_raises_on_api_error(mock_post):
    """_call_api raises LLMError when API returns error response."""
    from hypnogen.core.llm import _call_api, LLMError
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "error": {"message": "Rate limit exceeded"}
    }
    mock_post.return_value = mock_response
    
    with pytest.raises(LLMError):
        _call_api([{"role": "user", "content": "test"}], api_key="key")


# --- Test generate_script ---

@patch('hypnogen.core.llm._call_api')
def test_generate_script_returns_string_with_cmd_tags(mock_call_api):
    """generate_script returns script text with <cmd> tags."""
    from hypnogen.core.llm import generate_script
    
    mock_call_api.return_value = """And now... as you relax...
<cmd pitch="-2" rate="0.9">let go completely</cmd>
You feel calm..."""
    
    result = generate_script("build confidence", api_key="test-key")
    
    assert isinstance(result, str)
    assert "<cmd" in result
    assert "</cmd>" in result


@patch('hypnogen.core.llm._call_api')
def test_generate_script_includes_goal_in_prompt(mock_call_api):
    """generate_script includes goal in the prompt sent to API."""
    from hypnogen.core.llm import generate_script
    
    mock_call_api.return_value = "Script content..."
    
    generate_script(goal="overcome anxiety", duration_minutes=15, api_key="test-key")
    
    # Check the messages passed to _call_api
    call_args = mock_call_api.call_args
    messages = call_args.args[0] if call_args.args else call_args.kwargs.get("messages")
    user_message = messages[0]["content"]
    
    assert "overcome anxiety" in user_message
    assert "15" in user_message  # duration


@patch('hypnogen.core.llm._call_api')
def test_generate_script_includes_style(mock_call_api):
    """generate_script includes style in the prompt."""
    from hypnogen.core.llm import generate_script
    
    mock_call_api.return_value = "Script content..."
    
    generate_script(goal="relaxation", style="permissive", api_key="test-key")
    
    call_args = mock_call_api.call_args
    messages = call_args.args[0] if call_args.args else call_args.kwargs.get("messages")
    user_message = messages[0]["content"]
    
    assert "permissive" in user_message


@patch('hypnogen.core.llm.get_api_key')
@patch('hypnogen.core.llm._call_api')
def test_generate_script_uses_env_key_if_not_provided(mock_call_api, mock_get_key):
    """generate_script uses environment API key when not provided."""
    from hypnogen.core.llm import generate_script
    
    mock_get_key.return_value = "env-api-key"
    mock_call_api.return_value = "Script..."
    
    generate_script(goal="relaxation")  # No api_key provided
    
    mock_get_key.assert_called_once()
    call_args = mock_call_api.call_args
    api_key_arg = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get("api_key")
    assert api_key_arg == "env-api-key"


# --- Test generate_affirmations ---

@patch('hypnogen.core.llm._call_api')
def test_generate_affirmations_returns_list(mock_call_api):
    """generate_affirmations returns a list of strings."""
    from hypnogen.core.llm import generate_affirmations
    
    mock_call_api.return_value = """I am confident
I feel calm
I embrace success
My mind is clear
I am strong"""
    
    result = generate_affirmations("build confidence", count=5, api_key="test-key")
    
    assert isinstance(result, list)
    assert len(result) == 5
    assert all(isinstance(s, str) for s in result)


@patch('hypnogen.core.llm._call_api')
def test_generate_affirmations_includes_goal_in_prompt(mock_call_api):
    """generate_affirmations includes goal in the prompt."""
    from hypnogen.core.llm import generate_affirmations
    
    mock_call_api.return_value = "I am calm"
    
    generate_affirmations(goal="reduce stress", count=10, api_key="test-key")
    
    call_args = mock_call_api.call_args
    messages = call_args.args[0] if call_args.args else call_args.kwargs.get("messages")
    user_message = messages[0]["content"]
    
    assert "reduce stress" in user_message
    assert "10" in user_message  # count


@patch('hypnogen.core.llm._call_api')
def test_generate_affirmations_filters_invalid(mock_call_api):
    """generate_affirmations filters out invalid affirmations."""
    from hypnogen.core.llm import generate_affirmations
    
    # Some invalid: too long, has negation
    mock_call_api.return_value = """I am confident and ready for success today always forever
I never give up
I am calm
I feel strong
I don't worry"""
    
    result = generate_affirmations("confidence", api_key="test-key")
    
    # Only valid affirmations should be returned
    assert "I am calm" in result
    assert "I feel strong" in result
    # Invalid ones should be filtered
    assert not any("never" in a.lower() for a in result)
    assert not any("don't" in a for a in result)


@patch('hypnogen.core.llm._call_api')
def test_generate_affirmations_strips_whitespace(mock_call_api):
    """generate_affirmations strips leading/trailing whitespace from each line."""
    from hypnogen.core.llm import generate_affirmations
    
    mock_call_api.return_value = """  I am calm  
  I feel strong  
"""
    
    result = generate_affirmations("relaxation", api_key="test-key")
    
    assert "I am calm" in result
    assert "I feel strong" in result
    # No leading/trailing spaces
    assert all(a == a.strip() for a in result)


@patch('hypnogen.core.llm._call_api')
def test_generate_affirmations_skips_empty_lines(mock_call_api):
    """generate_affirmations skips empty lines."""
    from hypnogen.core.llm import generate_affirmations
    
    mock_call_api.return_value = """I am calm

I feel strong

I embrace peace
"""
    
    result = generate_affirmations("relaxation", api_key="test-key")
    
    assert len(result) == 3
    assert "" not in result


@patch('hypnogen.core.llm.get_api_key')
@patch('hypnogen.core.llm._call_api')
def test_generate_affirmations_uses_env_key_if_not_provided(mock_call_api, mock_get_key):
    """generate_affirmations uses environment API key when not provided."""
    from hypnogen.core.llm import generate_affirmations
    
    mock_get_key.return_value = "env-key"
    mock_call_api.return_value = "I am calm"
    
    generate_affirmations(goal="calm")  # No api_key
    
    mock_get_key.assert_called_once()


# --- Integration: generate_affirmations uses validate_affirmation ---

@patch('hypnogen.core.llm._call_api')
def test_generate_affirmations_validates_with_swarm(mock_call_api):
    """generate_affirmations uses validate_affirmation from swarm module."""
    from hypnogen.core.llm import generate_affirmations
    from hypnogen.core.swarm import validate_affirmation
    
    # Return a mix of valid and invalid
    mock_call_api.return_value = """I was tired yesterday
I am calm
I will succeed tomorrow"""
    
    result = generate_affirmations("relaxation", api_key="test-key")
    
    # Only present-tense, valid affirmations
    assert "I am calm" in result
    # Past/future tense filtered
    assert not any("was" in a.lower() for a in result)
    assert not any("will" in a.lower() for a in result)


# --- Test LLMError exception ---

def test_llm_error_is_exception():
    """LLMError is a proper exception class."""
    from hypnogen.core.llm import LLMError
    
    assert issubclass(LLMError, Exception)
    
    error = LLMError("test message")
    assert str(error) == "test message"


# --- Test API URL constant ---

def test_nvidia_api_url_defined():
    """NVIDIA_API_URL constant is defined."""
    from hypnogen.core.llm import NVIDIA_API_URL
    
    assert NVIDIA_API_URL == "https://integrate.api.nvidia.com/v1/chat/completions"


def test_model_constant_defined():
    """MODEL constant is defined."""
    from hypnogen.core.llm import MODEL
    
    assert MODEL == "moonshotai/kimi-k2.5"
