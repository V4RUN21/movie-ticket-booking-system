from datetime import date
import random
import string

from booking_data import (
    STATES, MOVIES, THEATRES, SHOWTIMES,
    SEAT_ROWS, SEAT_COLS, SEAT_PRICES, TIER_NAMES,
    booking_key, seat_price,
)
import booking_store


class BookingError(Exception):
    status = 400

    def __init__(self, message, *, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConflictError(BookingError):
    status = 409


def _all_seats():
    return [f"{row}{col}" for row in SEAT_ROWS for col in SEAT_COLS]


def _seat_sort_key(seat):
    return (SEAT_ROWS.index(seat[0]), int(seat[1:]))


def _validate_show(city, theatre, movie, show_date, showtime):
    if city not in THEATRES:
        raise BookingError("Unknown city.", details={"city": city})
    if theatre not in THEATRES[city]:
        raise BookingError(
            "Unknown theatre for city.",
            details={"city": city, "theatre": theatre},
        )
    if movie not in MOVIES:
        raise BookingError("Unknown movie.", details={"movie": movie})
    if showtime not in SHOWTIMES:
        raise BookingError("Unknown showtime.", details={"showtime": showtime})
    try:
        date.fromisoformat(show_date)
    except (TypeError, ValueError):
        raise BookingError("Date must use YYYY-MM-DD format.")


def _validate_seats(seats):
    if not isinstance(seats, list) or not seats:
        raise BookingError("At least one seat is required.")

    valid = set(_all_seats())
    normalized = []
    for seat in seats:
        if not isinstance(seat, str):
            raise BookingError("Seat names must be strings.")
        seat = seat.strip().upper()
        if seat not in valid:
            raise BookingError("Unknown seat.", details={"seat": seat})
        if seat not in normalized:
            normalized.append(seat)

    return sorted(normalized, key=_seat_sort_key)


def get_catalog():
    return {
        "states": STATES,
        "movies": MOVIES,
        "theatres": THEATRES,
        "showtimes": SHOWTIMES,
        "seat_rows": SEAT_ROWS,
        "seat_cols": SEAT_COLS,
        "seat_prices": SEAT_PRICES,
        "tier_names": {str(price): name for price, name in TIER_NAMES.items()},
    }


def get_availability(city, theatre, movie, date, showtime):
    _validate_show(city, theatre, movie, date, showtime)
    key = booking_key(city, theatre, movie, date, showtime)
    booked = sorted(booking_store.booked_seats(key), key=_seat_sort_key)
    booked_set = set(booked)
    seats = _all_seats()
    available = [seat for seat in seats if seat not in booked_set]
    return {
        "key": key,
        "booked": booked,
        "available": available,
        "total_seats": len(seats),
        "available_count": len(available),
        "booked_count": len(booked),
    }


def create_booking(city, theatre, movie, date, showtime, seats, customer_name=""):
    _validate_show(city, theatre, movie, date, showtime)
    seats = _validate_seats(seats)
    key = booking_key(city, theatre, movie, date, showtime)
    conflicts = booking_store.book_if_available(key, seats)
    if conflicts:
        raise ConflictError(
            "One or more selected seats are already booked.",
            details={"seats": conflicts},
        )

    total = sum(seat_price(seat) for seat in seats)
    ticket_id = "TKT-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=8))
    return {
        "ticket_id": ticket_id,
        "key": key,
        "customer_name": customer_name.strip() if isinstance(customer_name, str) else "",
        "city": city,
        "theatre": theatre,
        "movie": movie,
        "date": date,
        "showtime": showtime,
        "seats": seats,
        "total": total,
    }
