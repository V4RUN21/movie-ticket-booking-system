import json
import os
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_HOST = "127.0.0.1"
API_PORT = 8765
API_BASE = f"http://{API_HOST}:{API_PORT}"
_PROCESS = None


class ApiError(Exception):
    def __init__(self, message, *, status=None, details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details or {}


def ensure_backend_running(timeout=5.0):
    if _health_ok():
        return True

    _start_backend()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _health_ok():
            return True
        time.sleep(0.15)
    raise ApiError("Booking backend did not start in time.")


def fetch_availability(city, theatre, movie, date, showtime):
    query = urlencode({
        "city": city,
        "theatre": theatre,
        "movie": movie,
        "date": date,
        "showtime": showtime,
    })
    return _request("GET", f"/availability?{query}")


def create_booking(city, theatre, movie, date, showtime, seats, customer_name=""):
    return _request("POST", "/bookings", {
        "city": city,
        "theatre": theatre,
        "movie": movie,
        "date": date,
        "showtime": showtime,
        "seats": list(seats),
        "customer_name": customer_name,
    })


def _health_ok():
    try:
        data = _request("GET", "/health", timeout=0.75)
        return data.get("status") == "ok"
    except ApiError:
        return False


def _start_backend():
    global _PROCESS
    if _PROCESS and _PROCESS.poll() is None:
        return

    root = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(root, "booking_api.py")
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    _PROCESS = subprocess.Popen(
        [sys.executable, script],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )


def _request(method, path, payload=None, timeout=5.0):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(
        API_BASE + path,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        body = _read_error(exc)
        raise ApiError(
            body.get("error", f"HTTP {exc.code}"),
            status=exc.code,
            details=body.get("details", {}),
        )
    except URLError as exc:
        raise ApiError(f"Cannot reach booking backend: {exc.reason}")
    except TimeoutError:
        raise ApiError("Booking backend request timed out.")


def _read_error(exc):
    try:
        raw = exc.read().decode("utf-8")
        return json.loads(raw) if raw else {}
    except Exception:
        return {}
