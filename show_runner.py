#!/usr/bin/env python3
import os
import time
import yaml
import pygame
import threading
from gpio_controller import GPIOController
import patterns



## Type Convenience



from typing import Tuple, List, Any



## Utility



def beats_to_seconds(beats: float, bpm: float) -> float:
    """
    Converts a number of beats to their durration in seconds.

    Args:
        beats (float): the number of beats being played
        bpm (float): the tempo (beats per minute) of the song

    Returns:
        float: The length of the beats in seconds.
    """

    assert bpm > 0.0, f"invalid bpm ({bpm})"

    return (beats / bpm) * 60.0

def convert_beat_intervals(options, bpm):
    """
    Convert any beat-based interval options to time-based seconds.
    Looks for keys ending in '_interval' or named 'interval' and converts them.
    Returns a new dict with converted values.
    """
    
    converted = {}
    for key, value in options.items():
        if key.endswith('_interval') or key == 'interval':
            ## Convert beats to seconds
            converted[key] = beats_to_seconds(value, bpm)
        else:
            ## Keep other options as-is
            converted[key] = value
    return converted



## Initialization



def load_show(file_path: str) -> Tuple[Any, str]:
    """
    Load a YAML show file and also return the base directory
    so we can resolve the MP3 path relative to the YAML file.
    """
    base_dir: str = os.path.dirname(os.path.abspath(file_path)) or "."

    with open(file_path, "r") as f: show = yaml.safe_load(f)

    return show, base_dir

def play_song(song_path: str) -> float:
    """
    Initialize pygame mixer and start playing the given audio file.
    Returns the start time so we can sync patterns.
    """

    if not os.path.exists(song_path):
        raise FileNotFoundError(f"Audio file not found: {song_path}")

    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100)

    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()
    return time.time()



# Utility





def run_show(show, base_dir="."):
    """
    Run a light show based on a loaded show config.
    Also starts a background timestamp printer so you can
    see the current playback time every second.
    """

    gpio = GPIOController()
    sections = show["sections"]
    audio_file = show["file"]
    bpm = show.get("bpm")

    if bpm is None:
        print("WARNING: No BPM specified in config file. Intervals will be used as-is (in seconds).")
    else:
        print(f"BPM: {bpm} (1 beat = {beats_to_seconds(1, bpm):.6f} seconds)")

    # Resolve MP3 location
    audio_path = os.path.join(base_dir, audio_file)
    print(f"Playing audio: {audio_path}")
    start_time = play_song(audio_path)

    # Start background timestamp thread
    stop_event = threading.Event()
    ts_thread = threading.Thread(
        target=timestamp_printer,
        args=(start_time, stop_event),
        daemon=True,
    )
    ts_thread.start()

    try:
        for section in sections:
            pattern_name = section["pattern"]
            start = float(section["start"])
            end = float(section["end"])
            duration = end - start
            if duration <= 0:
                continue

            # Wait until it is time for this section
            while time.time() - start_time < start:
                time.sleep(0.01)

            print(f"[{start:5.2f}–{end:5.2f}] Running pattern: {pattern_name}")

            args = section.get("options", {})

            # Convert beat-based intervals to seconds if BPM is specified
            if bpm is not None:
                args = convert_beat_intervals(args, bpm)

            if not hasattr(patterns, pattern_name):
                print(f"WARNING: Pattern '{pattern_name}' not found. Skipping.")
                continue

            pattern_func = getattr(patterns, pattern_name)

            # Run the pattern (blocking) for this section's duration
            pattern_func(gpio, duration=duration, **args)

        # After all sections: wait for music to stop
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    finally:
        print("Show done. Turning everything off.")
        gpio.all_off()
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        # Stop timestamp thread
        stop_event.set()
        ts_thread.join(timeout=1.0)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 show_runner.py <show_yaml_file>")
        sys.exit(1)

    show_file = sys.argv[1]
    print(f"Loading show from {show_file}...")
    show_config, base_dir = load_show(show_file)
    run_show(show_config, base_dir=base_dir)
