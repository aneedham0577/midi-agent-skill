#!/usr/bin/env python3
"""
Convert MIDI file to WAV using FluidSynth and A320U.sf2 SoundFont.
"""

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ConvertOptions:
    """Configuration for MIDI to WAV conversion."""
    soundfont_path: Optional[str] = None  # Defaults to GeneralUser-GS.sf2 (or A320U.sf2) in soundfonts directory
    sample_rate: int = 44100
    gain: float = 0.6
    reverb: bool = True   # Studio space and depth
    chorus: bool = True   # Stereo warmth and thickness


def find_fluidsynth() -> Optional[str]:
    """Find fluidsynth executable in PATH or in local bin directory."""
    system_path = shutil.which("fluidsynth")
    if system_path:
        return system_path

    # Check local bin/ directory
    local_bin = Path(__file__).parent.parent / "bin" / "fluidsynth.exe"
    if local_bin.exists():
        return str(local_bin)

    return None


def convert_to_wav(midi_path: str, options: Optional[ConvertOptions] = None) -> str:
    """
    Convert a MIDI file to WAV using FluidSynth and A320U.sf2 SoundFont.

    Prerequisites:
    - FluidSynth must be installed (brew install fluidsynth on macOS)
    - A320U.sf2 must be placed in the soundfonts directory

    Args:
        midi_path: Path to the input MIDI file
        options: Conversion options

    Returns:
        Path to the generated WAV file

    Raises:
        FileNotFoundError: If MIDI file or SoundFont not found
        RuntimeError: If FluidSynth is not installed or conversion fails
    """
    if options is None:
        options = ConvertOptions()

    fluidsynth_exe = find_fluidsynth()
    if not fluidsynth_exe:
        raise RuntimeError(
            "FluidSynth is not installed.\n"
            "Install it with: brew install fluidsynth (macOS) or place fluidsynth.exe in external/midi-agent-skill/bin/"
        )

    # Validate MIDI file exists
    midi_file = Path(midi_path)
    if not midi_file.exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    # Resolve soundfont path
    if options.soundfont_path:
        soundfont = Path(options.soundfont_path)
    else:
        # Default to GeneralUser-GS.sf2, fall back to FluidR3 or A320U
        sf_dir = Path(__file__).parent.parent / "soundfonts"
        candidates = [
            sf_dir / "GeneralUser-GS.sf2",
            sf_dir / "FluidR3_GM_GS.sf2",
            sf_dir / "FluidR3_GM.sf2",
            sf_dir / "A320U.sf2"
        ]
        soundfont = next((p for p in candidates if p.exists()), candidates[-1])

    if not soundfont.exists():
        raise FileNotFoundError(
            f"SoundFont not found: {soundfont}\n"
            f"Please place GeneralUser-GS.sf2 or A320U.sf2 in the soundfonts directory."
        )

    # Set up output path
    out_dir = Path(__file__).parent.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    wav_path = out_dir / f"{midi_file.stem}.wav"

    # Build FluidSynth command
    cmd = [
        fluidsynth_exe,
        "-ni",  # Non-interactive, no shell
        f"--sample-rate={options.sample_rate}",
        f"--gain={options.gain}",
        "--reverb=yes" if options.reverb else "--reverb=no",
        "--chorus=yes" if options.chorus else "--chorus=no",
        "-F", str(wav_path),  # Output file
        str(soundfont),  # SoundFont
        str(midi_file)  # Input MIDI
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        raise RuntimeError(
            "FluidSynth is not installed.\n"
            "Install it with: brew install fluidsynth (macOS) or place fluidsynth.exe in external/midi-agent-skill/bin/"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FluidSynth conversion failed: {e.stderr}")

    return str(wav_path)


def is_fluidsynth_available() -> bool:
    """Check if FluidSynth is available on the system or in local bin."""
    return find_fluidsynth() is not None


def is_soundfont_available() -> bool:
    """Check if the default SoundFont (A320U.sf2) is available."""
    soundfont = Path(__file__).parent.parent / "soundfonts" / "A320U.sf2"
    return soundfont.exists()


@dataclass
class ConversionStatus:
    """Status of MIDI to WAV conversion capability."""
    fluidsynth_installed: bool
    soundfont_available: bool
    ready: bool
    message: str


def get_conversion_status() -> ConversionStatus:
    """Get system status for MIDI to WAV conversion."""
    fluidsynth_installed = is_fluidsynth_available()
    soundfont_available = is_soundfont_available()
    ready = fluidsynth_installed and soundfont_available

    messages = []
    if not fluidsynth_installed:
        messages.append("FluidSynth is not installed. Install with: brew install fluidsynth")
    if not soundfont_available:
        messages.append("A320U.sf2 SoundFont not found. Download from: https://musical-artifacts.com/artifacts/5906")
        messages.append("Place the file in: soundfonts/A320U.sf2")

    if ready:
        message = "Ready for MIDI to WAV conversion using A320U.sf2 SoundFont."
    else:
        message = "\n".join(messages)

    return ConversionStatus(
        fluidsynth_installed=fluidsynth_installed,
        soundfont_available=soundfont_available,
        ready=ready,
        message=message
    )


if __name__ == "__main__":
    # Check conversion status
    status = get_conversion_status()
    print(f"FluidSynth installed: {status.fluidsynth_installed}")
    print(f"SoundFont available: {status.soundfont_available}")
    print(f"Ready: {status.ready}")
    print(f"Message: {status.message}")

    # Example conversion (if ready)
    if len(sys.argv) > 1 and status.ready:
        midi_file = sys.argv[1]
        try:
            wav_file = convert_to_wav(midi_file)
            print(f"Converted: {wav_file}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
