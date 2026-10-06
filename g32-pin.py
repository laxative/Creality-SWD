import lgpio
import time
import sys
import subprocess
import os

BOOT0 = 27 #GPIO PINS ON HAT GOING TO BOOT0 and RST / RESET
RESET = 22

# Update these to match your setup
KATAPULT_DIR = "/home/pi/katapult"  # path to your katapult directory
KLIPPER_BIN = "/home/pi/klipper/out/klipper.bin"  # path to compiled klipper binary
SERIAL_PORT = "/dev/serial0"  # or /dev/ttyAMA0, /dev/ttyUSB0 etc.
BAUD_RATE = "230400"

h = lgpio.gpiochip_open(4)
lgpio.gpio_claim_output(h, BOOT0)
lgpio.gpio_claim_output(h, RESET)

def boot_application():
    print("Booting into application (Klipper)...")
    lgpio.gpio_write(h, BOOT0, 0)
    lgpio.gpio_write(h, RESET, 0)
    time.sleep(0.5)
    lgpio.gpio_write(h, RESET, 1)
    time.sleep(0.1)
    print("Done - GD32 should now be running Klipper")

def boot_bootloader():
    print("Booting into factory bootloader...")
    lgpio.gpio_write(h, BOOT0, 1)
    lgpio.gpio_write(h, RESET, 0)
    time.sleep(0.5)
    lgpio.gpio_write(h, RESET, 1)
    time.sleep(0.1)
    print("Done - GD32 is now in factory bootloader mode")

def reboot():
    print("Rebooting GD32...")
    lgpio.gpio_write(h, BOOT0, 0)
    lgpio.gpio_write(h, RESET, 0)
    time.sleep(0.5)
    lgpio.gpio_write(h, RESET, 1)
    time.sleep(0.1)
    print("Done - GD32 rebooted")

def flash_katapult():
    print("Entering Katapult bootloader via double-reset...")

    # First reset
    lgpio.gpio_write(h, BOOT0, 0)
    lgpio.gpio_write(h, RESET, 0)
    time.sleep(0.1)
    lgpio.gpio_write(h, RESET, 1)
    time.sleep(0.4)  # wait within double-reset window

    # Second reset
    lgpio.gpio_write(h, RESET, 0)
    time.sleep(0.1)
    lgpio.gpio_write(h, RESET, 1)
    time.sleep(0.5)  # give Katapult time to initialize

    print("Attempting to flash via Katapult...")

    if not os.path.exists(KLIPPER_BIN):
        print(f"Error: Klipper binary not found at {KLIPPER_BIN}")
        print("Run 'make' in the klipper directory first")
        return

    flash_script = os.path.join(KATAPULT_DIR, "scripts", "flash_can.py")
    if not os.path.exists(flash_script):
        print(f"Error: flash_can.py not found at {flash_script}")
        return

    cmd = [
        "python3", flash_script,
        "-d", SERIAL_PORT,
        "-b", BAUD_RATE,
        "-f", KLIPPER_BIN
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        print("Flash successful! Rebooting into Klipper...")
        time.sleep(0.5)
        boot_application()
    else:
        print("Flash failed. Check connections and try again.")

# --- CLI ---
usage = """
Usage:
  python3 gd32_boot.py app        -> boot into Klipper
  python3 gd32_boot.py bootloader -> boot into factory bootloader
  python3 gd32_boot.py reboot     -> reboot the board
  python3 gd32_boot.py flash      -> flash Klipper via Katapult
"""

if len(sys.argv) < 2:
    print(usage)
else:
    cmd = sys.argv[1]
    if cmd == "app":
        boot_application()
    elif cmd == "bootloader":
        boot_bootloader()
    elif cmd == "reboot":
        reboot()
    elif cmd == "flash":
        flash_katapult()
    else:
        print(f"Unknown argument: '{cmd}'")
        print(usage)

lgpio.gpiochip_close(h)
