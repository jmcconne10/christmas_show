#!/usr/bin/env python3
import time
import random

# These are the logical names from channel_map.yaml
TREE_NAMES = ["T1", "T2", "T3", "BigTree"]
BULB_NAMES = ["B1", "B2", "B3", "B4"]

def _safe_on(gpio, name):
    if name in gpio.channels:
        gpio.on(name)

def _safe_off(gpio, name):
    if name in gpio.channels:
        gpio.off(name)

def all_off(gpio):
    gpio.all_off()

def all_on(gpio):
    gpio.all_on()

def blink_all(gpio, duration=5.0, interval=0.5):
    """
    Simple: all lights on, all lights off, repeat.
    """
    end = time.time() + duration
    state = False
    while time.time() < end:
        if state:
            gpio.all_off()
        else:
            gpio.all_on()
        state = not state
        time.sleep(interval)
    gpio.all_off()

def alternate_trees_and_bulbs(gpio, duration=5.0, interval=0.4):
    """
    Trees ON / Bulbs OFF, then Trees OFF / Bulbs ON.
    """
    end = time.time() + duration
    state = False
    while time.time() < end:
        if state:
            # trees on, bulbs off
            for t in TREE_NAMES:
                _safe_on(gpio, t)
            for b in BULB_NAMES:
                _safe_off(gpio, b)
        else:
            # bulbs on, trees off
            for t in TREE_NAMES:
                _safe_off(gpio, t)
            for b in BULB_NAMES:
                _safe_on(gpio, b)
        state = not state
        time.sleep(interval)
    gpio.all_off()

def wave_trees(gpio, duration=5.0, step_interval=0.2):
    """
    Light up trees one after another (T1 -> T2 -> T3 -> BigTree) in a wave.
    """
    end = time.time() + duration
    names = [n for n in TREE_NAMES if n in gpio.channels]
    if not names:
        return
    while time.time() < end:
        for name in names:
            gpio.all_off()
            _safe_on(gpio, name)
            time.sleep(step_interval)
    gpio.all_off()

def wave_all(gpio, duration=5.0, step_interval=0.2):
    """
    Light up trees and bulbs together in sequence:
    T1+B1, then T2+B2, then T3+B3, then BigTree+B4
    """
    end = time.time() + duration
    # Pair trees with bulbs
    pairs = [
        ("T1", "B1"),
        ("T2", "B2"),
        ("T3", "B3"),
        ("BigTree", "B4")
    ]
    # Filter to only include pairs where both channels exist
    valid_pairs = [(t, b) for t, b in pairs 
                   if t in gpio.channels and b in gpio.channels]
    if not valid_pairs:
        return
    
    while time.time() < end:
        for tree, bulb in valid_pairs:
            gpio.all_off()
            _safe_on(gpio, tree)
            _safe_on(gpio, bulb)
            time.sleep(step_interval)
    gpio.all_off()

def trees_cascade(gpio, duration=5.0, step_interval=0.2):
    """
    Cascade effect for trees: turn on one at a time, then turn off one at a time.
    Sequence: T1 on, T2 on, T3 on, T4 on, T1 off, T2 off, T3 off, T4 off, repeat
    """
    end = time.time() + duration
    names = [n for n in TREE_NAMES if n in gpio.channels]
    if not names:
        return
    
    while time.time() < end:
        # Turn on each tree, one at a time (keeping previous ones on)
        for name in names:
            _safe_on(gpio, name)
            time.sleep(step_interval)
        
        # Turn off each tree, one at a time
        for name in names:
            _safe_off(gpio, name)
            time.sleep(step_interval)
    
    gpio.all_off()

def chase_bulbs(gpio, duration=5.0, step_interval=0.15):
    """
    Chase pattern across the 4 bulb channels.
    """
    end = time.time() + duration
    names = [n for n in BULB_NAMES if n in gpio.channels]
    if not names:
        return
    idx = 0
    while time.time() < end:
        gpio.all_off()
        _safe_on(gpio, names[idx % len(names)])
        idx += 1
        time.sleep(step_interval)
    gpio.all_off()

def sparkle(gpio, duration=5.0, interval=0.08, on_fraction=0.5):
    """
    Randomly turn some channels on/off to create a twinkling effect.
    """
    end = time.time() + duration
    all_names = list(gpio.channels.keys())
    if not all_names:
        return
    while time.time() < end:
        for name in all_names:
            if random.random() < on_fraction:
                _safe_on(gpio, name)
            else:
                _safe_off(gpio, name)
        time.sleep(interval)
    gpio.all_off()

def finale_flash(gpio, duration=3.0, interval=0.12):
    """
    Rapid strobe with everything, ending ON briefly, then OFF.
    """
    end = time.time() + duration
    state = False
    while time.time() < end:
        if state:
            gpio.all_on()
        else:
            gpio.all_off()
        state = not state
        time.sleep(interval)
    # Hold everything on for a beat, then off
    gpio.all_on()
    time.sleep(0.5)
    gpio.all_off()