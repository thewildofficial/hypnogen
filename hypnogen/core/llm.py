import os

import httpx
from dotenv import load_dotenv

from hypnogen.core.swarm import validate_affirmation

load_dotenv()

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "moonshotai/kimi-k2.5"


class LLMError(Exception):
    pass


def get_api_key() -> str:
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        raise ValueError("NVIDIA_API_KEY environment variable not set")
    return key


def _call_api(
    messages: list[dict],
    api_key: str,
    stream: bool = False,
    max_tokens: int = 16384,
    temperature: float = 1.0,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1.00,
        "stream": stream,
        "chat_template_kwargs": {"thinking": True},
    }

    try:
        response = httpx.post(
            NVIDIA_API_URL,
            headers=headers,
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
    except Exception as e:
        raise LLMError(f"HTTP error: {e}") from e

    data = response.json()

    if "error" in data:
        raise LLMError(f"API error: {data['error']}")

    return data["choices"][0]["message"]["content"]


def generate_script(
    goal: str,
    duration_minutes: int = 10,
    style: str = "ericksonian",
    api_key: str | None = None,
) -> str:
    if api_key is None:
        api_key = get_api_key()

    word_count = duration_minutes * 150

    prompt = f"""You are an expert hypnotherapist creating an Ericksonian hypnosis script.

Goal: {goal}
Duration: {duration_minutes} minutes (approximately {word_count} words)
Style: {style}

Generate a hypnotic induction script with these requirements:
1. Use ellipses (...) for natural pauses in speech
2. Mark embedded commands with <cmd pitch="-2" rate="0.9">command here</cmd>
3. Add <pause duration="500ms"/> for longer pauses
4. Include fractionalization (going deeper, coming up slightly, going deeper again)
5. Use embedded commands sparingly (max 1 per 30 seconds of speech)
6. End with a proper emergence/awakening sequence

Return ONLY the script text, no explanations or metadata."""

    messages = [{"role": "user", "content": prompt}]
    return _call_api(messages, api_key)


def generate_affirmations(
    goal: str,
    count: int = 20,
    api_key: str | None = None,
) -> list[str]:
    if api_key is None:
        api_key = get_api_key()

    prompt = f"""Generate {count} powerful affirmations for this goal: {goal}

Rules for each affirmation:
1. Maximum 7 words
2. Present tense only (I am, I have, I feel)
3. No negations (no "not", "never", "don't")
4. First person (I, My, Me)
5. Positive and empowering

Return one affirmation per line, nothing else."""

    messages = [{"role": "user", "content": prompt}]
    response = _call_api(messages, api_key)

    lines = response.strip().split("\n")
    affirmations = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        valid, _ = validate_affirmation(stripped)
        if valid:
            affirmations.append(stripped)

    return affirmations
