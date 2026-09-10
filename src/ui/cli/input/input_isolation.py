"""Optional Windows low-level keyboard isolation.

The hook suppresses physical keys handled by the application while allowing
events marked as injected (the playback output) to reach the target program.
"""

from __future__ import annotations

import ctypes
import os
from collections.abc import Callable, Iterable
from typing import Any, cast
from ctypes import wintypes


class WindowsInputIsolation:
    """Best-effort WH_KEYBOARD_LL hook with safe non-Windows fallback."""

    LLKHF_INJECTED = 0x10
    WH_KEYBOARD_LL = 13
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_SYSKEYDOWN = 0x0104
    WM_SYSKEYUP = 0x0105

    def __init__(
        self, scan_codes: Iterable[int], on_key: Callable[[int], None] | None = None
    ) -> None:
        self.scan_codes = {int(code) for code in scan_codes if int(code) > 0}
        self.on_key = on_key
        self._hook = None
        self._callback = None
        self._thread_id = 0

    @property
    def supported(self) -> bool:
        return os.name == "nt"

    def should_suppress(self, scan_code: int, *, injected: bool = False) -> bool:
        """Return whether a low-level event should be blocked."""
        return not injected and int(scan_code) in self.scan_codes

    def start(self) -> bool:
        if not self.supported or self._hook is not None:
            return False if not self.supported else True
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            result_type = getattr(wintypes, "LRESULT", ctypes.c_long)
            pointer_type = getattr(wintypes, "ULONG_PTR", ctypes.c_void_p)
            hook_proc = ctypes.WINFUNCTYPE(
                result_type,
                ctypes.c_int,
                wintypes.WPARAM,
                wintypes.LPARAM,
            )

            class KBDLLHOOKSTRUCT(ctypes.Structure):
                _fields_ = [
                    ("vkCode", wintypes.DWORD),
                    ("scanCode", wintypes.DWORD),
                    ("flags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", pointer_type),
                ]

            def callback(n_code: int, w_param: int, l_param: int) -> int:
                if n_code < 0:
                    return int(
                        user32.CallNextHookEx(self._hook, n_code, w_param, l_param)
                    )
                data = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if data.flags & self.LLKHF_INJECTED:
                    return int(
                        user32.CallNextHookEx(self._hook, n_code, w_param, l_param)
                    )
                if self.should_suppress(int(data.scanCode)) and w_param in {
                    self.WM_KEYDOWN,
                    self.WM_SYSKEYDOWN,
                }:
                    if self.on_key:
                        self.on_key(int(data.scanCode))
                    return 1
                if self.should_suppress(int(data.scanCode)) and w_param in {
                    self.WM_KEYUP,
                    self.WM_SYSKEYUP,
                }:
                    return 1
                return int(user32.CallNextHookEx(self._hook, n_code, w_param, l_param))

            self._callback = cast(Any, hook_proc(callback))
            self._thread_id = kernel32.GetCurrentThreadId()
            self._hook = user32.SetWindowsHookExW(
                self.WH_KEYBOARD_LL, self._callback, kernel32.GetModuleHandleW(None), 0
            )
            return bool(self._hook)
        except (AttributeError, OSError, TypeError, ValueError):
            self._hook = None
            self._callback = None
            return False

    def stop(self) -> None:
        if self._hook is not None:
            try:
                ctypes.windll.user32.UnhookWindowsHookEx(self._hook)
            except (AttributeError, OSError):
                pass
            self._hook = None
            self._callback = None

    def pump(self) -> None:
        """Dispatch pending Windows messages for the installing thread."""
        if not self.supported or self._hook is None:
            return
        try:
            msg = wintypes.MSG()
            user32 = ctypes.windll.user32
            peek = getattr(user32, "PeekMessageW")
            while peek(ctypes.byref(msg), None, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except (AttributeError, OSError, TypeError):
            return
