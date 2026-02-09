import os

import httpx
from dotenv import load_dotenv

from hypnogen.core.swarm import validate_affirmation

load_dotenv()

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
KIMI_MODEL = "moonshotai/kimi-k2.5"

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_PRO_MODEL = "gemini-2.5-pro-preview-05-06"
GEMINI_FLASH_MODEL = "gemini-2.5-flash-preview-04-17"

AVAILABLE_MODELS = [
    ("Gemini Pro", "gemini-pro"),
    ("Gemini Flash", "gemini-flash"),
    ("Kimi K2.5 (NVIDIA)", "kimi"),
]


class LLMError(Exception):
    pass


def get_api_key(provider: str = "nvidia") -> str:
    if provider == "gemini":
        key = os.getenv("GEMINI_KEY")
        if not key:
            raise ValueError("GEMINI_KEY environment variable not set")
        return key
    else:
        key = os.getenv("NVIDIA_API_KEY")
        if not key:
            raise ValueError("NVIDIA_API_KEY environment variable not set")
        return key


def _call_gemini_api(
    messages: list[dict],
    api_key: str,
    model: str = GEMINI_PRO_MODEL,
    max_tokens: int = 16384,
    temperature: float = 1.0,
) -> str:
    url = f"{GEMINI_API_URL}/{model}:generateContent?key={api_key}"

    gemini_contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    payload = {
        "contents": gemini_contents,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
            "topP": 1.0,
        },
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=300.0,
        )
        response.raise_for_status()
    except Exception as e:
        raise LLMError(f"Gemini HTTP error: {e}") from e

    data = response.json()

    if "error" in data:
        raise LLMError(f"Gemini API error: {data['error']}")

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Gemini response format: {e}") from e


def _call_nvidia_api(
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
        "model": KIMI_MODEL,
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
            timeout=300.0,
        )
        response.raise_for_status()
    except Exception as e:
        raise LLMError(f"NVIDIA HTTP error: {e}") from e

    data = response.json()

    if "error" in data:
        raise LLMError(f"NVIDIA API error: {data['error']}")

    return data["choices"][0]["message"]["content"]


def _call_api_with_fallback(messages: list[dict]) -> str:
    errors = []

    # Try Gemini Pro first
    try:
        api_key = get_api_key("gemini")
        return _call_gemini_api(messages, api_key, model=GEMINI_PRO_MODEL)
    except Exception as e:
        errors.append(f"Gemini Pro: {e}")

    # Try Gemini Flash as second option
    try:
        api_key = get_api_key("gemini")
        return _call_gemini_api(messages, api_key, model=GEMINI_FLASH_MODEL)
    except Exception as e:
        errors.append(f"Gemini Flash: {e}")

    # Fall back to Kimi
    try:
        api_key = get_api_key("nvidia")
        return _call_nvidia_api(messages, api_key)
    except Exception as e:
        errors.append(f"Kimi: {e}")

    raise LLMError(f"All providers failed: {'; '.join(errors)}")


def generate_script(
    goal: str,
    duration_minutes: int = 10,
    style: str = "ericksonian",
    depth: str = "medium",
    command_density: str = "medium",
    focus_theme: str = "",
    custom_instructions: str = "",
) -> str:
    word_count = duration_minutes * 150

    # Map density to concrete guidance
    density_map = {
        "low": "Use embedded commands very sparingly — no more than 1 per 60 seconds of speech. Let the natural language do the work.",
        "medium": "Use embedded commands moderately — approximately 1 per 30 seconds of speech. Balance direct suggestion with natural flow.",
        "high": "Use embedded commands frequently — approximately 1 per 15-20 seconds of speech. Layer suggestions densely throughout.",
    }
    density_guidance = density_map.get(command_density, density_map["medium"])

    # Map depth to induction characteristics
    depth_map = {
        "light": (
            "Create a light, relaxing induction. Keep the subject aware and engaged. "
            "Use gentle, conversational language. Minimal fractionalization. "
            "Focus on calm alertness and focused relaxation."
        ),
        "medium": (
            "Create a moderately deep induction with gradual deepening. "
            "Include fractionalization (going deeper, coming up slightly, going deeper again). "
            "Use progressive relaxation and moderate pacing."
        ),
        "deep": (
            "Create a deeply immersive induction targeting profound trance. "
            "Use extensive fractionalization, countdown deepeners, and staircase/elevator metaphors. "
            "Slow pacing with long pauses. Layer multiple deepening techniques."
        ),
        "somnambulistic": (
            "Create an extremely deep somnambulistic induction. "
            "Use rapid induction followed by multiple deepening passes. "
            "Include amnesia suggestions, time distortion, and catalepsy markers. "
            "Very slow pacing with extended pauses between suggestions."
        ),
    }
    depth_guidance = depth_map.get(depth, depth_map["medium"])

    # Map style to tone guidance
    style_map = {
        "ericksonian": (
            "Use Ericksonian indirect hypnosis techniques: embedded commands, presuppositions, "
            "double binds, metaphors, and stories. Avoid direct commands — instead, use "
            "'you might notice...', 'I wonder if...', 'and as you...'"
        ),
        "permissive": (
            "Use a permissive, gentle approach. Offer suggestions rather than commands. "
            "'You may find...', 'Perhaps you'll notice...', 'Allow yourself to...'. "
            "Give the subject full agency and choice in every suggestion."
        ),
        "authoritative": (
            "Use a confident, direct authoritative style. Clear, firm commands delivered warmly. "
            "'Now relax your body completely.', 'Feel the tension leaving.', 'Go deeper now.' "
            "Be commanding but never harsh."
        ),
        "conversational": (
            "Use a natural, conversational tone as if talking to a close friend. "
            "Weave suggestions into casual storytelling and anecdotes. "
            "Make it feel like a comfortable, meandering conversation that happens to be deeply relaxing."
        ),
        "fractionation": (
            "Use a FRACTIONATION-HEAVY induction style. Fractionation means repeatedly bringing the subject "
            "UP slightly and then dropping them DEEPER. This creates a ratchet effect where each drop goes deeper "
            "than before. Structure the script around cycles of:\n"
            "1. Brief alerting ('Opening your eyes for a moment...') followed by immediate re-induction ('And closing them now... dropping DEEPER')\n"
            "2. Use verbal drop cues throughout with the <drop>word</drop> tag. Examples:\n"
            "   - <drop>drop</drop> — a sharp, commanding drop cue\n"
            "   - <drop>sleep</drop> — a softer drop cue\n"
            "   - <drop>down</drop> — a directional drop cue\n"
            "3. Use <snap/> tags to insert crisp finger-snap sounds before or after drop cues:\n"
            "   - <snap/> <drop>drop</drop> — snap then drop\n"
            "   - <snap/> <pause duration=\"500ms\"/> <drop>sleep</drop> — snap, pause, then sleep cue\n"
            "4. Include rapid countdowns with drops: 'Three... two... one... <snap/> <drop>drop</drop>'\n"
            "5. Use at least 5-8 fractionation cycles in the script\n"
            "6. Each drop should be followed by deepening language and a pause for the subject to settle\n"
            "7. Vary the drop cue words: alternate between 'drop', 'sleep', 'down', 'deeper', 'let go'\n"
            "Be commanding but warm. The drops should feel safe and inviting, not aggressive."
        ),
    }
    style_guidance = style_map.get(style, style_map["ericksonian"])

    # Build optional sections
    focus_section = ""
    if focus_theme:
        focus_section = f"\nTheme/Focus: {focus_theme}\nWeave this theme naturally throughout the script as a central metaphor or recurring motif.\n"

    custom_section = ""
    if custom_instructions:
        custom_section = f"\nAdditional Instructions from User:\n{custom_instructions}\nHonor these instructions while maintaining hypnotic flow.\n"

    prompt = f"""You are an expert hypnotherapist and master of trance language patterns.

GOAL: {goal}
TARGET DURATION: {duration_minutes} minutes (approximately {word_count} words)
{focus_section}{custom_section}
STYLE GUIDANCE:
{style_guidance}

DEPTH GUIDANCE:
{depth_guidance}

EMBEDDED COMMANDS:
{density_guidance}
Mark embedded commands with <cmd pitch="-2" rate="0.9">command text</cmd>
You may vary pitch (-1 to -3) and rate (0.8 to 1.0) for natural variation.

STRUCTURE REQUIREMENTS:
1. Opening: Begin with a guided breathing exercise — at least 3 deep inhales and exhales with <pause duration="3000ms"/> between each breath cycle so the subject can actually follow along. Establish rapport and set expectations.
2. Induction: Guide into trance using techniques appropriate to the depth level
3. Deepening: Use fractionalization and deepeners appropriate to the depth
4. Therapeutic Content: Address the goal with suggestions, metaphors, and embedded commands
5. Future Pacing: Help the subject imagine using these changes in daily life
6. Emergence: Bring back to full alertness with positive suggestions

PACING RULES (CRITICAL — this audio will be read aloud by TTS):
- Countdowns MUST have a <pause duration="1500ms"/> between each number. Example:
  Ten... <pause duration="1500ms"/> nine... <pause duration="1500ms"/> eight... <pause duration="1500ms"/>
  Never write countdowns as a continuous run like "ten... nine... eight..."
- Breathing cues MUST have pauses long enough for the subject to actually breathe:
  Breathe in deeply now... <pause duration="3000ms"/> and exhale slowly... <pause duration="3000ms"/>
  Use 2000ms-4000ms for breath pauses — real breathing takes time.
- After any instruction that asks the subject to DO something (close eyes, relax muscles, visualize), add at least <pause duration="1500ms"/> so they can comply.
- Fractionalization transitions ("floating up... dropping deeper") need <pause duration="1000ms"/> at each shift.
- Between major sections, use <pause duration="2000ms"/> to let suggestions settle.

FORMATTING RULES:
- Use ellipses (...) for natural speech pauses within phrases
- Use <pause duration="500ms"/> for short dramatic pauses
- Use <pause duration="1000ms"/> between sentences that need breathing room
- Use <pause duration="1500ms"/> to <pause duration="4000ms"/> for countdowns, breathing, and action compliance
- Use <snap/> to insert a crisp finger-snap sound (fractionation style only)
- Use <drop>word</drop> to insert a pitch-shifted drop cue with snap overlay, where word is "drop", "sleep", "down", etc. (fractionation style only)
- Each paragraph should flow naturally when read aloud
- No numbered lists, headers, or markdown — just flowing script text

Return ONLY the script text. No explanations, titles, or metadata."""

    messages = [{"role": "user", "content": prompt}]
    return _call_api_with_fallback(messages)


def generate_affirmations(
    goal: str,
    count: int = 20,
) -> list[str]:
    prompt = f"""Generate {count} powerful affirmations for this goal: {goal}

Rules for each affirmation:
1. Maximum 7 words
2. Present tense only (I am, I have, I feel)
3. No negations (no "not", "never", "don't")
4. First person (I, My, Me)
5. Positive and empowering

Return one affirmation per line, nothing else."""

    messages = [{"role": "user", "content": prompt}]
    response = _call_api_with_fallback(messages)

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
