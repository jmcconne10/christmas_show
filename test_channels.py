#!/usr/bin/env python3

import time
import yaml
from gpiozero import OutputDevice

CHANNEL_ORDER = [
    ("CH1 - T1 (Small Tree 1)", "T1"),
    ("CH2 - T2 (Small Tree 2)", "T2"),
    ("CH3 - T3 (Small Tree 3)", "T3"),
    ("CH4 - BigTree (Large Tree)", "BigTree"),
    ("CH5 - B1 (Bulbs 1)", "B1"),
    ("CH6 - B2 (Bulbs 2)", "B2"),
    ("CH7 - B3 (Bulbs 3)", "B3"),
    ("CH8 - B4 (Bulbs 4)", "B4"),
]

def load_channel_map(path="channel_map.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_gpio_for_zone(channel_map, zone_key):
    # Trees are under channel_map["trees"], bulbs under channel_map["bulbs"]
    trees = channel_map.get("trees", {})
    bulbs = channel_map.get("bulbs", {})

    if zone_key in trees:
        return trees[zone_key]
    if zone_key in bulbs:
        return bulbs[zone_key]

    raise KeyError(f"Zone key '{zone_key}' not found in channel_map")

def main():
    channel_map = load_channel_map()

    devices = []
    for label, zone_key in CHANNEL_ORDER:
        gpio_pin = get_gpio_for_zone(channel_map, zone_key)
        dev = OutputDevice(gpio_pin, active_high=True, initial_value=False)
        devices.append((label, dev))

    try:
        # Make sure everything starts OFF
        for _, dev in devices:
            dev.off()

        print("Channel test starting.")
        print("You will be asked to plug a lamp into each channel in turn.")
        print("Press Ctrl+C at any time to exit.\n")

        for label, dev in devices:
            input(f"➡️  Plug the lamp into: {label}, then press Enter...")
            print(f"   Turning ON {label}...")
            dev.on()
            print("   Lamp SHOULD BE ON now.")
            input("   Press Enter to turn it OFF and move to the next channel...")
            dev.off()
            print(f"   {label} OFF.\n")
            time.sleep(0.5)

        print("✅ Channel test complete. All channels OFF.")

    except KeyboardInterrupt:
        print("\nInterrupted by user, turning everything OFF...")
    finally:
        for _, dev in devices:
            dev.off()
        print("All outputs set to OFF. Goodbye.")

if __name__ == "__main__":
    main()
