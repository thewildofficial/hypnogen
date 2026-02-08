"""Script parser for hypnotic scripts with XML-style tags."""
import re
from typing import Any


def parse_script(text: str) -> list[dict[str, Any]]:
    """Parse hypnotic script text into segments.
    
    Extracts text, command tags, and pause markers from scripts.
    
    Args:
        text: Script text with optional XML-style tags
        
    Returns:
        List of segment dictionaries with type and type-specific fields:
        - text segments: {"type": "text", "text": str}
        - command segments: {"type": "command", "text": str, "pitch": float, "rate": float}
        - pause segments: {"type": "pause", "duration_ms": int}
        
    Raises:
        ValueError: If nested tags are detected
        
    Example:
        >>> parse_script('Hello <cmd pitch="-2">world</cmd>')
        [
            {"type": "text", "text": "Hello"},
            {"type": "command", "text": "world", "pitch": -2.0, "rate": 1.0}
        ]
    """
    if not text:
        return []
    
    # Check for nested tags
    if _has_nested_tags(text):
        raise ValueError("Nested tags are not supported")
    
    segments: list[dict[str, Any]] = []
    position = 0
    
    # Pattern to match cmd tags or pause tags
    tag_pattern = re.compile(
        r'<(cmd|pause)\s*([^>]*?)(?:/>|>(.*?)</\1>)',
        re.DOTALL
    )
    
    for match in tag_pattern.finditer(text):
        # Add text before the tag
        text_before = text[position:match.start()].strip()
        if text_before:
            segments.append({"type": "text", "text": text_before})
        
        tag_name = match.group(1)
        attributes = match.group(2)
        content = match.group(3) if match.group(3) is not None else ""
        
        if tag_name == "cmd":
            segments.append(_parse_cmd_tag(attributes, content))
        elif tag_name == "pause":
            segments.append(_parse_pause_tag(attributes))
        
        position = match.end()
    
    # Add remaining text after last tag
    text_after = text[position:].strip()
    if text_after:
        segments.append({"type": "text", "text": text_after})
    
    return segments


def _has_nested_tags(text: str) -> bool:
    """Check if text contains nested tags."""
    # Look for opening tag followed by another opening tag before closing
    nested_pattern = re.compile(r'<(cmd|pause)[^>]*>.*?<(cmd|pause)', re.DOTALL)
    match = nested_pattern.search(text)
    if match:
        # Verify it's actually nested (not sequential)
        # Check if there's a closing tag between the two opening tags
        between_start = match.start()
        between_end = match.end()
        between_text = text[between_start:between_end]
        # If we find < tag without a closing tag first, it's nested
        if '<' in between_text[1:]:
            # Find the first tag's closing position
            first_tag = match.group(1)
            closing_pattern = re.compile(f'</{first_tag}>')
            first_close = closing_pattern.search(text[between_start:])
            if first_close:
                # Check if second opening tag comes before first closing tag
                second_open_pos = between_text[1:].find('<')
                if second_open_pos != -1 and second_open_pos + 1 < first_close.start():
                    return True
    return False


def _parse_cmd_tag(attributes: str, content: str) -> dict[str, Any]:
    """Parse command tag attributes and content."""
    pitch = 0.0
    rate = 1.0
    
    # Extract pitch attribute
    pitch_match = re.search(r'pitch\s*=\s*["\']?(-?\d+(?:\.\d+)?)["\']?', attributes)
    if pitch_match:
        pitch = float(pitch_match.group(1))
    
    # Extract rate attribute
    rate_match = re.search(r'rate\s*=\s*["\']?(\d+(?:\.\d+)?)["\']?', attributes)
    if rate_match:
        rate = float(rate_match.group(1))
    
    return {
        "type": "command",
        "text": content.strip(),
        "pitch": pitch,
        "rate": rate,
    }


def _parse_pause_tag(attributes: str) -> dict[str, Any]:
    """Parse pause tag duration attribute."""
    # Extract duration attribute
    duration_match = re.search(
        r'duration\s*=\s*["\']?(\d+(?:\.\d+)?)(ms|s)["\']?',
        attributes
    )
    
    if not duration_match:
        raise ValueError("Pause tag missing duration attribute")
    
    value = float(duration_match.group(1))
    unit = duration_match.group(2)
    
    if unit == "s":
        duration_ms = int(value * 1000)
    else:  # ms
        duration_ms = int(value)
    
    return {
        "type": "pause",
        "duration_ms": duration_ms,
    }


def validate_marking_density(
    segments: list[dict[str, Any]],
    words_per_second: float = 2.5,
    max_density: float = 1 / 20,
) -> tuple[bool, str]:
    """Validate that analog-marked commands don't exceed density threshold.
    
    Enforces the rule: no more than 1 analog-marked command per 20-30 seconds
    of audio. This prevents over-reliance on analog marking which can create
    a new parsing channel the brain adapts to.
    
    Args:
        segments: Output from parse_script() - list of segment dicts
        words_per_second: Average speaking rate for duration estimation (default 2.5 wps)
        max_density: Maximum marked commands per second (default 1/20 = one per 20s)
        
    Returns:
        (True, "OK") if valid, (False, "warning: ...") if exceeding density
        
    Notes:
        - A command is "analog-marked" if pitch != 0.0 OR rate != 1.0
        - Commands with both defaults (pitch=0, rate=1.0) are NOT marked
        - Estimates duration by counting all words in text and command segments
        - This is a warning, not a hard error
        
    Example:
        >>> segments = [
        ...     {"type": "text", "text": "hello world"},
        ...     {"type": "command", "text": "relax", "pitch": -2.0, "rate": 1.0}
        ... ]
        >>> validate_marking_density(segments)
        (True, "OK")
    """
    if not segments:
        return (True, "OK")
    
    # Count total words for duration estimation
    total_words = 0
    for segment in segments:
        if segment["type"] == "text":
            total_words += len(segment["text"].split())
        elif segment["type"] == "command":
            total_words += len(segment["text"].split())
    
    # Count analog-marked commands (pitch != 0.0 OR rate != 1.0)
    marked_count = 0
    for segment in segments:
        if segment["type"] == "command":
            pitch = segment.get("pitch", 0.0)
            rate = segment.get("rate", 1.0)
            if pitch != 0.0 or rate != 1.0:
                marked_count += 1
    
    # If no words or no marked commands, always valid
    if total_words == 0 or marked_count == 0:
        return (True, "OK")
    
    # Estimate duration and check density
    estimated_duration = total_words / words_per_second
    actual_density = marked_count / estimated_duration
    
    if actual_density > max_density:
        return (
            False,
            f"warning: {marked_count} analog-marked commands in ~{estimated_duration:.0f}s "
            f"(density {actual_density:.3f}/s exceeds max {max_density:.3f}/s)",
        )
    
    return (True, "OK")
