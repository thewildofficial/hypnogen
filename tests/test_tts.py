"""Tests for TTS synthesis module."""
import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock
from hypnogen.core.tts import synthesize, list_voices


class TestSynthesize:
    """Test suite for synthesize function."""

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_returns_numpy_array_and_sample_rate(self, mock_pipeline_class):
        """synthesize should return (np.ndarray, int) tuple."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Mock the pipeline call to return a generator with results
        mock_result = Mock()
        mock_audio = Mock()
        mock_audio.cpu.return_value.numpy.return_value = np.array([0.1, 0.2, 0.3])
        mock_result.output.audio = mock_audio
        mock_pipeline.return_value = [mock_result]  # Generator yields one result
        
        audio, sr = synthesize("test text")
        
        assert isinstance(audio, np.ndarray)
        assert isinstance(sr, int)
        assert sr == 24000

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_default_voice(self, mock_pipeline_class):
        """synthesize should use default voice 'af_heart'."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        mock_result = Mock()
        mock_audio = Mock()
        mock_audio.cpu.return_value.numpy.return_value = np.array([0.1])
        mock_result.output.audio = mock_audio
        mock_pipeline.return_value = [mock_result]
        
        synthesize("test")
        
        # Check that pipeline was called with correct voice
        mock_pipeline.assert_called_once()
        call_args = mock_pipeline.call_args
        assert call_args[1]['voice'] == 'af_heart'

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_custom_voice(self, mock_pipeline_class):
        """synthesize should pass through custom voice parameter."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        mock_result = Mock()
        mock_audio = Mock()
        mock_audio.cpu.return_value.numpy.return_value = np.array([0.1])
        mock_result.output.audio = mock_audio
        mock_pipeline.return_value = [mock_result]
        
        synthesize("test", voice="am_adam")
        
        call_args = mock_pipeline.call_args
        assert call_args[1]['voice'] == 'am_adam'

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_speed_parameter(self, mock_pipeline_class):
        """synthesize should pass through speed parameter."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        mock_result = Mock()
        mock_audio = Mock()
        mock_audio.cpu.return_value.numpy.return_value = np.array([0.1])
        mock_result.output.audio = mock_audio
        mock_pipeline.return_value = [mock_result]
        
        synthesize("test", speed=0.8)
        
        call_args = mock_pipeline.call_args
        assert call_args[1]['speed'] == 0.8

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_returns_mono_audio(self, mock_pipeline_class):
        """synthesize should return 1D (mono) audio array."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        mock_result = Mock()
        mock_audio = Mock()
        # Kokoro returns 1D audio
        mock_audio.cpu.return_value.numpy.return_value = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_result.output.audio = mock_audio
        mock_pipeline.return_value = [mock_result]
        
        audio, _ = synthesize("test")
        
        assert audio.ndim == 1
        assert len(audio) == 5

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_concatenates_multiple_chunks(self, mock_pipeline_class):
        """synthesize should concatenate audio from multiple results."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Mock two results (pipeline might split long text)
        mock_result1 = Mock()
        mock_audio1 = Mock()
        mock_audio1.cpu.return_value.numpy.return_value = np.array([0.1, 0.2])
        mock_result1.output.audio = mock_audio1
        
        mock_result2 = Mock()
        mock_audio2 = Mock()
        mock_audio2.cpu.return_value.numpy.return_value = np.array([0.3, 0.4])
        mock_result2.output.audio = mock_audio2
        
        mock_pipeline.return_value = [mock_result1, mock_result2]
        
        audio, _ = synthesize("test")
        
        assert len(audio) == 4
        np.testing.assert_array_equal(audio, np.array([0.1, 0.2, 0.3, 0.4]))

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_handles_empty_text(self, mock_pipeline_class):
        """synthesize should raise ValueError for empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            synthesize("")

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_handles_whitespace_only_text(self, mock_pipeline_class):
        """synthesize should raise ValueError for whitespace-only text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            synthesize("   \n\t  ")

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_rejects_invalid_speed(self, mock_pipeline_class):
        """synthesize should raise ValueError for invalid speed values."""
        with pytest.raises(ValueError, match="Speed must be positive"):
            synthesize("test", speed=0.0)
        
        with pytest.raises(ValueError, match="Speed must be positive"):
            synthesize("test", speed=-1.0)

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_sample_rate_parameter(self, mock_pipeline_class):
        """synthesize should accept custom sample rate (for future extensibility)."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        mock_result = Mock()
        mock_audio = Mock()
        mock_audio.cpu.return_value.numpy.return_value = np.array([0.1])
        mock_result.output.audio = mock_audio
        mock_pipeline.return_value = [mock_result]
        
        audio, sr = synthesize("test", sr=22050)
        
        # Should return the requested sample rate
        assert sr == 22050

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_detects_language_from_voice(self, mock_pipeline_class):
        """synthesize should extract language code from voice name."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        mock_result = Mock()
        mock_audio = Mock()
        mock_audio.cpu.return_value.numpy.return_value = np.array([0.1])
        mock_result.output.audio = mock_audio
        mock_pipeline.return_value = [mock_result]
        
        synthesize("test", voice="af_heart")
        
        # Should initialize pipeline with language 'a' (from af_heart)
        mock_pipeline_class.assert_called_once()
        call_args = mock_pipeline_class.call_args
        # KPipeline is called with lang_code as a keyword argument
        assert call_args.kwargs['lang_code'] == 'a'

    @patch('hypnogen.core.tts.KPipeline')
    def test_synthesize_skips_results_without_audio(self, mock_pipeline_class):
        """synthesize should skip results that have no audio output."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # First result has no audio, second has audio
        mock_result1 = Mock()
        mock_result1.output.audio = None
        
        mock_result2 = Mock()
        mock_audio2 = Mock()
        mock_audio2.cpu.return_value.numpy.return_value = np.array([0.5, 0.6])
        mock_result2.output.audio = mock_audio2
        
        mock_pipeline.return_value = [mock_result1, mock_result2]
        
        audio, _ = synthesize("test")
        
        assert len(audio) == 2
        np.testing.assert_array_equal(audio, np.array([0.5, 0.6]))


class TestListVoices:
    """Test suite for list_voices function."""

    @patch('hypnogen.core.tts.KPipeline')
    def test_list_voices_returns_list_of_strings(self, mock_pipeline_class):
        """list_voices should return a list of voice IDs as strings."""
        # We'll return a hardcoded list for now
        voices = list_voices()
        
        assert isinstance(voices, list)
        assert len(voices) > 0
        assert all(isinstance(v, str) for v in voices)

    @patch('hypnogen.core.tts.KPipeline')
    def test_list_voices_includes_default_voice(self, mock_pipeline_class):
        """list_voices should include the default voice 'af_heart'."""
        voices = list_voices()
        assert 'af_heart' in voices

    @patch('hypnogen.core.tts.KPipeline')
    def test_list_voices_includes_male_voice(self, mock_pipeline_class):
        """list_voices should include at least one male voice like 'am_adam'."""
        voices = list_voices()
        # Check for any male voice (am_* pattern)
        male_voices = [v for v in voices if v.startswith('am_')]
        assert len(male_voices) > 0
