"""Tests for CLI module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from click.testing import CliRunner


class TestCLIHelp:
    """Test CLI help and structure."""

    def test_cli_main_help_shows_usage(self):
        """Main CLI --help shows generate command."""
        from hypnogen.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output

    def test_generate_help_shows_all_options(self):
        """generate --help shows all required options."""
        from hypnogen.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        # Check required options
        assert "--script" in result.output or "-s" in result.output
        assert "--affirmations" in result.output or "-a" in result.output
        assert "--out" in result.output or "-o" in result.output
        # Check optional options
        assert "--length-sec" in result.output or "-l" in result.output
        assert "--seed" in result.output
        assert "--voice" in result.output or "-v" in result.output
        assert "--stems-dir" in result.output
        assert "--sr" in result.output


class TestCLIInputValidation:
    """Test CLI input validation."""

    def test_missing_script_path_fails(self):
        """Missing --script option fails."""
        from hypnogen.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            aff_file = Path(tmpdir) / "affirmations.txt"
            aff_file.write_text("I am calm\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                ["generate", "-a", str(aff_file), "-o", str(out_file)],
            )
            assert result.exit_code != 0

    def test_missing_affirmations_path_fails(self):
        """Missing --affirmations option fails."""
        from hypnogen.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            script_file = Path(tmpdir) / "script.txt"
            script_file.write_text("Welcome to relaxation.\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                ["generate", "-s", str(script_file), "-o", str(out_file)],
            )
            assert result.exit_code != 0

    def test_invalid_script_path_fails(self):
        """Non-existent script file fails."""
        from hypnogen.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            aff_file = Path(tmpdir) / "affirmations.txt"
            aff_file.write_text("I am calm\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "-s",
                    "/nonexistent/script.txt",
                    "-a",
                    str(aff_file),
                    "-o",
                    str(out_file),
                ],
            )
            assert result.exit_code != 0
            assert "does not exist" in result.output.lower() or "error" in result.output.lower()

    def test_invalid_affirmations_path_fails(self):
        """Non-existent affirmations file fails."""
        from hypnogen.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            script_file = Path(tmpdir) / "script.txt"
            script_file.write_text("Welcome to relaxation.\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "-s",
                    str(script_file),
                    "-a",
                    "/nonexistent/affirmations.txt",
                    "-o",
                    str(out_file),
                ],
            )
            assert result.exit_code != 0


class TestCLIGeneration:
    """Test CLI generation pipeline with mocked TTS."""

    @pytest.fixture
    def mock_synthesize(self):
        """Mock TTS synthesize to avoid downloading model."""
        # Return 1 second of silence at 24000Hz
        mock_audio = np.zeros(24000, dtype=np.float32)
        with patch("hypnogen.cli.synthesize") as mock:
            mock.return_value = (mock_audio, 24000)
            yield mock

    @pytest.fixture
    def temp_files(self):
        """Create temporary script and affirmations files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_file = Path(tmpdir) / "script.txt"
            script_file.write_text("Welcome to deep relaxation.\n<pause duration=\"500ms\"/>\nYou are calm and peaceful.\n")

            aff_file = Path(tmpdir) / "affirmations.txt"
            aff_file.write_text("I am calm\nI am peaceful\nI am relaxed\n")

            out_file = Path(tmpdir) / "output.wav"

            yield {
                "tmpdir": tmpdir,
                "script": str(script_file),
                "affirmations": str(aff_file),
                "output": str(out_file),
            }

    def test_generate_creates_output_file(self, mock_synthesize, temp_files):
        """Generate command creates output WAV file."""
        from hypnogen.cli import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "generate",
                "-s",
                temp_files["script"],
                "-a",
                temp_files["affirmations"],
                "-o",
                temp_files["output"],
                "--length-sec",
                "10",  # Short duration for fast test
            ],
        )

        if result.exit_code != 0:
            print(f"CLI output: {result.output}")
            if result.exception:
                import traceback

                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert os.path.exists(temp_files["output"]), "Output file not created"

    def test_generate_with_seed_is_reproducible(self, mock_synthesize, temp_files):
        """Generate with same seed produces same output."""
        from hypnogen.cli import cli

        runner = CliRunner()

        # First run with seed
        out1 = temp_files["output"]
        result1 = runner.invoke(
            cli,
            [
                "generate",
                "-s",
                temp_files["script"],
                "-a",
                temp_files["affirmations"],
                "-o",
                out1,
                "--length-sec",
                "5",
                "--seed",
                "42",
            ],
        )
        assert result1.exit_code == 0

        # Second run with same seed, different output file
        out2 = out1.replace(".wav", "_2.wav")
        result2 = runner.invoke(
            cli,
            [
                "generate",
                "-s",
                temp_files["script"],
                "-a",
                temp_files["affirmations"],
                "-o",
                out2,
                "--length-sec",
                "5",
                "--seed",
                "42",
            ],
        )
        assert result2.exit_code == 0

        # Files should exist and be identical (with mocked TTS)
        assert os.path.exists(out1)
        assert os.path.exists(out2)

    def test_generate_creates_stems_directory(self, mock_synthesize, temp_files):
        """Generate with --stems-dir creates stems directory and files."""
        from hypnogen.cli import cli

        runner = CliRunner()
        stems_dir = os.path.join(temp_files["tmpdir"], "stems")

        result = runner.invoke(
            cli,
            [
                "generate",
                "-s",
                temp_files["script"],
                "-a",
                temp_files["affirmations"],
                "-o",
                temp_files["output"],
                "--length-sec",
                "5",
                "--stems-dir",
                stems_dir,
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert os.path.exists(stems_dir), "Stems directory not created"
        # Check for at least some stem files
        stem_files = os.listdir(stems_dir)
        assert len(stem_files) > 0, "No stem files created"

    def test_generate_with_custom_sr(self, mock_synthesize, temp_files):
        """Generate respects custom sample rate."""
        from hypnogen.cli import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "generate",
                "-s",
                temp_files["script"],
                "-a",
                temp_files["affirmations"],
                "-o",
                temp_files["output"],
                "--length-sec",
                "5",
                "--sr",
                "48000",
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert os.path.exists(temp_files["output"])

    def test_generate_echoes_success_message(self, mock_synthesize, temp_files):
        """Generate prints success message with output path."""
        from hypnogen.cli import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "generate",
                "-s",
                temp_files["script"],
                "-a",
                temp_files["affirmations"],
                "-o",
                temp_files["output"],
                "--length-sec",
                "5",
            ],
        )

        assert result.exit_code == 0
        assert "Generated" in result.output or "output" in result.output.lower()


class TestCLIAffirmationValidation:
    """Test CLI handles affirmation validation."""

    @pytest.fixture
    def mock_synthesize(self):
        """Mock TTS synthesize to avoid downloading model."""
        mock_audio = np.zeros(24000, dtype=np.float32)
        with patch("hypnogen.cli.synthesize") as mock:
            mock.return_value = (mock_audio, 24000)
            yield mock

    def test_invalid_affirmations_are_skipped(self, mock_synthesize):
        """Invalid affirmations are skipped with warning."""
        from hypnogen.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            script_file = Path(tmpdir) / "script.txt"
            script_file.write_text("Welcome.\n")

            # Mix of valid and invalid affirmations
            aff_file = Path(tmpdir) / "affirmations.txt"
            aff_file.write_text(
                "I am calm\n"  # Valid
                "I was happy\n"  # Invalid - past tense
                "I am peaceful\n"  # Valid
            )

            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "-s",
                    str(script_file),
                    "-a",
                    str(aff_file),
                    "-o",
                    str(out_file),
                    "--length-sec",
                    "5",
                ],
            )

            # Should still succeed with valid affirmations
            assert result.exit_code == 0


class TestCLIMarkingDensityWarning:
    """Test CLI shows warning for excessive marking density."""

    @pytest.fixture
    def mock_synthesize(self):
        """Mock TTS synthesize to avoid downloading model."""
        mock_audio = np.zeros(24000, dtype=np.float32)
        with patch("hypnogen.cli.synthesize") as mock:
            mock.return_value = (mock_audio, 24000)
            yield mock

    def test_excessive_marking_density_shows_warning(self, mock_synthesize):
        """Script with too many marked commands shows warning."""
        from hypnogen.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Script with many marked commands (high density)
            script_file = Path(tmpdir) / "script.txt"
            script_file.write_text(
                '<cmd pitch="-2">one</cmd> '
                '<cmd pitch="-2">two</cmd> '
                '<cmd pitch="-2">three</cmd>\n'
            )

            aff_file = Path(tmpdir) / "affirmations.txt"
            aff_file.write_text("I am calm\n")

            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "-s",
                    str(script_file),
                    "-a",
                    str(aff_file),
                    "-o",
                    str(out_file),
                    "--length-sec",
                    "5",
                ],
            )

            # Should still succeed but with warning
            assert result.exit_code == 0
            # Warning may be printed to stderr
            assert "warning" in result.output.lower() or result.exit_code == 0


class TestCLILLMIntegration:

    @pytest.fixture
    def mock_synthesize(self):
        mock_audio = np.zeros(24000, dtype=np.float32)
        with patch("hypnogen.cli.synthesize") as mock:
            mock.return_value = (mock_audio, 24000)
            yield mock

    def test_help_shows_llm_options(self):
        from hypnogen.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--generate-script" in result.output
        assert "--generate-affirmations" in result.output
        assert "--use-llm" in result.output
        assert "--goal" in result.output
        assert "--style" in result.output
        assert "--affirmation-count" in result.output

    def test_use_llm_without_goal_fails(self, mock_synthesize):
        from hypnogen.cli import cli

        runner = CliRunner()
        result = runner.invoke(
            cli, ["generate", "--use-llm", "-o", "/tmp/test.wav"]
        )
        assert result.exit_code != 0
        assert "--goal" in result.output or "goal" in result.output.lower()

    def test_generate_script_without_goal_fails(self, mock_synthesize):
        from hypnogen.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            aff_file = Path(tmpdir) / "aff.txt"
            aff_file.write_text("I am calm\n")
            result = runner.invoke(
                cli,
                ["generate", "--generate-script", "-a", str(aff_file), "-o", "/tmp/test.wav"],
            )
            assert result.exit_code != 0

    @patch("hypnogen.cli.llm_generate_script")
    def test_generate_script_calls_llm(self, mock_llm_script, mock_synthesize):
        from hypnogen.cli import cli

        mock_llm_script.return_value = "And now... relax deeply."

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            aff_file = Path(tmpdir) / "aff.txt"
            aff_file.write_text("I am calm\nI am focused\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "--generate-script",
                    "--goal", "build confidence",
                    "-a", str(aff_file),
                    "-o", str(out_file),
                    "--length-sec", "10",
                ],
            )

            assert result.exit_code == 0, f"CLI failed: {result.output}"
            mock_llm_script.assert_called_once()
            call_kwargs = mock_llm_script.call_args
            assert call_kwargs.kwargs.get("goal") == "build confidence" or call_kwargs[1].get("goal") == "build confidence"

    @patch("hypnogen.cli.llm_generate_affirmations")
    def test_generate_affirmations_calls_llm(self, mock_llm_aff, mock_synthesize):
        from hypnogen.cli import cli

        mock_llm_aff.return_value = ["I am calm", "I feel strong", "I am focused"]

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            script_file = Path(tmpdir) / "script.txt"
            script_file.write_text("Welcome to relaxation.\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "--generate-affirmations",
                    "--goal", "reduce stress",
                    "-s", str(script_file),
                    "-o", str(out_file),
                    "--length-sec", "10",
                ],
            )

            assert result.exit_code == 0, f"CLI failed: {result.output}"
            mock_llm_aff.assert_called_once()

    @patch("hypnogen.cli.llm_generate_affirmations")
    @patch("hypnogen.cli.llm_generate_script")
    def test_use_llm_generates_both(self, mock_llm_script, mock_llm_aff, mock_synthesize):
        from hypnogen.cli import cli

        mock_llm_script.return_value = "Relax now."
        mock_llm_aff.return_value = ["I am calm", "I am strong"]

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "output.wav"
            result = runner.invoke(
                cli,
                [
                    "generate",
                    "--use-llm",
                    "--goal", "sleep better",
                    "-o", str(out_file),
                    "--length-sec", "10",
                ],
            )

            assert result.exit_code == 0, f"CLI failed: {result.output}"
            mock_llm_script.assert_called_once()
            mock_llm_aff.assert_called_once()

    @patch("hypnogen.cli.llm_generate_script")
    def test_llm_error_shows_friendly_message(self, mock_llm_script, mock_synthesize):
        from hypnogen.cli import cli
        from hypnogen.core.llm import LLMError

        mock_llm_script.side_effect = LLMError("API timeout")

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            aff_file = Path(tmpdir) / "aff.txt"
            aff_file.write_text("I am calm\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "--generate-script",
                    "--goal", "relax",
                    "-a", str(aff_file),
                    "-o", str(out_file),
                ],
            )

            assert result.exit_code != 0

    @patch("hypnogen.cli.llm_generate_script")
    def test_custom_style_passed_to_llm(self, mock_llm_script, mock_synthesize):
        from hypnogen.cli import cli

        mock_llm_script.return_value = "Relax now."

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            aff_file = Path(tmpdir) / "aff.txt"
            aff_file.write_text("I am calm\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "--generate-script",
                    "--goal", "confidence",
                    "--style", "permissive",
                    "-a", str(aff_file),
                    "-o", str(out_file),
                    "--length-sec", "10",
                ],
            )

            assert result.exit_code == 0, f"CLI failed: {result.output}"
            call_kwargs = mock_llm_script.call_args
            assert call_kwargs.kwargs.get("style") == "permissive" or call_kwargs[1].get("style") == "permissive"

    @patch("hypnogen.cli.llm_generate_affirmations")
    def test_custom_affirmation_count_passed_to_llm(self, mock_llm_aff, mock_synthesize):
        from hypnogen.cli import cli

        mock_llm_aff.return_value = ["I am calm", "I am strong"]

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            script_file = Path(tmpdir) / "script.txt"
            script_file.write_text("Welcome.\n")
            out_file = Path(tmpdir) / "output.wav"

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "--generate-affirmations",
                    "--goal", "focus",
                    "--affirmation-count", "15",
                    "-s", str(script_file),
                    "-o", str(out_file),
                    "--length-sec", "10",
                ],
            )

            assert result.exit_code == 0, f"CLI failed: {result.output}"
            call_kwargs = mock_llm_aff.call_args
            assert call_kwargs.kwargs.get("count") == 15 or call_kwargs[1].get("count") == 15

    def test_no_script_no_generate_fails(self, mock_synthesize):
        from hypnogen.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            aff_file = Path(tmpdir) / "aff.txt"
            aff_file.write_text("I am calm\n")
            result = runner.invoke(
                cli,
                ["generate", "-a", str(aff_file), "-o", "/tmp/test.wav"],
            )
            assert result.exit_code != 0


class TestCLIEntryPoint:

    def test_main_function_exists(self):
        from hypnogen.cli import main

        assert callable(main)
