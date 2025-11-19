#!/usr/bin/env python3

import os
import time
import yaml
import pygame

from gpio_controller import GPIOController
import patterns


def load_show(file_path):
    """
    Load a YAML show file and also return the base directory
    so we can resolve the MP3 path relative to the YAML file.
    """
    base_dir = os.path.dirname(os.path.abspath(file_path)) or "."
    with open(file_path, "r") as f:
        show = yaml.safe_load(f)
    return show, base_dir


def play_song(song_path):
    """
    Initialize pygame mixer and start playing the given audio file.
    Returns the start time (time.time()) so we can sync patterns.
    """
    if not os.path.exists(song_path):
        raise FileNotFoundError(f"Audio file not found: {song_path}")

    # Initialize mixer (safe to call multiple times)
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100)

    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()
    return time.time()


def run_show(show, base_dir="."):
    """
    Run a light show based on a loaded show config and base directory.
    The YAML must contain:
      - file: "somefile.mp3"
      - sections: list of { start, end, pattern, options? }
    """
    gpio = GPIOController()

    sections = show["sections"]
    audio_file = show["file"]

    # Resolve MP3 path relative to YAML directory
    audio_path = os.path.join(base_dir, audio_file)

    print(f"Playing audio: {audio_path}")
    start_time = play_song(audio_path)

    try:
        for section in sections:
            pattern_name = section["pattern"]
            start = float(section["start"])
            end = float(section["end"])
            duration = end - start
            if duration <= 0:
                # Skip invalid or zero-length sections
                continue

            # Wait until it's time for this section
            while time.time() - start_time < start:
                time.sleep(0.05)

            print(f"[{start:5.2f}–{end:5.2f}] Running pattern: {pattern_name}")

            # Get any extra options for the pattern
            args = section.get("options", {})

            # Look up the pattern function in patterns.py
            if not hasattr(patterns, pattern_name):
                print(f"WARNING: Pattern '{pattern_name}' not found. Skipping section.")
                continue

            pattern_func = getattr(patterns, pattern_name)

            # Call the pattern. All patterns follow: func(gpio, duration=..., **options)
            pattern_func(gpio, duration=duration, **args)

        # After all sections, wait for music to finish (if still playing)
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    finally:
        print("Show done. Turning everything off.")
        gpio.all_off()
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 show_runner.py <show_yaml_file>")
        sys.exit(1)

    show_file = sys.argv[1]
    print(f"Loading show from {show_file}...")

    show_config, base_dir = load_show(show_file)
    run_show(show_config, base_dir=base_dir)
