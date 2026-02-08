"""Affirmation swarm generation with random panning and timing."""

import numpy as np


# Validation rules
FORBIDDEN_TENSE_WORDS = {
    "was", "were", "will", "would", "could", "should", "had",
    "have been", "has been"
}
FORBIDDEN_NEGATIONS = {
    "not", "never", "don't", "won't", "can't", "isn't", "aren't",
    "doesn't", "didn't"
}
MAX_WORDS = 7


def validate_affirmation(text: str) -> tuple[bool, str]:
    """
    Validate affirmation against rules.
    
    Rules:
    - Non-empty after stripping whitespace
    - ≤ 7 words
    - Present tense only (reject past/future/conditional)
    - No negations
    
    Args:
        text: Affirmation text to validate
        
    Returns:
        Tuple of (valid: bool, reason: str)
        If valid: (True, "OK")
        If invalid: (False, "reason: <explanation>")
    """
    # Strip and check empty
    stripped = text.strip()
    if not stripped:
        return (False, "reason: empty or whitespace-only")
    
    # Check word count
    words = stripped.split()
    if len(words) > MAX_WORDS:
        return (False, f"reason: exceeds {MAX_WORDS} words (has {len(words)})")
    
    # Lowercase for case-insensitive checks
    lower_text = stripped.lower()
    lower_words = [w.lower() for w in words]
    
    # Check forbidden tense words
    for forbidden in FORBIDDEN_TENSE_WORDS:
        if " " in forbidden:
            # Multi-word phrases like "have been"
            if forbidden in lower_text:
                return (False, f"reason: forbidden tense '{forbidden}'")
        else:
            # Single words
            if forbidden in lower_words:
                return (False, f"reason: forbidden tense '{forbidden}'")
    
    # Check negations
    for negation in FORBIDDEN_NEGATIONS:
        if negation in lower_words or negation in lower_text:
            return (False, f"reason: negation '{negation}' not allowed")
    
    return (True, "OK")


def validate_affirmations(texts: list[str]) -> list[tuple[bool, str]]:
    """
    Validate multiple affirmations.
    
    Args:
        texts: List of affirmation texts
        
    Returns:
        List of (valid, reason) tuples matching input order
    """
    return [validate_affirmation(text) for text in texts]


def apply_constant_power_pan(audio: np.ndarray, pan: float) -> np.ndarray:
    """
    Apply constant-power panning to mono audio.
    
    Constant power panning preserves total energy:
    left_gain^2 + right_gain^2 = 1
    
    Args:
        audio: Mono audio (1D array)
        pan: Pan position in [-1.0, 1.0]
             -1.0 = full left, 0.0 = center, 1.0 = full right
             
    Returns:
        Stereo audio with shape (N, 2)
    """
    # Map pan [-1, 1] to angle [0, π/2]
    angle = (pan + 1.0) * (np.pi / 4.0)
    
    # Constant power gains
    left_gain = np.cos(angle)
    right_gain = np.sin(angle)
    
    # Apply gains and stack to stereo
    left_channel = audio * left_gain
    right_channel = audio * right_gain
    
    return np.stack([left_channel, right_channel], axis=-1)


def phonetic_hash(text: str) -> str:
    """
    Compute crude phonetic fingerprint for collision detection.
    
    Extracts initial consonant clusters and dominant vowel patterns
    from each word to create a phonetic signature. This is intentionally
    crude - designed to catch obvious collisions like "calm/clear/claim"
    without full IPA processing.
    
    Args:
        text: Input text to hash
        
    Returns:
        Phonetic hash string (e.g., "clm-a" for "calm")
    """
    # Lowercase and strip
    text = text.lower().strip()
    if not text:
        return ""
    
    # Split into words
    words = text.split()
    if not words:
        return ""
    
    # Define vowels
    vowels = set("aeiou")
    
    # Extract phonetic components from each word
    components = []
    for word in words:
        if not word:
            continue
        
        # Extract consonants and vowels separately
        consonants = []
        vowel_part = []
        
        for char in word:
            if not char.isalpha():
                continue
            if char in vowels:
                vowel_part.append(char)
            else:
                consonants.append(char)
        
        # Build component: first 2-3 consonants + first vowel
        consonant_str = "".join(consonants[:3])
        vowel_str = vowel_part[0] if vowel_part else ""
        
        if consonant_str or vowel_str:
            component = f"{consonant_str}-{vowel_str}" if vowel_str else consonant_str
            components.append(component)
    
    return " ".join(components)


def phonetic_similarity(a: str, b: str) -> float:
    """
    Compute phonetic similarity between two texts.
    
    Compares phonetic hashes and returns overlap ratio.
    Similarity > 0.6 indicates texts are phonetically similar
    enough to avoid back-to-back scheduling.
    
    Args:
        a: First text
        b: Second text
        
    Returns:
        Similarity score in [0.0, 1.0] where 1.0 is identical
    """
    hash_a = phonetic_hash(a)
    hash_b = phonetic_hash(b)
    
    if not hash_a and not hash_b:
        return 1.0
    if not hash_a or not hash_b:
        return 0.0
    
    # Compare consonant prefixes (the part before the first dash in each component)
    # Extract first component's consonants for each hash
    parts_a = hash_a.split()[0] if hash_a.split() else ""
    parts_b = hash_b.split()[0] if hash_b.split() else ""
    
    # Get consonant prefix (before dash)
    cons_a = parts_a.split("-")[0] if "-" in parts_a else parts_a
    cons_b = parts_b.split("-")[0] if "-" in parts_b else parts_b
    
    if not cons_a and not cons_b:
        return 1.0
    if not cons_a or not cons_b:
        return 0.0
    
    # Compute shared prefix length
    shared_len = 0
    for char_a, char_b in zip(cons_a, cons_b):
        if char_a == char_b:
            shared_len += 1
        else:
            break
    
    # Similarity = shared prefix / max length
    max_len = max(len(cons_a), len(cons_b))
    if max_len == 0:
        return 0.0
    
    return shared_len / max_len


def schedule_affirmations(
    affirmations: list[str],
    duration_sec: float,
    rng: np.random.Generator | None = None,
) -> list[dict]:
    """
    Create placement schedule for affirmations with random timing and panning.
    
    Cycles through affirmations to fill duration, with random gaps between
    placements and random stereo positions.
    
    Args:
        affirmations: List of affirmation texts (for cycling)
        duration_sec: Total duration to fill
        rng: Random number generator (creates default if None)
        
    Returns:
        List of dicts with keys:
        - "index": int (position in affirmations list)
        - "start_sec": float (start time in seconds)
        - "pan": float (stereo position in [-0.9, 0.9])
    """
    if rng is None:
        rng = np.random.default_rng()
    
    schedule = []
    current_time = 0.0
    affirmation_idx = 0
    
    while current_time < duration_sec:
        # Schedule this affirmation
        schedule.append({
            "index": affirmation_idx % len(affirmations),
            "start_sec": current_time,
            "pan": rng.uniform(-0.9, 0.9),
        })
        
        # Random gap until next affirmation (0.5s to 2.0s)
        gap = rng.uniform(0.5, 2.0)
        current_time += gap
        affirmation_idx += 1
    
    # Post-process to avoid phonetically similar back-to-back entries
    SIMILARITY_THRESHOLD = 0.6
    changed = True
    max_iterations = len(schedule) * 2  # Allow more iterations for complex cases
    iterations = 0
    
    while changed and iterations < max_iterations:
        changed = False
        iterations += 1
        
        for i in range(len(schedule) - 1):
            text_i = affirmations[schedule[i]["index"]]
            text_j = affirmations[schedule[i + 1]["index"]]
            similarity = phonetic_similarity(text_i, text_j)
            
            if similarity > SIMILARITY_THRESHOLD:
                # Find any non-similar entry to swap with
                swap_candidate = None
                for k in range(i + 2, len(schedule)):
                    text_k = affirmations[schedule[k]["index"]]
                    # Check that text_k is not similar to text_i
                    if phonetic_similarity(text_i, text_k) > SIMILARITY_THRESHOLD:
                        continue
                    
                    # Validate swap won't make things worse
                    # Check what text_j would be next to at position k
                    problems = 0
                    if k - 1 >= 0:
                        text_k_prev = affirmations[schedule[k - 1]["index"]]
                        if phonetic_similarity(text_k_prev, text_j) > SIMILARITY_THRESHOLD:
                            problems += 1
                    if k + 1 < len(schedule):
                        text_k_next = affirmations[schedule[k + 1]["index"]]
                        if phonetic_similarity(text_j, text_k_next) > SIMILARITY_THRESHOLD:
                            problems += 1
                    
                    # Only swap if net improvement (fix 1, create at most 1)
                    if problems <= 1:
                        swap_candidate = k
                        break
                
                # Swap indices only (preserve timing and pan)
                if swap_candidate is not None:
                    schedule[i + 1]["index"], schedule[swap_candidate]["index"] = (
                        schedule[swap_candidate]["index"],
                        schedule[i + 1]["index"],
                    )
                    changed = True
                    break  # Restart scan after swap
    
    return schedule


def generate_swarm(
    affirmation_audios: list[np.ndarray],
    duration_sec: float,
    sr: int = 44100,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    Generate affirmation swarm layer with random panning and timing.
    
    Takes pre-rendered audio clips and places them into a stereo buffer
    according to a random schedule with stereo panning and timing jitter.
    
    Args:
        affirmation_audios: List of mono audio clips (1D numpy arrays)
        duration_sec: Total output duration in seconds
        sr: Sample rate (default 44100 Hz)
        rng: Random number generator (creates default if None)
        
    Returns:
        Stereo audio with shape (N, 2) where N = duration_sec * sr
    """
    if rng is None:
        rng = np.random.default_rng()
    
    # Create empty stereo buffer
    total_samples = int(duration_sec * sr)
    swarm_buffer = np.zeros((total_samples, 2), dtype=np.float64)
    
    # Get placement schedule (uses affirmation indices, not the audio directly)
    # We create a dummy list of affirmation IDs to pass to scheduler
    affirmation_ids = [str(i) for i in range(len(affirmation_audios))]
    schedule = schedule_affirmations(affirmation_ids, duration_sec, rng=rng)
    
    # Place each scheduled affirmation
    for item in schedule:
        clip_idx = item["index"]
        start_sec = item["start_sec"]
        pan = item["pan"]
        
        # Get the audio clip
        clip_mono = affirmation_audios[clip_idx]
        
        # Apply panning to make it stereo
        clip_stereo = apply_constant_power_pan(clip_mono, pan)
        
        # Calculate sample position
        start_sample = int(start_sec * sr)
        
        # Skip if start is beyond buffer
        if start_sample >= total_samples:
            continue
        
        # Calculate how much of the clip fits in the buffer
        clip_length = len(clip_stereo)
        available_space = total_samples - start_sample
        samples_to_copy = min(clip_length, available_space)
        
        # Add clip to buffer (additive mixing for overlaps)
        swarm_buffer[start_sample:start_sample + samples_to_copy] += (
            clip_stereo[:samples_to_copy]
        )
    
    return swarm_buffer
