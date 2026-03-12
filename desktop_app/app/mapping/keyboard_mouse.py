from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Dict, Set

from app.core.models import MouseButtonName

# Win32 SendInput constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

MAPVK_VK_TO_VSC = 0

user32 = ctypes.WinDLL("user32", use_last_error=True)


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUTUNION),
    ]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT
user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
user32.MapVirtualKeyW.restype = wintypes.UINT
user32.VkKeyScanW.argtypes = (wintypes.WCHAR,)
user32.VkKeyScanW.restype = ctypes.c_short


_SPECIAL_VK: Dict[str, int] = {
    "space": 0x20,
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "tab": 0x09,
    "shift": 0x10,
    "shift_l": 0xA0,
    "shift_r": 0xA1,
    "ctrl": 0x11,
    "control": 0x11,
    "ctrl_l": 0xA2,
    "ctrl_r": 0xA3,
    "alt": 0x12,
    "alt_l": 0xA4,
    "alt_r": 0xA5,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "backspace": 0x08,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "insert": 0x2D,
}

_EXTENDED_KEYS = {
    0xA3,  # RCTRL
    0xA5,  # RALT
    0x25, 0x26, 0x27, 0x28,  # arrows
    0x21, 0x22, 0x23, 0x24,  # pgup/down, end, home
    0x2D, 0x2E,  # insert, delete
}


def _send_input(*inputs: INPUT) -> None:
    if not inputs:
        return
    array_type = INPUT * len(inputs)
    sent = user32.SendInput(len(inputs), array_type(*inputs), ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise ctypes.WinError(ctypes.get_last_error())


def _keyboard_input(scan_code: int, key_up: bool = False, extended: bool = False) -> INPUT:
    flags = KEYEVENTF_SCANCODE
    if key_up:
        flags |= KEYEVENTF_KEYUP
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    return INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, scan_code, flags, 0, None))


def _mouse_input(flags: int, dx: int = 0, dy: int = 0) -> INPUT:
    return INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(dx, dy, 0, flags, 0, None))


def _vk_to_scan_code(vk: int) -> int:
    return int(user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC))


def _resolve_key_spec(name: str) -> tuple[int, bool]:
    lowered = name.strip().lower()

    if lowered in _SPECIAL_VK:
        vk = _SPECIAL_VK[lowered]
        return _vk_to_scan_code(vk), vk in _EXTENDED_KEYS

    if lowered.startswith("f") and lowered[1:].isdigit():
        fn_num = int(lowered[1:])
        if 1 <= fn_num <= 24:
            vk = 0x6F + fn_num
            return _vk_to_scan_code(vk), False

    if len(lowered) == 1:
        vk_with_shift = int(user32.VkKeyScanW(lowered))
        if vk_with_shift == -1:
            raise ValueError(f"Unsupported key mapping: {name!r}")
        vk = vk_with_shift & 0xFF
        return _vk_to_scan_code(vk), False

    raise ValueError(f"Unsupported key mapping: {name!r}")


class KeyboardMouseInjector:
    def __init__(self) -> None:
        self._held_keys: Set[str] = set()
        self._held_mouse_buttons: Set[MouseButtonName] = set()

    def tap_key(self, key_name: str) -> None:
        scan_code, extended = _resolve_key_spec(key_name)
        _send_input(
            _keyboard_input(scan_code, key_up=False, extended=extended),
            _keyboard_input(scan_code, key_up=True, extended=extended),
        )

    def hold_key(self, key_name: str) -> None:
        if key_name in self._held_keys:
            return
        scan_code, extended = _resolve_key_spec(key_name)
        _send_input(_keyboard_input(scan_code, key_up=False, extended=extended))
        self._held_keys.add(key_name)

    def release_key(self, key_name: str) -> None:
        if key_name not in self._held_keys:
            return
        scan_code, extended = _resolve_key_spec(key_name)
        _send_input(_keyboard_input(scan_code, key_up=True, extended=extended))
        self._held_keys.discard(key_name)

    def click_mouse(self, button_name: MouseButtonName) -> None:
        down_flag, up_flag = self._resolve_mouse_flags(button_name)
        _send_input(_mouse_input(down_flag), _mouse_input(up_flag))

    def hold_mouse_button(self, button_name: MouseButtonName) -> None:
        if button_name in self._held_mouse_buttons:
            return
        down_flag, _ = self._resolve_mouse_flags(button_name)
        _send_input(_mouse_input(down_flag))
        self._held_mouse_buttons.add(button_name)

    def release_mouse_button(self, button_name: MouseButtonName) -> None:
        if button_name not in self._held_mouse_buttons:
            return
        _, up_flag = self._resolve_mouse_flags(button_name)
        _send_input(_mouse_input(up_flag))
        self._held_mouse_buttons.discard(button_name)

    def move_mouse(self, dx: int = 0, dy: int = 0) -> None:
        if dx or dy:
            _send_input(_mouse_input(MOUSEEVENTF_MOVE, dx=dx, dy=dy))

    def release_all(self) -> None:
        for key_name in list(self._held_keys):
            self.release_key(key_name)
        for button_name in list(self._held_mouse_buttons):
            self.release_mouse_button(button_name)

    @staticmethod
    def _resolve_mouse_flags(name: MouseButtonName) -> tuple[int, int]:
        return {
            "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
            "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
            "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
        }[name]
