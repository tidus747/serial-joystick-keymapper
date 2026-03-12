# Serial Joystick Keymapper

Arduino Nano firmware and a Windows desktop app to read a custom-wired joystick over serial and map its buttons and analog sticks to keyboard and mouse input.

## Overview

This project bridges a custom joystick wired to an **Arduino Nano** with a **Windows 11** desktop application.

The Arduino reads:

- 4 digital buttons
- 2 analog sticks (4 analog axes total)

It then sends the raw state to the PC over USB serial.

The Python desktop application provides:

- a live joystick test/calibration interface inspired by the Windows joystick properties panel
- calibration tools for each axis
- configurable button and axis mapping
- keyboard and mouse input emulation
- JSON-based profiles for different games
- background operation while minimized to the system tray
- a panic stop to disable input mapping immediately

## Features

### Firmware
- Reads 4 digital buttons
- Reads 4 analog channels
- Sends joystick state over serial
- Lightweight and easy to customize
- Keeps hardware logic simple and pushes calibration/mapping to the desktop app

### Desktop App
- Windows-style joystick monitoring interface
- Live display of:
  - Button 1-4
  - Stick 1 X/Y
  - Stick 2 X/Y
- Per-axis calibration:
  - min
  - center
  - max
  - deadzone
  - invert
  - sensitivity
  - curve/expo
- Mapping modes:
  - button -> keyboard
  - button -> mouse click
  - axis -> keyboard thresholds
  - axis -> mouse movement
- JSON profile save/load
- Run while minimized to tray
- Global enable/disable mapping
- Panic stop

## Project Structure

```text
serial-joystick-keymapper/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ firmware/
│  └─ nano_serial_joystick/
│     └─ nano_serial_joystick.ino
├─ desktop_app/
│  ├─ pyproject.toml
│  ├─ requirements.txt
│  ├─ main.py
│  ├─ app/
│  │  ├─ ui/
│  │  │  ├─ main_window.py
│  │  │  ├─ widgets/
│  │  │  │  ├─ stick_widget.py
│  │  │  │  ├─ button_indicator.py
│  │  │  │  └─ calibration_panel.py
│  │  ├─ serial/
│  │  │  ├─ serial_reader.py
│  │  │  └─ protocol.py
│  │  ├─ mapping/
│  │  │  ├─ actions.py
│  │  │  ├─ keyboard_mouse.py
│  │  │  └─ axis_processing.py
│  │  ├─ profiles/
│  │  │  ├─ profile_manager.py
│  │  │  └─ schema.py
│  │  └─ core/
│  │     ├─ models.py
│  │     ├─ state_store.py
│  │     └─ controller.py
│  └─ profiles/
│     └─ example_profile.json
└─ docs/
   ├─ protocol.md
   ├─ calibration.md
   └─ roadmap.md
```

## Hardware

### Target Board
- Arduino Nano

### Suggested Pin Mapping

```cpp
const uint8_t BTN1_PIN = 2;
const uint8_t BTN2_PIN = 3;
const uint8_t BTN3_PIN = 4;
const uint8_t BTN4_PIN = 5;

const uint8_t STICK1_X_PIN = A0;
const uint8_t STICK1_Y_PIN = A1;
const uint8_t STICK2_X_PIN = A2;
const uint8_t STICK2_Y_PIN = A3;
```

Adjust these pins to match your wiring.

## Serial Protocol

The firmware sends newline-delimited frames in text format:

```text
T,<b1>,<b2>,<b3>,<b4>,<s1x>,<s1y>,<s2x>,<s2y>\n
```

Example:

```text
T,0,1,0,0,512,498,1023,14
```

Where:

- `b1..b4` are button states (`0` or `1`)
- `s1x, s1y, s2x, s2y` are analog readings (`0..1023`)

## Requirements

- Windows 11
- Python 3.11+
- Arduino Nano

## Installation

### 1. Flash the Arduino firmware
Upload the sketch in:

```text
firmware/nano_serial_joystick/nano_serial_joystick.ino
```

### 2. Create a Python virtual environment

```bash
cd desktop_app
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python main.py
```

## Safety Notes

This application can generate real keyboard and mouse events on the system.

Recommended safeguards:

- keep the visible global enable/disable toggle in mind
- use the panic stop in the toolbar or tray menu
- start with harmless test bindings first
- avoid binding movement keys or mouse actions until calibration is correct

## Known Limitations

- Designed for Windows 11
- Depends on stable serial communication
- Not presented as a USB HID joystick device
- Requires the desktop application to be running for mappings to work
- Some games may react differently to synthetic keyboard/mouse events depending on anti-cheat or input backend

## License

This project is released under the MIT License. See the `LICENSE` file for details.
