<p align="center">
  <img src="hypnogen_logo.png" alt="Hypnogen Logo" width="200"/>
</p>

<h1 align="center">Hypnogen</h1>

<p align="center">
  <strong>AI-Powered Hypnosis Audio Generator</strong><br>
  Create personalized hypnosis sessions with binaural beats, Ericksonian scripts, and subliminal affirmations
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#installation">Installation</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#macos-app">macOS App</a> •
  <a href="#api">API</a> •
  <a href="#development">Development</a>
</p>

---

## 🎯 Features

### Multi-Layer Audio Architecture
- **Binaural Beat Bed**: Customizable frequency entrainment (delta, theta, alpha waves)
- **Shepherd Track**: Ericksonian induction with embedded commands
- **Subliminal Swarm**: Background affirmations at user-calibrated levels
- **Boundary Events**: Smooth transitions with clicks, pauses, and stereo effects

### AI-Powered Generation
- **LLM Script Writing**: Generate hypnotic scripts from simple goals
- **Smart Affirmations**: Diverse mix of I/You/Reality statements
- **5 Tone Styles**: Calm therapeutic, intense coach, mystic-poetic, clinical-precision, minimalist
- **Theme Anchors**: Consistent metaphors woven throughout

### User Calibration
- **Subliminal Level Calibration**: Listen to 5 sample levels and choose your optimal setting
- **Progress Tracking**: Detailed generation progress with section names
- **Voice Selection**: 11 voices across American and British accents

### Technical Excellence
- **Kokoro TTS**: High-quality neural text-to-speech
- **TTS Caching**: Reused pipelines for faster generation
- **Retry Logic**: Automatic repair for invalid affirmations
- **Validation**: No negations, no future tense, 20-word limit

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hypnogen.git
cd hypnogen

# Install in editable mode
pip install -e .

# Set up API keys (required for LLM features)
export NVIDIA_API_KEY="your_key_here"
export GEMINI_KEY="your_key_here"
```

### Requirements
- Python 3.9+
- NVIDIA API key (for Kimi K2.5) OR Gemini API key
- ~2GB disk space for Kokoro TTS models

---

## 🚀 Quickstart

### Generate Your First Session

```bash
# Using LLM to generate everything
hypnogen generate \
  --use-llm \
  --goal "deep relaxation and stress relief" \
  --out my_session.wav \
  --length-sec 600
```

Or use the **Gradio UI** for a visual experience:

```bash
python -m hypnogen.web
```

Then open http://localhost:7860 in your browser.

---

## 🎨 Gradio UI Guide

### Step 1: Calibrate Subliminal Level

Before generating, use the calibration feature to find your optimal subliminal level:

1. Click **"Generate Calibration Samples"**
2. Listen to all 5 samples (from very subtle to clearly audible)
3. Select the level where you can hear words when focused, but they blend away when not
4. This level will be used for your session

### Step 2: Choose Your Generation Mode

**Option A: AI Generation**
- Enter your **Goal** (e.g., "confidence for public speaking")
- Select **Script Style**: Ericksonian, Permissive, Authoritative, Conversational, or Fractionation
- Choose **Induction Depth**: Light, Medium, Deep, or Somnambulistic
- Set **Affirmation Tone**: Calm therapeutic, Intense coach, Mystic-poetic, Clinical-precision, or Minimalist
- Click **"Generate Both"** to create script and affirmations

**Option B: Manual Input**
- Paste your own script in the "Hypnotic Script" box
- Add affirmations (one per line) in the "Affirmations" box
- Use markup tags: `<cmd>embedded commands</cmd>`, `<snap/>`, `<pause duration="1000ms"/>`

### Step 3: Configure Audio

- **Shepherd Voice**: Main induction voice (default: af_heart - warm female)
- **Swarm Voice**: Background affirmations voice
- **Randomize Voices**: Use different voices for variety
- **Random Seed**: For reproducible sessions

### Step 4: Generate

Click **"Generate Audio"** and watch the progress:
- Parsing script
- TTS Shepherd: X/Y segments
- TTS Swarm: X/Y affirmations
- Generating binaural bed
- Mixing layers
- Exporting WAV

---

## 💻 CLI Reference

### Basic Generation

```bash
hypnogen generate \
  --script script.txt \
  --affirmations affirmations.txt \
  --out session.wav \
  --length-sec 600 \
  --voice af_heart
```

### LLM-Powered Generation

```bash
hypnogen generate \
  --use-llm \
  --goal "overcome procrastination" \
  --style ericksonian \
  --depth medium \
  --command-density medium \
  --focus-theme "work productivity" \
  --out productive.wav \
  --length-sec 900
```

### Generate Components Separately

```bash
# Script only
hypnogen generate \
  --generate-script \
  --goal "sleep better" \
  --style fractionation \
  --out sleep_script.txt

# Affirmations only
hypnogen generate \
  --generate-affirmations \
  --goal "confidence" \
  --affirmation-count 30 \
  --out confidence_affirmations.txt
```

### Available Options

| Flag | Description | Default |
|------|-------------|---------|
| `--script, -s` | Path to script file | - |
| `--affirmations, -a` | Path to affirmations file | - |
| `--out, -o` | Output WAV file (required) | - |
| `--length-sec, -l` | Session length in seconds | 600 |
| `--voice, -v` | TTS voice | af_heart |
| `--seed` | Random seed | - |
| `--use-llm` | Enable LLM generation | False |
| `--goal, -g` | Goal for LLM generation | - |
| `--style` | Script style | ericksonian |
| `--depth` | Induction depth | medium |
| `--command-density` | Embedded command density | medium |
| `--focus-theme` | Theme/focus for script | - |
| `--custom-instructions` | Additional instructions | - |
| `--stems-dir` | Export individual stems | - |

### Voice Options

**American English:**
- `af_heart` - Warm and gentle (default)
- `af_bella` - Expressive
- `af_sarah` - Professional
- `af_nicole` - Conversational
- `af_sky` - Bright and clear
- `am_adam` - Clear and steady
- `am_michael` - Deep voice

**British English:**
- `bf_emma` - British accent
- `bf_isabella` - Soft British
- `bm_george` - British accent
- `bm_lewis` - Warm British

---

## 📝 Script Markup Guide

Use special tags in your scripts for advanced audio effects:

```text
# Embedded Commands (pitch-shifted, slower)
As you <cmd pitch="-2" rate="0.9">relax deeply</cmd>...

# Pauses (in milliseconds)
Breathe in... <pause duration="3000ms"/> and out...

# Finger Snaps
<snap/> <drop>drop</drop> deeper now...

# Drop Cues (with pitch shift)
Three... two... one... <drop>sleep</drop>

# Combined Effects
<snap/> <pause duration="500ms"/> <drop>drop</drop>
```

---

## 🧪 Testing

```bash
# Run full test suite
pytest -q

# Run with coverage
pytest --cov=hypnogen --cov-report=html

# Run specific test categories
pytest -q tests/test_web.py -k "calibration"
pytest -q tests/test_tts.py -k "voices"
pytest -q tests/test_epochs.py -k "snap"
```

---

## ⚠️ Disclaimer & Safety

**Hypnogen is for experimental and educational purposes only.**

- **Not a Medical Device**: Not intended to diagnose, treat, cure, or prevent any condition
- **No Therapeutic Claims**: Results vary; no guarantees provided
- **Use at Your Own Risk**: Consult a professional if you have epilepsy, seizure disorders, or mental health conditions

### Safety Boundaries

- **Age Restriction**: Not for use by or on minors (18+ only)
- **Consent Required**: Never play generated audio for someone without their explicit knowledge and agreement
- **No Driving**: Do not use while driving, operating machinery, or in situations requiring full alertness
- **No Manipulation**: Do not use to manipulate, deceive, or coerce any person

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           User Input (CLI/UI)           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      LLM Generation (Optional)          │
│  ├─ Script with embedded commands       │
│  ├─ Affirmations (I/You/Reality mix)    │
│  └─ Theme anchors                       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Audio Pipeline                │
│  ├─ Shepherd: TTS with pitch shifts     │
│  ├─ Swarm: Subliminal affirmations      │
│  ├─ Binaural: Frequency entrainment     │
│  ├─ Epochs: Boundary events             │
│  └─ Mixer: Layered combination          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Output (WAV file)              │
└─────────────────────────────────────────┘
```

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional voice accents (Kokoro supports many languages)
- More script styles and induction techniques
- Enhanced audio effects (reverb, spatial audio)
- Performance optimizations
- Documentation improvements

Please ensure tests pass and add new tests for new features.

---

## 📄 License

See [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ for the hypnosis and self-improvement community
</p>

<p align="center">
  <sub>Remember: You are always in control. Your mind, your journey.</sub>
</p>
