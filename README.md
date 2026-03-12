# Serial Joystick Keymapper

Arduino Nano firmware and a Windows desktop app to read a custom-wired joystick over serial and map its buttons and analog sticks to keyboard and mouse input.

## Overview

This project bridges a custom joystick wired to an **Arduino Nano** with a **Windows 11** desktop application.

The Arduino reads:

- 4 digital buttons
- 2 analog sticks (4 analog axes total)

It then sends the raw state to the PC over USB serial.

The Python desktop application provides:

- a live joystick test/calibration interface similar to the Windows joystick properties panel
- calibration tools for each axis
- configurable button and axis mapping
- keyboard and mouse input emulation
- JSON-based profiles for different games
- background operation while minimized
- a panic stop to disable input mapping immediately

## Main Use Case

Some games do not accept MIDI devices or custom HID controllers, but they do accept keyboard and mouse input.

This project allows a custom joystick to be interpreted as:

- keyboard key presses
- held keys
- mouse movement
- mouse button clicks

while preserving analog joystick input for calibration and flexible mapping.

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
- Run while minimized
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

### Expected Inputs

- 4 digital buttons
- 4 analog channels:
- Stick 1 X
- Stick 1 Y
- Stick 2 X
- Stick 2 Y

### Suggested Pin Mapping

```c++
const uint8_t BTN1_PIN = 2;
const uint8_t BTN2_PIN = 3;
const uint8_t BTN3_PIN = 4;
const uint8_t BTN4_PIN = 5;

const uint8_t STICK1_X_PIN = A0;
const uint8_t STICK1_Y_PIN = A1;
const uint8_t STICK2_X_PIN = A2;
const uint8_t STICK2_Y_PIN = A3;
```

This mapping is intentionally simple. Adjust it to match your wiring.

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
- b1..b4 are button states (0 or 1)
- s1x, s1y, s2x, s2y are analog readings (0..1023)

## Architecture

This project deliberately keeps the Arduino firmware simple.

### Arduino responsibilities

- read pins
- debounce buttons
- sample analog inputs
- send raw state over serial

### Desktop app responsibilities
- parse serial frames
- display live joystick state
- calibrate axes
- apply deadzones and sensitivity
- map joystick inputs to keyboard/mouse output
- save and load profiles

This separation avoids reflashing the Arduino whenever a game mapping changes.

#### Desktop App Requirements
- Windows 11
- Python 3.11+ recommended

##### Recommended Python stack
- PySide6
- pyserial

Potential additional dependency:
- a Windows input injection layer based on SendInput

## Getting Started

### 1. Flash the Arduino firmware

Upload the sketch in:
```
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
### 5. Select the serial port
- Choose the Arduino COM port
- Connect
- Verify that button and stick states update live

### 6. Calibrate
For each axis:
- center the stick
- capture center
- move to extremes
- capture min/max
- set deadzone and inversion as needed

### 7. Create mappings

Examples:

- Stick 1 X -> `A` / `D`
- Stick 1 Y -> `W` / `S`
- Stick 2 X/Y -> `mouse movement`
- Button 1 -> `Space`
- Button 2 -> `E`
- Button 3 -> `left mouse`
- Button 4 -> `right mouse`

### 8. Save profile

Store the configuration as JSON and reload it later for a specific game.

Example Profile Concept
```json
{
  "profile_name": "Space Game",
  "serial": {
    "port": "COM5",
    "baudrate": 230400
  },
  "buttons": {
    "btn1": { "mode": "keyboard", "key": "space", "behavior": "hold" },
    "btn2": { "mode": "keyboard", "key": "e", "behavior": "press" }
  },
  "axes": {
    "stick1_x": {
      "mode": "digital_axis",
      "negative_key": "a",
      "positive_key": "d"
    },
    "stick1_y": {
      "mode": "digital_axis",
      "negative_key": "w",
      "positive_key": "s"
    },
    "stick2_x": {
      "mode": "mouse_axis",
      "target": "mouse_x"
    },
    "stick2_y": {
      "mode": "mouse_axis",
      "target": "mouse_y"
    }
  }
}
```
## Safety Notes

This application can generate real keyboard and mouse events on the system.

### Recommended safeguards:

- keep a visible global enable/disable toggle
- include a panic stop button
- optionally define a keyboard emergency shortcut in future versions

## Limitations

- Designed for Windows 11
- Depends on stable serial communication
- Not presented as a USB HID joystick device
- Requires the desktop application to be running for mappings to work
