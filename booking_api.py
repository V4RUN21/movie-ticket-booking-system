#! python3.13
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from urllib.parse import parse_qs, urlparse

from booking_service import (
    BookingError,
    ConflictError,
    create_booking,
    get_availability,
    get_catalog,
)


HOST = "127.0.0.1"
PORT = 8765


class BookingApiHandler(BaseHTTPRequestHandler):
    server_version = "BookingAPI/1.0"

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._send_json(200, {"status": "ok"})
            elif parsed.path == "/catalog":
                self._send_json(200, get_catalog())
            elif parsed.path == "/availability":
                query = parse_qs(parsed.query)
                self._send_json(200, get_availability(
                    _one(query, "city"),
                    _one(query, "theatre"),
                    _one(query, "movie"),
                    _one(query, "date"),
                    _one(query, "showtime"),
                ))
            else:
                self._send_json(404, {"error": "Not found."})
        except BookingError as exc:
            self._send_json(exc.status, _error_body(exc))
        except Exception as exc:
            self._send_json(500, {"error": "Unexpected server error.", "details": str(exc)})

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            if parsed.path != "/bookings":
                self._send_json(404, {"error": "Not found."})
                return

            body = self._read_json()
            result = create_booking(
                body.get("city"),
                body.get("theatre"),
                body.get("movie"),
                body.get("date"),
                body.get("showtime"),
                body.get("seats"),
                body.get("customer_name", ""),
            )
            self._send_json(201, result)
        except BookingError as exc:
            self._send_json(exc.status, _error_body(exc))
        except Exception as exc:
            self._send_json(500, {"error": "Unexpected server error.", "details": str(exc)})

    def do_OPTIONS(self):
        self._send_json(204, {})

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (
            self.client_address[0],
            self.log_date_time_string(),
            fmt % args,
        ))

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            raise BookingError("Request body is required.")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            raise BookingError("Request body must be valid JSON.")

    def _send_json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if status != 204:
            self.wfile.write(data)


def _one(query, name):
    values = query.get(name)
    if not values or values[0] == "":
        raise BookingError(f"Missing query parameter: {name}")
    return values[0]


def _error_body(exc):
    body = {"error": exc.message}
    if exc.details:
        body["details"] = exc.details
    return body


def run(host=HOST, port=PORT):
    server = ThreadingHTTPServer((host, port), BookingApiHandler)
    print(f"Booking API running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT
    run(host, port)
