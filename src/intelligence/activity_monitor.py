# activity_monitor.py
# Background monitor for APP and IDLE distractions.
# Runs on a daemon thread alongside the camera so Vision handles face-presence
# distractions while this module handles OS-level signals.
#
# APP_DISTRACTION  — the foreground window belongs to a known distracting site/app
# IDLE_DISTRACTION — no keyboard or mouse input for IDLE_THRESHOLD seconds

import ctypes
import ctypes.wintypes
import time
import threading

from session_manager import DistractionType

# Window titles containing any of these keywords are classified as distracting.
# Matched against the lowercased foreground window title so casing is irrelevant.
_DISTRACTING_KEYWORDS = {
    "youtube", "netflix", "twitch", "hulu", "disney+", "amazon prime video",
    "facebook", "instagram", "tiktok", "twitter", "reddit", "9gag",
    "discord", "whatsapp", "telegram",
    "espn", "nfl", "nba", "mlb",
}


class ActivityMonitor:
    """Polls the OS every POLL_INTERVAL seconds to detect app and idle distractions.

    Usage:
        monitor = ActivityMonitor(session_manager)
        monitor.start()   # non-blocking; spawns a daemon thread
        ...
        monitor.stop()    # flushes any open events then joins the thread
    """

    POLL_INTERVAL    = 5.0    # seconds between OS checks (lower = more responsive, more CPU)
    IDLE_THRESHOLD   = 300.0  # seconds of no keyboard/mouse input before opening an idle event
    DISTRACTION_COOLDOWN = 5.0  # seconds after trigger disappears before the event is finalised

    def __init__(self, session_manager):
        self._session_manager = session_manager

        # APP distraction state — mirrors the cooldown pattern used in camera.py
        self._app_distraction_start: float | None = None  # wall-clock time app event opened
        self._app_last_seen: float | None = None          # last poll where distracting app was in focus

        # IDLE distraction state
        self._idle_distraction_start: float | None = None  # wall-clock time idle event opened
        self._idle_last_seen: float | None = None          # last poll where idle threshold was exceeded

        self._running = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Spawn the background polling thread. Safe to call once per session."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="ActivityMonitor")
        self._thread.start()

    def stop(self):
        """Signal the thread to stop, flush any open events, then join."""
        self._running = False
        if self._thread:
            # Give the thread up to one full poll interval to notice the stop signal
            self._thread.join(timeout=self.POLL_INTERVAL + 1)
        self._flush()

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    def _monitor_loop(self):
        while self._running:
            now = time.time()
            title = self._get_foreground_window_title()
            idle_seconds = self._get_idle_seconds()

            app_detected = self._is_distracting_app(title)
            # Only evaluate idle when there's no app distraction active — app takes priority
            # (same suppression logic as phone > look_away in camera.py)
            is_idle = (not app_detected) and (idle_seconds >= self.IDLE_THRESHOLD)

            self._update_app_tracking(now, app_detected)
            self._update_idle_tracking(now, is_idle)

            time.sleep(self.POLL_INTERVAL)

    # ------------------------------------------------------------------
    # Tracking helpers (same cooldown pattern as camera._update_distraction_tracking)
    # ------------------------------------------------------------------

    def _update_app_tracking(self, now: float, app_detected: bool):
        if app_detected:
            if self._app_distraction_start is None:
                self._app_distraction_start = now  # open event on first poll where app is foreground
            self._app_last_seen = now
        elif self._app_distraction_start is not None:
            if now - self._app_last_seen >= self.DISTRACTION_COOLDOWN:
                duration = max(1, int(self._app_last_seen - self._app_distraction_start))
                try:
                    self._session_manager.log_distraction(DistractionType.APP_DISTRACTION, duration)
                except Exception:
                    pass  # Session may not be IN_PROGRESS; never crash the monitor thread
                self._app_distraction_start = None
                self._app_last_seen = None

    def _update_idle_tracking(self, now: float, is_idle: bool):
        if is_idle:
            if self._idle_distraction_start is None:
                self._idle_distraction_start = now  # open event once idle threshold is crossed
            self._idle_last_seen = now
        elif self._idle_distraction_start is not None:
            if now - self._idle_last_seen >= self.DISTRACTION_COOLDOWN:
                duration = max(1, int(self._idle_last_seen - self._idle_distraction_start))
                try:
                    self._session_manager.log_distraction(DistractionType.IDLE_DISTRACTION, duration)
                except Exception:
                    pass
                self._idle_distraction_start = None
                self._idle_last_seen = None

    # ------------------------------------------------------------------
    # Flush on shutdown
    # ------------------------------------------------------------------

    def _flush(self):
        """Log any in-progress events before the monitor shuts down."""
        if self._app_distraction_start is not None:
            end = self._app_last_seen or time.time()
            duration = max(1, int(end - self._app_distraction_start))
            try:
                self._session_manager.log_distraction(DistractionType.APP_DISTRACTION, duration)
            except Exception:
                pass
            self._app_distraction_start = None
            self._app_last_seen = None

        if self._idle_distraction_start is not None:
            end = self._idle_last_seen or time.time()
            duration = max(1, int(end - self._idle_distraction_start))
            try:
                self._session_manager.log_distraction(DistractionType.IDLE_DISTRACTION, duration)
            except Exception:
                pass
            self._idle_distraction_start = None
            self._idle_last_seen = None

    # ------------------------------------------------------------------
    # OS helpers (Windows — ctypes only, no extra packages)
    # ------------------------------------------------------------------

    def _get_foreground_window_title(self) -> str:
        """Return the title of the currently focused window, lowercased."""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
            buf = ctypes.create_unicode_buffer(length)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length)
            return buf.value.lower()
        except Exception:
            return ""

    def _get_idle_seconds(self) -> float:
        """Return seconds elapsed since the last keyboard or mouse input (Windows)."""
        try:
            class _LASTINPUTINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.wintypes.UINT),
                    ("dwTime", ctypes.wintypes.DWORD),
                ]

            info = _LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
            # Both GetTickCount() and dwTime are milliseconds since system boot
            elapsed_ms = ctypes.windll.kernel32.GetTickCount() - info.dwTime
            return elapsed_ms / 1000.0
        except Exception:
            return 0.0

    @staticmethod
    def _is_distracting_app(title: str) -> bool:
        """True if any distracting keyword appears in the window title."""
        return any(keyword in title for keyword in _DISTRACTING_KEYWORDS)
