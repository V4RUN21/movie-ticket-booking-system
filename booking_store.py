import json
import os
import tempfile
import threading

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bookings.json")
_PATH = os.environ.get("BOOKINGS_PATH", _DEFAULT_PATH)
_LOCK = threading.RLock()


def load():
    with _LOCK:
        if not os.path.exists(_PATH):
            return {}
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)


def save(data):
    with _LOCK:
        folder = os.path.dirname(_PATH)
        fd, tmp_path = tempfile.mkstemp(
            prefix="bookings-", suffix=".json", dir=folder, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            os.replace(tmp_path, _PATH)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def booked_seats(key):
    return set(load().get(key, []))


def is_booked(key, seat):
    return seat in booked_seats(key)


def book(key, seats):
    with _LOCK:
        data = load()
        existing = set(data.get(key, []))
        existing.update(seats)
        data[key] = sorted(existing)
        save(data)


def book_if_available(key, seats):
    with _LOCK:
        requested = set(seats)
        data = load()
        existing = set(data.get(key, []))
        conflicts = requested & existing
        if conflicts:
            return sorted(conflicts)
        data[key] = sorted(existing | requested)
        save(data)
        return []
