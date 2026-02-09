"""Tests for README documentation."""
import os


def test_readme_exists():
    """README.md should exist in repo root."""
    assert os.path.exists('README.md'), "README.md not found in repo root"


def test_readme_has_required_sections():
    """README.md should contain disclaimer, minors, and consent."""
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read().lower()
    assert 'disclaimer' in content, "README missing 'disclaimer' section"
    assert 'minors' in content, "README missing 'minors' reference"
    assert 'consent' in content, "README missing 'consent' reference"


def test_readme_has_quickstart():
    """README.md should contain quickstart instructions."""
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'pytest' in content, "README missing test instructions"
    assert 'pip install' in content.lower(), "README missing install instructions"
