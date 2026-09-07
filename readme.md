# Movie Ticket Booking System

A Python-based movie ticket booking application with a Tkinter desktop interface, custom HTTP API, business logic layer, and JSON-based persistence.

## Features

- State and city selection
- Movie and theatre selection
- Show time selection
- Interactive seat selection
- Economy, Standard and Premium seat categories
- Dynamic ticket pricing
- Seat availability checking
- Booking conflict detection
- Simulated payment validation
- Ticket generation
- Local HTTP backend
- JSON-based data persistence

## Architecture

Tkinter UI
↓
HTTP Client
↓
HTTP API
↓
Booking Service
↓
Booking Store
↓
JSON Storage

## Technologies

- Python
- Tkinter
- HTTP
- JSON
- Threading
- REST-style API architecture

## How to Run

Run:

`run_booking.bat`

or:

`run_booking.ps1`

The application starts the local backend automatically.

## Project Status

This is a portfolio/learning project. The payment process is simulated and the current persistence layer uses JSON rather than a production database.

## Future Improvements

- SQLite/PostgreSQL database
- Automated tests
- Booking history
- Booking cancellation
- Authentication
- FastAPI backend
- Real payment gateway integration
- Web-based frontend