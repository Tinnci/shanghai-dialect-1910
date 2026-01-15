"""
1910 Shanghai Dialect TTS Synthesis Task

This module provides the inference pipeline for synthesizing speech
from Pott Romanization input.

Usage:
    uv run python xtask.py synthesize "Ngoo yiao mah dzi"
    uv run python xtask.py synthesize --file input.txt --output output/
"""

import sys
from pathlib import Path
from typing import Optional
import torch

# Ensure project root is in path
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def get_device() -> torch.device:
    """Get the best available device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_matcha_model(
    checkpoint_path: Optional[Path] = None, device: torch.device = None
):
    """
    Load the Matcha-TTS model.

    If no checkpoint is provided, returns None (for dry-run mode).
    """
    if device is None:
        device = get_device()

    if checkpoint_path is None:
        print("⚠️ No checkpoint provided. Running in dry-run mode (frontend only).")
        return None

    try:
        from matcha.models.matcha_tts import MatchaTTS

        model = MatchaTTS.load_from_checkpoint(
            str(checkpoint_path), map_location=device
        )
        model.eval()
        model.to(device)
        print(f"✓ Model loaded from {checkpoint_path}")
        return model
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return None


def load_vocoder(checkpoint_path: Optional[Path] = None, device: torch.device = None):
    """
    Load the HiFi-GAN vocoder.

    If no checkpoint is provided, returns None.
    """
    if device is None:
        device = get_device()

    if checkpoint_path is None:
        return None

    try:
        from matcha.hifigan.config import v1
        from matcha.hifigan.env import AttrDict
        from matcha.hifigan.models import Generator as HiFiGAN

        h = AttrDict(v1)
        hifigan = HiFiGAN(h).to(device)
        state_dict = torch.load(str(checkpoint_path), map_location=device)
        hifigan.load_state_dict(state_dict["generator"])
        hifigan.eval()
        hifigan.remove_weight_norm()
        print(f"✓ Vocoder loaded from {checkpoint_path}")
        return hifigan
    except Exception as e:
        print(f"✗ Failed to load vocoder: {e}")
        return None


def text_to_sequence_shanghai(text: str):
    """
    Convert Pott romanization text to model input sequence.

    Uses shanghai_cleaners for G2P conversion.
    """
    from matcha.text import text_to_sequence

    sequence, clean_text = text_to_sequence(text, ["shanghai_cleaners"])
    return sequence, clean_text


@torch.inference_mode()
def synthesize(
    text: str,
    model=None,
    vocoder=None,
    device: torch.device = None,
    n_timesteps: int = 10,
    temperature: float = 0.667,
    length_scale: float = 1.0,
):
    """
    Synthesize speech from Pott romanization text.

    Args:
        text: Input text in Pott romanization
        model: Loaded Matcha-TTS model (or None for dry-run)
        vocoder: Loaded HiFi-GAN vocoder (or None for dry-run)
        device: Torch device
        n_timesteps: Number of ODE solver steps
        temperature: Sampling temperature
        length_scale: Duration scaling factor

    Returns:
        dict with keys:
        - 'text': Original input
        - 'ipa': IPA transcription
        - 'sequence': Model input IDs
        - 'mel': Generated mel spectrogram (if model available)
        - 'audio': Generated audio waveform (if vocoder available)
    """
    if device is None:
        device = get_device()

    # Step 1: Frontend - Convert text to sequence
    sequence, ipa_text = text_to_sequence_shanghai(text)

    result = {
        "text": text,
        "ipa": ipa_text,
        "sequence": sequence,
        "mel": None,
        "audio": None,
    }

    print(f"\n📝 Input (Pott):  {text}")
    print(f"🔤 IPA Output:    {ipa_text}")
    print(
        f"🔢 Sequence:      {sequence[:15]}..."
        if len(sequence) > 15
        else f"🔢 Sequence:      {sequence}"
    )

    if model is None:
        print("\n⚠️ No model loaded - frontend-only mode.")
        return result

    # Step 2: Prepare tensors
    from matcha.utils.utils import intersperse

    # Add blank tokens between phonemes (common for TTS)
    sequence_intersp = intersperse(sequence, 0)
    x = torch.tensor([sequence_intersp], dtype=torch.long, device=device)
    x_lengths = torch.tensor([len(sequence_intersp)], dtype=torch.long, device=device)

    # Step 3: Generate mel spectrogram
    print("\n⏳ Generating mel spectrogram...")

    output = model.synthesise(
        x,
        x_lengths,
        n_timesteps=n_timesteps,
        temperature=temperature,
        length_scale=length_scale,
    )

    mel = output["mel"]
    result["mel"] = mel
    print(f"✓ Mel shape: {mel.shape}")

    if vocoder is None:
        print("⚠️ No vocoder loaded - returning mel only.")
        return result

    # Step 4: Generate audio waveform
    print("⏳ Generating audio waveform...")

    audio = vocoder(mel).clamp(-1, 1)
    audio = audio.squeeze().cpu().numpy()
    result["audio"] = audio
    print(f"✓ Audio shape: {audio.shape}")

    return result


def save_audio(audio, output_path: Path, sample_rate: int = 22050):
    """Save audio waveform to file."""
    import soundfile as sf

    sf.write(str(output_path), audio, sample_rate)
    print(f"💾 Audio saved to: {output_path}")


def run_synthesize(
    text: str,
    output_path: Optional[Path] = None,
    model_checkpoint: Optional[Path] = None,
    vocoder_checkpoint: Optional[Path] = None,
    n_timesteps: int = 10,
    temperature: float = 0.667,
    length_scale: float = 1.0,
):
    """
    Main entry point for synthesis task.
    """
    print("=" * 60)
    print("🍵 1910 Shanghai Dialect TTS Synthesis")
    print("=" * 60)

    device = get_device()
    print(f"📍 Device: {device}")

    # Load models
    model = load_matcha_model(model_checkpoint, device)
    vocoder = load_vocoder(vocoder_checkpoint, device)

    # Synthesize
    result = synthesize(
        text=text,
        model=model,
        vocoder=vocoder,
        device=device,
        n_timesteps=n_timesteps,
        temperature=temperature,
        length_scale=length_scale,
    )

    # Save output
    if result["audio"] is not None and output_path:
        save_audio(result["audio"], output_path)
    elif result["mel"] is not None:
        # Save mel as numpy for debugging
        import numpy as np

        mel_path = (
            output_path.with_suffix(".npy") if output_path else Path("output_mel.npy")
        )
        np.save(str(mel_path), result["mel"].cpu().numpy())
        print(f"💾 Mel saved to: {mel_path}")

    print("\n" + "=" * 60)
    print("✓ Synthesis complete!")
    print("=" * 60)

    return result


# Test function
if __name__ == "__main__":
    # Dry-run test (no models)
    run_synthesize("Ngoo yiao mah dzi")
