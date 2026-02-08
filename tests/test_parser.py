"""Tests for script parser."""
import pytest
from hypnogen.core.parser import parse_script


def test_empty_string_returns_empty_list():
    """Empty input should return empty list."""
    result = parse_script("")
    assert result == []


def test_plain_text_no_tags():
    """Plain text with no tags should return single text segment."""
    result = parse_script("Hello world")
    assert result == [{"type": "text", "text": "Hello world"}]


def test_text_with_leading_trailing_whitespace():
    """Text segments should have leading/trailing whitespace stripped."""
    result = parse_script("  Hello world  ")
    assert result == [{"type": "text", "text": "Hello world"}]


def test_single_cmd_tag_no_attributes():
    """Command tag with no attributes should use defaults."""
    result = parse_script("Before <cmd>relax deeper</cmd> after")
    assert result == [
        {"type": "text", "text": "Before"},
        {"type": "command", "text": "relax deeper", "pitch": 0.0, "rate": 1.0},
        {"type": "text", "text": "after"},
    ]


def test_cmd_tag_with_pitch_and_rate():
    """Command tag with pitch and rate attributes."""
    result = parse_script('<cmd pitch="-2" rate="0.9">feel confident</cmd>')
    assert result == [
        {"type": "command", "text": "feel confident", "pitch": -2.0, "rate": 0.9},
    ]


def test_cmd_tag_with_only_pitch():
    """Command tag with only pitch attribute should default rate to 1.0."""
    result = parse_script('<cmd pitch="1.5">higher</cmd>')
    assert result == [
        {"type": "command", "text": "higher", "pitch": 1.5, "rate": 1.0},
    ]


def test_cmd_tag_with_only_rate():
    """Command tag with only rate attribute should default pitch to 0.0."""
    result = parse_script('<cmd rate="0.8">slower</cmd>')
    assert result == [
        {"type": "command", "text": "slower", "pitch": 0.0, "rate": 0.8},
    ]


def test_pause_tag_milliseconds():
    """Pause tag with milliseconds duration."""
    result = parse_script('<pause duration="500ms"/>')
    assert result == [
        {"type": "pause", "duration_ms": 500},
    ]


def test_pause_tag_seconds():
    """Pause tag with seconds duration."""
    result = parse_script('<pause duration="2s"/>')
    assert result == [
        {"type": "pause", "duration_ms": 2000},
    ]


def test_pause_tag_with_closing_tag():
    """Pause tag can also use closing tag format."""
    result = parse_script('<pause duration="1s"></pause>')
    assert result == [
        {"type": "pause", "duration_ms": 1000},
    ]


def test_mixed_text_commands_and_pauses():
    """Complex script with text, commands, and pauses."""
    script = (
        "And as you listen to my voice... "
        '<cmd pitch="-2" rate="0.9">feel confident</cmd>... '
        'you can begin to notice <pause duration="500ms"/> how naturally '
        '<cmd>relax deeper</cmd> with each breath.'
    )
    result = parse_script(script)
    assert result == [
        {"type": "text", "text": "And as you listen to my voice..."},
        {"type": "command", "text": "feel confident", "pitch": -2.0, "rate": 0.9},
        {"type": "text", "text": "... you can begin to notice"},
        {"type": "pause", "duration_ms": 500},
        {"type": "text", "text": "how naturally"},
        {"type": "command", "text": "relax deeper", "pitch": 0.0, "rate": 1.0},
        {"type": "text", "text": "with each breath."},
    ]


def test_nested_tags_raise_error():
    """Nested command tags should raise ValueError."""
    with pytest.raises(ValueError, match="Nested tags are not supported"):
        parse_script("<cmd>outer <cmd>inner</cmd></cmd>")


def test_whitespace_only_segments_skipped():
    """Segments with only whitespace should be skipped."""
    result = parse_script("Hello   <cmd>world</cmd>   there")
    assert result == [
        {"type": "text", "text": "Hello"},
        {"type": "command", "text": "world", "pitch": 0.0, "rate": 1.0},
        {"type": "text", "text": "there"},
    ]


def test_newlines_preserved_in_text():
    """Internal whitespace including newlines should be preserved."""
    result = parse_script("Line 1\nLine 2\n<cmd>command</cmd>\nLine 3")
    assert result == [
        {"type": "text", "text": "Line 1\nLine 2"},
        {"type": "command", "text": "command", "pitch": 0.0, "rate": 1.0},
        {"type": "text", "text": "Line 3"},
    ]


def test_multiple_pauses_in_sequence():
    """Multiple pause tags in sequence."""
    result = parse_script(
        '<pause duration="100ms"/><pause duration="200ms"/><pause duration="300ms"/>'
    )
    assert result == [
        {"type": "pause", "duration_ms": 100},
        {"type": "pause", "duration_ms": 200},
        {"type": "pause", "duration_ms": 300},
    ]


def test_cmd_tag_with_single_quotes():
    """Command tag attributes can use single quotes."""
    result = parse_script("<cmd pitch='-1' rate='1.2'>text</cmd>")
    assert result == [
        {"type": "command", "text": "text", "pitch": -1.0, "rate": 1.2},
    ]


def test_pause_duration_without_quotes():
    """Pause duration can be specified without quotes."""
    result = parse_script("<pause duration=500ms/>")
    assert result == [
        {"type": "pause", "duration_ms": 500},
    ]


# Marking density validation tests
def test_validate_marking_density_zero_marked_commands():
    """Script with no marked commands should be valid."""
    from hypnogen.core.parser import validate_marking_density
    
    segments = [
        {"type": "text", "text": "You are calm and confident"},
        {"type": "command", "text": "relax", "pitch": 0.0, "rate": 1.0},  # Not marked (defaults)
        {"type": "text", "text": "feeling peaceful"},
    ]
    
    valid, message = validate_marking_density(segments)
    assert valid is True
    assert message == "OK"


def test_validate_marking_density_one_marked_in_60s():
    """Script with 1 marked command in 60s of text should be valid."""
    from hypnogen.core.parser import validate_marking_density
    
    # 2.5 words/sec * 60 sec = 150 words
    long_text = " ".join(["word"] * 150)
    segments = [
        {"type": "text", "text": long_text},
        {"type": "command", "text": "relax", "pitch": -2.0, "rate": 1.0},  # Marked (pitch != 0)
    ]
    
    valid, message = validate_marking_density(segments, words_per_second=2.5, max_density=1/20)
    assert valid is True
    assert message == "OK"


def test_validate_marking_density_three_marked_in_30s():
    """Script with 3 marked commands in 30s of text should be invalid."""
    from hypnogen.core.parser import validate_marking_density
    
    # 2.5 words/sec * 30 sec = 75 words
    text = " ".join(["word"] * 75)
    segments = [
        {"type": "text", "text": text},
        {"type": "command", "text": "relax", "pitch": -2.0, "rate": 1.0},  # Marked
        {"type": "command", "text": "sleep", "pitch": -3.0, "rate": 0.9},  # Marked
        {"type": "command", "text": "calm", "pitch": 0.0, "rate": 0.8},    # Marked (rate != 1.0)
    ]
    
    valid, message = validate_marking_density(segments, words_per_second=2.5, max_density=1/20)
    assert valid is False
    assert "warning" in message.lower()
    assert "3" in message  # Should mention the count
    assert "30" in message or "density" in message.lower()


def test_validate_marking_density_pitch_shift_only():
    """Commands with only pitch shift should count as marked."""
    from hypnogen.core.parser import validate_marking_density
    
    # 2.5 words/sec * 10 sec = 25 words
    text = " ".join(["word"] * 25)
    segments = [
        {"type": "text", "text": text},
        {"type": "command", "text": "relax", "pitch": -2.0, "rate": 1.0},  # Marked (pitch only)
        {"type": "command", "text": "sleep", "pitch": 1.5, "rate": 1.0},   # Marked (pitch only)
    ]
    
    # 2 marked commands in 10s = 0.2 per second > 0.05 (1/20)
    valid, message = validate_marking_density(segments, words_per_second=2.5, max_density=1/20)
    assert valid is False
    assert "warning" in message.lower()


def test_validate_marking_density_rate_change_only():
    """Commands with only rate change should count as marked."""
    from hypnogen.core.parser import validate_marking_density
    
    # 2.5 words/sec * 10 sec = 25 words
    text = " ".join(["word"] * 25)
    segments = [
        {"type": "text", "text": text},
        {"type": "command", "text": "relax", "pitch": 0.0, "rate": 0.9},  # Marked (rate only)
        {"type": "command", "text": "sleep", "pitch": 0.0, "rate": 0.8},  # Marked (rate only)
    ]
    
    # 2 marked commands in 10s = 0.2 per second > 0.05 (1/20)
    valid, message = validate_marking_density(segments, words_per_second=2.5, max_density=1/20)
    assert valid is False
    assert "warning" in message.lower()


def test_validate_marking_density_defaults_not_marked():
    """Commands with both defaults (pitch=0, rate=1.0) should NOT count as marked."""
    from hypnogen.core.parser import validate_marking_density
    
    # 2.5 words/sec * 10 sec = 25 words
    text = " ".join(["word"] * 25)
    segments = [
        {"type": "text", "text": text},
        {"type": "command", "text": "relax", "pitch": 0.0, "rate": 1.0},  # NOT marked
        {"type": "command", "text": "sleep", "pitch": 0.0, "rate": 1.0},  # NOT marked
    ]
    
    valid, message = validate_marking_density(segments, words_per_second=2.5)
    assert valid is True
    assert message == "OK"


def test_validate_marking_density_empty_segments():
    """Empty segments list should be valid."""
    from hypnogen.core.parser import validate_marking_density
    
    valid, message = validate_marking_density([])
    assert valid is True
    assert message == "OK"


def test_validate_marking_density_all_plain_text():
    """Script with only plain text should be valid."""
    from hypnogen.core.parser import validate_marking_density
    
    segments = [
        {"type": "text", "text": "You are calm and confident"},
        {"type": "text", "text": "feeling peaceful and relaxed"},
    ]
    
    valid, message = validate_marking_density(segments)
    assert valid is True
    assert message == "OK"
