import argparse
import ctypes
import math
import os
import struct
import subprocess
import sys
import time
from ctypes import wintypes

if sys.platform != "win32":
    sys.exit("This script only runs on Windows.")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
hid = ctypes.WinDLL("hid", use_last_error=True)

try:
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

WM_NULL = 0x0000
WM_INPUT = 0x00FF
WM_TIMER = 0x0113
WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WM_APP = 0x8000
WM_TRAYICON = WM_APP + 1
WM_RBUTTONUP = 0x0205
WM_LBUTTONUP = 0x0202
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIDI_PREPARSEDDATA = 0x20000005
RIM_TYPEHID = 2
GA_ROOT = 2
SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE = 0x0001, 0x0004, 0x0010
SWP_ASYNCWINDOWPOS = 0x4000
MOVE_FLAGS = SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_ASYNCWINDOWPOS
SW_MAXIMIZE, SW_RESTORE = 3, 9
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
MONITOR_DEFAULTTONEAREST = 2
GWL_STYLE = -16
WS_MAXIMIZEBOX = 0x00010000
WS_EX_TOOLWINDOW = 0x00000080
HIDP_STATUS_SUCCESS = 0x00110000
HID_INPUT = 0

NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP = 0x1, 0x2, 0x4
MF_STRING, MF_GRAYED, MF_SEPARATOR = 0x0, 0x1, 0x800
TPM_RIGHTBUTTON, TPM_RETURNCMD, TPM_BOTTOMALIGN = 0x2, 0x100, 0x20
IDI_APPLICATION = 32512
ID_ELEVATE, ID_QUIT = 1001, 1002

PAGE_GENERIC, PAGE_DIGITIZER = 0x01, 0x0D
USAGE_X, USAGE_Y = 0x30, 0x31
USAGE_TIP, USAGE_CONTACT_ID, USAGE_CONTACT_COUNT = 0x42, 0x51, 0x54
USAGE_TOUCHPAD = 0x05

SHELL_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"}

DEADZONE_PX = 12
SNAP_EDGE_PX = 4

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HANDLE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HANDLE),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_ubyte * 16),
        ("hBalloonIcon", wintypes.HANDLE),
    ]


class HIDP_CAPS(ctypes.Structure):
    _fields_ = [
        ("Usage", wintypes.USHORT),
        ("UsagePage", wintypes.USHORT),
        ("InputReportByteLength", wintypes.USHORT),
        ("OutputReportByteLength", wintypes.USHORT),
        ("FeatureReportByteLength", wintypes.USHORT),
        ("Reserved", wintypes.USHORT * 17),
        ("NumberLinkCollectionNodes", wintypes.USHORT),
        ("NumberInputButtonCaps", wintypes.USHORT),
        ("NumberInputValueCaps", wintypes.USHORT),
        ("NumberInputDataIndices", wintypes.USHORT),
        ("NumberOutputButtonCaps", wintypes.USHORT),
        ("NumberOutputValueCaps", wintypes.USHORT),
        ("NumberOutputDataIndices", wintypes.USHORT),
        ("NumberFeatureButtonCaps", wintypes.USHORT),
        ("NumberFeatureValueCaps", wintypes.USHORT),
        ("NumberFeatureDataIndices", wintypes.USHORT),
    ]


class HIDP_VALUE_CAPS(ctypes.Structure):
    _fields_ = [
        ("UsagePage", wintypes.USHORT),
        ("ReportID", ctypes.c_ubyte),
        ("IsAlias", ctypes.c_ubyte),
        ("BitField", wintypes.USHORT),
        ("LinkCollection", wintypes.USHORT),
        ("LinkUsage", wintypes.USHORT),
        ("LinkUsagePage", wintypes.USHORT),
        ("IsRange", ctypes.c_ubyte),
        ("IsStringRange", ctypes.c_ubyte),
        ("IsDesignatorRange", ctypes.c_ubyte),
        ("IsAbsolute", ctypes.c_ubyte),
        ("HasNull", ctypes.c_ubyte),
        ("Reserved", ctypes.c_ubyte),
        ("BitSize", wintypes.USHORT),
        ("ReportCount", wintypes.USHORT),
        ("Reserved2", wintypes.USHORT * 5),
        ("UnitsExp", wintypes.ULONG),
        ("Units", wintypes.ULONG),
        ("LogicalMin", wintypes.LONG),
        ("LogicalMax", wintypes.LONG),
        ("PhysicalMin", wintypes.LONG),
        ("PhysicalMax", wintypes.LONG),
        ("Usage", wintypes.USHORT),
        ("UsageMax", wintypes.USHORT),
        ("Rest", wintypes.USHORT * 6),
    ]


assert ctypes.sizeof(HIDP_VALUE_CAPS) == 72 or ctypes.sizeof(ctypes.c_void_p) == 4

HEADER_SIZE = ctypes.sizeof(RAWINPUTHEADER)

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HANDLE, wintypes.HANDLE, ctypes.c_void_p,
]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
user32.RegisterWindowMessageW.restype = wintypes.UINT
user32.RegisterRawInputDevices.argtypes = [ctypes.POINTER(RAWINPUTDEVICE), wintypes.UINT, wintypes.UINT]
user32.RegisterRawInputDevices.restype = wintypes.BOOL
user32.GetRawInputData.argtypes = [ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p,
                                   ctypes.POINTER(wintypes.UINT), wintypes.UINT]
user32.GetRawInputData.restype = wintypes.UINT
user32.GetRawInputDeviceInfoW.argtypes = [wintypes.HANDLE, wintypes.UINT, ctypes.c_void_p,
                                          ctypes.POINTER(wintypes.UINT)]
user32.GetRawInputDeviceInfoW.restype = wintypes.UINT
user32.SetTimer.argtypes = [wintypes.HWND, ctypes.c_size_t, wintypes.UINT, ctypes.c_void_p]
user32.SetTimer.restype = ctypes.c_size_t
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int
user32.WindowFromPoint.argtypes = [wintypes.POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.IsZoomed.argtypes = [wintypes.HWND]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
user32.MonitorFromPoint.restype = wintypes.HANDLE
user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
user32.GetMonitorInfoW.restype = wintypes.BOOL
user32.CreatePopupMenu.restype = ctypes.c_void_p
user32.AppendMenuW.argtypes = [ctypes.c_void_p, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
user32.AppendMenuW.restype = wintypes.BOOL
user32.TrackPopupMenu.argtypes = [ctypes.c_void_p, wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, wintypes.HWND, ctypes.c_void_p]
user32.TrackPopupMenu.restype = wintypes.UINT
user32.DestroyMenu.argtypes = [ctypes.c_void_p]
user32.DestroyMenu.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.LoadIconW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
user32.LoadIconW.restype = ctypes.c_void_p
user32.DestroyIcon.argtypes = [ctypes.c_void_p]
shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL
shell32.ExtractIconW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.UINT]
shell32.ExtractIconW.restype = ctypes.c_void_p
shell32.ShellExecuteW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                  wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_int]
shell32.ShellExecuteW.restype = ctypes.c_void_p
shell32.IsUserAnAdmin.restype = wintypes.BOOL
kernel32.GetModuleHandleW.restype = wintypes.HANDLE

hid.HidP_GetCaps.argtypes = [ctypes.c_void_p, ctypes.POINTER(HIDP_CAPS)]
hid.HidP_GetCaps.restype = ctypes.c_long
hid.HidP_GetValueCaps.argtypes = [ctypes.c_int, ctypes.POINTER(HIDP_VALUE_CAPS),
                                  ctypes.POINTER(wintypes.USHORT), ctypes.c_void_p]
hid.HidP_GetValueCaps.restype = ctypes.c_long
hid.HidP_GetUsageValue.argtypes = [ctypes.c_int, wintypes.USHORT, wintypes.USHORT, wintypes.USHORT,
                                   ctypes.POINTER(wintypes.ULONG), ctypes.c_void_p,
                                   ctypes.c_char_p, wintypes.ULONG]
hid.HidP_GetUsageValue.restype = ctypes.c_long
hid.HidP_GetUsages.argtypes = [ctypes.c_int, wintypes.USHORT, wintypes.USHORT,
                               ctypes.POINTER(wintypes.USHORT), ctypes.POINTER(wintypes.ULONG),
                               ctypes.c_void_p, ctypes.c_char_p, wintypes.ULONG]
hid.HidP_GetUsages.restype = ctypes.c_long


def _ok(status):
    return (status & 0xFFFFFFFF) == HIDP_STATUS_SUCCESS


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def say(*a):
    if sys.stdout is not None:
        try:
            print(*a, flush=True)
        except Exception:
            pass


def is_admin():
    try:
        return bool(shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_elevated():
    args = sys.argv[1:]
    if getattr(sys, "frozen", False):
        exe = sys.executable
        params = subprocess.list2cmdline(args)
    else:
        exe = sys.executable
        params = subprocess.list2cmdline([os.path.abspath(sys.argv[0])] + args)
    result = shell32.ShellExecuteW(None, "runas", exe, params or None, None, 1)
    return (result or 0) > 32


class TrayIcon:
    def __init__(self, hwnd, tip):
        self.hwnd = hwnd
        self.tip = tip
        self.owns_icon = False
        self.hicon = None
        if getattr(sys, "frozen", False):
            h = shell32.ExtractIconW(kernel32.GetModuleHandleW(None), sys.executable, 0)
            if h and h > 1:
                self.hicon = h
                self.owns_icon = True
        if not self.hicon:
            self.hicon = user32.LoadIconW(None, ctypes.c_void_p(IDI_APPLICATION))

    def _data(self):
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = self.hicon
        nid.szTip = self.tip[:127]
        return nid

    def add(self):
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(self._data()))

    def remove(self):
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._data()))
        if self.owns_icon and self.hicon:
            user32.DestroyIcon(self.hicon)
            self.hicon = None
            self.owns_icon = False

    def show_menu(self):
        admin = is_admin()
        menu = user32.CreatePopupMenu()
        if admin:
            user32.AppendMenuW(menu, MF_STRING | MF_GRAYED, ID_ELEVATE, "Running as administrator")
        else:
            user32.AppendMenuW(menu, MF_STRING, ID_ELEVATE, "Restart as administrator")
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, ID_QUIT, "Quit")
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        user32.SetForegroundWindow(self.hwnd)
        cmd = user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_RETURNCMD | TPM_BOTTOMALIGN,
                                    pt.x, pt.y, 0, self.hwnd, None)
        user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        user32.DestroyMenu(menu)
        return cmd


class Touchpad:
    def __init__(self, hdevice):
        size = wintypes.UINT(0)
        user32.GetRawInputDeviceInfoW(hdevice, RIDI_PREPARSEDDATA, None, ctypes.byref(size))
        if size.value == 0:
            raise RuntimeError("no preparsed data")
        self.ppd = ctypes.create_string_buffer(size.value)
        if user32.GetRawInputDeviceInfoW(hdevice, RIDI_PREPARSEDDATA, self.ppd,
                                         ctypes.byref(size)) == 0xFFFFFFFF:
            raise RuntimeError("could not read preparsed data")

        caps = HIDP_CAPS()
        if not _ok(hid.HidP_GetCaps(self.ppd, ctypes.byref(caps))):
            raise RuntimeError("HidP_GetCaps failed")

        n = wintypes.USHORT(caps.NumberInputValueCaps)
        arr = (HIDP_VALUE_CAPS * max(n.value, 1))()
        if not _ok(hid.HidP_GetValueCaps(HID_INPUT, arr, ctypes.byref(n), self.ppd)):
            raise RuntimeError("HidP_GetValueCaps failed")

        def covers(c, usage):
            if c.IsRange:
                return c.Usage <= usage <= c.UsageMax
            return c.Usage == usage

        self.links = []
        self.x_max = self.y_max = 1
        for c in arr[: n.value]:
            if c.UsagePage == PAGE_GENERIC and covers(c, USAGE_X):
                if c.LinkCollection not in self.links:
                    self.links.append(c.LinkCollection)
                self.x_max = max(self.x_max, c.LogicalMax)
            elif c.UsagePage == PAGE_GENERIC and covers(c, USAGE_Y):
                self.y_max = max(self.y_max, c.LogicalMax)
        if not self.links:
            raise RuntimeError("no finger collections found")

    def parse(self, report):
        n = len(report)
        val = wintypes.ULONG()
        count = None
        if _ok(hid.HidP_GetUsageValue(HID_INPUT, PAGE_DIGITIZER, 0, USAGE_CONTACT_COUNT,
                                      ctypes.byref(val), self.ppd, report, n)):
            count = val.value

        contacts = []
        for lc in self.links:
            x, y, cid = wintypes.ULONG(), wintypes.ULONG(), wintypes.ULONG()
            if not _ok(hid.HidP_GetUsageValue(HID_INPUT, PAGE_GENERIC, lc, USAGE_X,
                                              ctypes.byref(x), self.ppd, report, n)):
                continue
            if not _ok(hid.HidP_GetUsageValue(HID_INPUT, PAGE_GENERIC, lc, USAGE_Y,
                                              ctypes.byref(y), self.ppd, report, n)):
                continue
            if not _ok(hid.HidP_GetUsageValue(HID_INPUT, PAGE_DIGITIZER, lc, USAGE_CONTACT_ID,
                                              ctypes.byref(cid), self.ppd, report, n)):
                cid.value = lc
            buf = (wintypes.USHORT * 16)()
            ln = wintypes.ULONG(16)
            tip = False
            if _ok(hid.HidP_GetUsages(HID_INPUT, PAGE_DIGITIZER, lc, buf, ctypes.byref(ln),
                                      self.ppd, report, n)):
                tip = USAGE_TIP in buf[: ln.value]
            contacts.append((cid.value, x.value, y.value, tip))
        return count, contacts


class WindowMover:
    def __init__(self, fingers, sensitivity, snap_top, debug):
        self.fingers = fingers
        self.sens = sensitivity
        self.snap_top = snap_top
        self.debug = debug
        self.contacts = {}
        self.last_report = time.monotonic()
        self.active = False
        self.hwnd = None
        self.pending_restore = False
        self.moved = False
        self.screen_w = user32.GetSystemMetrics(0)
        self.screen_h = user32.GetSystemMetrics(1)
        self._last_n = 0

    def log(self, *a):
        if self.debug:
            say(*a)

    def feed(self, pad, count, slots):
        self.last_report = time.monotonic()
        downs = {}
        ups = set()
        for cid, x, y, tip in slots:
            if tip:
                downs[cid] = (x / pad.x_max, y / pad.y_max)
            elif x or y:
                ups.add(cid)
        for cid in ups:
            if cid not in downs:
                self.contacts.pop(cid, None)
        self.contacts.update(downs)
        self.update()

    def watchdog(self):
        if self.contacts and time.monotonic() - self.last_report > 0.25:
            self.contacts.clear()
            self.update()

    def update(self):
        n = len(self.contacts)
        if n != self._last_n:
            self.log(f"fingers: {n}")
            self._last_n = n
        if n == self.fingers:
            xs = [p[0] for p in self.contacts.values()]
            ys = [p[1] for p in self.contacts.values()]
            cx, cy = sum(xs) / n, sum(ys) / n
            if not self.active:
                self.start(cx, cy)
            elif self.hwnd:
                self.move(cx, cy)
        elif self.active:
            self.stop()

    def start(self, cx, cy):
        self.active = True
        self.hwnd = None
        self.moved = False
        self.pending_restore = False
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        hwnd = self.pick_window(pt)
        if not hwnd:
            self.log("no movable window under cursor")
            return
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        self.hwnd = hwnd
        self.cx0, self.cy0 = cx, cy
        self.x0, self.y0 = r.left, r.top
        self.off_x, self.off_y = pt.x - r.left, pt.y - r.top
        self.grab_rect = (r.left, r.top, r.right, r.bottom)
        self.pending_restore = bool(user32.IsZoomed(hwnd))
        self.log(f"grabbed window {hwnd:#x}" + (" (maximized)" if self.pending_restore else ""))

    def tear_off(self, cx, cy):
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        l, t, rt, b = self.grab_rect
        fx = _clamp((pt.x - l) / max(rt - l, 1), 0.0, 1.0)
        fy = _clamp((pt.y - t) / max(b - t, 1), 0.0, 1.0)
        user32.ShowWindow(self.hwnd, SW_RESTORE)
        r = wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(r))
        left = pt.x - round(fx * (r.right - r.left))
        top = pt.y - round(fy * (r.bottom - r.top))
        user32.SetWindowPos(self.hwnd, None, left, top, 0, 0, MOVE_FLAGS)
        self.x0, self.y0 = left, top
        self.off_x, self.off_y = pt.x - left, pt.y - top
        self.cx0, self.cy0 = cx, cy
        self.pending_restore = False
        self.moved = True
        self.log("restored from maximized")

    def move(self, cx, cy):
        dx = int((cx - self.cx0) * self.screen_w * self.sens)
        dy = int((cy - self.cy0) * self.screen_h * self.sens)
        dist = math.hypot(dx, dy)
        if self.pending_restore:
            if dist >= DEADZONE_PX:
                self.tear_off(cx, cy)
            return
        if dist >= DEADZONE_PX:
            self.moved = True
        left, top = self.x0 + dx, self.y0 + dy
        user32.SetWindowPos(self.hwnd, None, left, top, 0, 0, MOVE_FLAGS)
        vx = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        vy = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        vw = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        vh = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        user32.SetCursorPos(_clamp(left + self.off_x, vx, vx + vw - 1),
                            _clamp(top + self.off_y, vy, vy + vh - 1))

    def stop(self):
        hwnd, moved = self.hwnd, self.moved
        self.active = False
        self.hwnd = None
        self.pending_restore = False
        if not hwnd:
            return
        self.log("released")
        if self.snap_top and moved and self.at_top_edge() \
                and user32.GetWindowLongW(hwnd, GWL_STYLE) & WS_MAXIMIZEBOX:
            user32.ShowWindow(hwnd, SW_MAXIMIZE)
            self.log("maximized (released at top edge)")

    def at_top_edge(self):
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        mon = user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if not mon or not user32.GetMonitorInfoW(mon, ctypes.byref(mi)):
            return False
        return pt.y <= mi.rcMonitor.top + SNAP_EDGE_PX

    def pick_window(self, pt):
        h = user32.WindowFromPoint(pt)
        if not h:
            return None
        root = user32.GetAncestor(h, GA_ROOT) or h
        name = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(root, name, 256)
        if name.value in SHELL_CLASSES:
            return None
        if not user32.IsWindowVisible(root) or user32.IsIconic(root):
            return None
        return root


def main():
    ap = argparse.ArgumentParser(description="Move windows with a multi-finger touchpad drag.")
    ap.add_argument("--fingers", type=int, default=4, help="number of fingers (default 4)")
    ap.add_argument("--sensitivity", type=float, default=1.5,
                    help="1.0 = sliding across the whole pad moves the window across the screen "
                         "(default 1.5)")
    ap.add_argument("--no-snap", action="store_true",
                    help="don't maximize a window when it is released at the top edge of a monitor")
    ap.add_argument("--debug", action="store_true", help="print diagnostics")
    args = ap.parse_args()

    mover = WindowMover(args.fingers, args.sensitivity, not args.no_snap, args.debug)
    pads = {}
    state = {"tray": None, "taskbar_created": user32.RegisterWindowMessageW("TaskbarCreated")}

    def get_pad(hdev):
        key = hdev or 0
        if key not in pads:
            try:
                pads[key] = Touchpad(hdev)
                mover.log(f"touchpad ready: {len(pads[key].links)} finger slots, "
                          f"x_max={pads[key].x_max}, y_max={pads[key].y_max}")
            except Exception as e:
                mover.log("ignoring device:", e)
                pads[key] = None
        return pads[key]

    def on_input(lparam):
        size = wintypes.UINT(0)
        user32.GetRawInputData(lparam, RID_INPUT, None, ctypes.byref(size), HEADER_SIZE)
        if size.value == 0:
            return
        buf = ctypes.create_string_buffer(size.value)
        if user32.GetRawInputData(lparam, RID_INPUT, buf, ctypes.byref(size),
                                  HEADER_SIZE) != size.value:
            return
        raw = buf.raw
        hdr = RAWINPUTHEADER.from_buffer_copy(raw[:HEADER_SIZE])
        if hdr.dwType != RIM_TYPEHID:
            return
        size_hid, count = struct.unpack_from("<II", raw, HEADER_SIZE)
        data = raw[HEADER_SIZE + 8:]
        pad = get_pad(hdr.hDevice)
        if pad is None or size_hid == 0:
            return
        for i in range(count):
            report = data[i * size_hid:(i + 1) * size_hid]
            c, slots = pad.parse(report)
            if slots:
                mover.feed(pad, c, slots)

    def on_tray(hwnd, lparam):
        event = lparam & 0xFFFF
        if event in (WM_RBUTTONUP, WM_LBUTTONUP):
            cmd = state["tray"].show_menu()
            if cmd == ID_QUIT:
                user32.DestroyWindow(hwnd)
            elif cmd == ID_ELEVATE and not is_admin():
                if relaunch_elevated():
                    user32.DestroyWindow(hwnd)

    def wnd_proc(hwnd, msg, wparam, lparam):
        try:
            if msg == WM_INPUT:
                on_input(lparam)
            elif msg == WM_TIMER:
                mover.watchdog()
            elif msg == WM_TRAYICON:
                on_tray(hwnd, lparam)
            elif msg == state["taskbar_created"] and state["tray"]:
                state["tray"].add()
            elif msg == WM_DESTROY:
                if state["tray"]:
                    state["tray"].remove()
                user32.PostQuitMessage(0)
                return 0
        except Exception as e:
            mover.log("error:", repr(e))
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    proc = WNDPROC(wnd_proc)
    hinst = kernel32.GetModuleHandleW(None)
    cls = "FourFingerDragMsgWindow"
    wc = WNDCLASSW()
    wc.lpfnWndProc = proc
    wc.hInstance = hinst
    wc.lpszClassName = cls
    if not user32.RegisterClassW(ctypes.byref(wc)):
        sys.exit("RegisterClass failed")
    hwnd = user32.CreateWindowExW(WS_EX_TOOLWINDOW, cls, cls, 0, 0, 0, 0, 0,
                                  None, None, hinst, None)
    if not hwnd:
        sys.exit("CreateWindow failed")

    rid = RAWINPUTDEVICE(PAGE_DIGITIZER, USAGE_TOUCHPAD, RIDEV_INPUTSINK, hwnd)
    if not user32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(rid)):
        sys.exit("Could not register for touchpad input")
    user32.SetTimer(hwnd, 1, 100, None)

    tip = f"{args.fingers}-finger window drag" + (" (admin)" if is_admin() else "")
    state["tray"] = TrayIcon(hwnd, tip)
    state["tray"].add()

    say(f"Running: drag with {args.fingers} fingers to move a window. "
        f"Use the tray icon or Ctrl+C to quit.")
    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        state["tray"].remove()


if __name__ == "__main__":
    main()
