#! python3.13
from tk_runtime import configure_tcl_tk

configure_tcl_tk()

import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from booking_data import (
    STATES, MOVIES, THEATRES, SHOWTIMES,
    SEAT_ROWS, SEAT_COLS, SEAT_PRICES, TIER_NAMES,
    seat_price,
)
import random
import booking_client

BG       = "#FFFFFF"
SURFACE  = "#F0F0F0"
CARD     = "#F7F7F7"
NUM_BG   = "#EAEAEA"
ORANGE   = "#7FB77E"   # pale green (primary accent)
ORANGE_A = "#5FA05E"   # slightly deeper green for hover/active
GOLD     = "#3D6B3C"   # deep green for emphasized text on light bg
FG       = "#1A1A1A"
FG_MUT   = "#6B6B6B"
FG_ON_OR = "#FFFFFF"   # text drawn on pale green
GREY_BDR = "#C8C8C8"
BOOKED   = "#B8B8B8"
ERR      = "#D32F2F"

F_TITLE = ("Arial Black", 11)
F_HEAD  = ("Arial Black", 14)
F_LBL   = ("Arial Black", 9)
F_BTN   = ("Arial Black", 9)
F_SEAT  = ("Arial Black", 8)
F_SEC   = ("Arial Black", 7)


def styled_btn(parent, text, cmd, *, fg=FG, bg=SURFACE, bdr=ORANGE,
               width=14, height=2, font=F_BTN):
    return tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg,
        activebackground=ORANGE_A, activeforeground=FG_ON_OR,
        relief=tk.FLAT, bd=0, cursor="hand2",
        font=font, width=width, height=height,
        highlightthickness=2,
        highlightbackground=bdr,
        highlightcolor=ORANGE,
    )


class BookingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TICKET BOOKING")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("560x720")
        self.total_pages = 7
        self.ticket_id = ""
        self._backend_error = ""

        self.state_v   = tk.StringVar()
        self.city_v    = tk.StringVar()
        self.date_v    = tk.StringVar()
        self.movie_v   = tk.StringVar()
        self.theatre_v = tk.StringVar()
        self.show_v    = tk.StringVar()
        self.selected_seats = set()
        self.last_booked = []
        self.last_booking = {}

        try:
            booking_client.ensure_backend_running()
        except booking_client.ApiError as exc:
            self._backend_error = exc.message

        self._build_titlebar()
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.pages = {}
        for i, builder in enumerate([
            self._page_location, self._page_date, self._page_movie,
            self._page_theatre, self._page_seats,
            self._page_payment, self._page_ticket,
        ], start=1):
            f = tk.Frame(self.body, bg=BG)
            builder(f)
            self.pages[i] = f

        self.current = 1
        self._show(1)
        self._build_splash()

    # ─── Splash / Welcome ─────────────────────────────────────────────
    def _build_splash(self):
        W, H = 560, 720
        self.splash = tk.Frame(self, bg=BG)
        self.splash.place(x=0, y=0, relwidth=1, relheight=1)
        c = tk.Canvas(self.splash, bg=BG, width=W, height=H,
                      highlightthickness=0)
        c.pack(fill=tk.BOTH, expand=True)
        self.splash_canvas = c

        # Title + tagline
        c.create_text(W // 2, 110, text="POPCORN  &  CHILL",
                      fill=ORANGE, font=("Arial Black", 28, "bold"))
        c.create_text(W // 2, 150,
                      text="◆  YOUR MOVIE.  YOUR SEAT.  YOUR TIME.  ◆",
                      fill=FG_MUT, font=("Arial Black", 9))

        # ── Film reel (left)
        rcx, rcy, R = 130, 350, 65
        c.create_oval(rcx - R, rcy - R, rcx + R, rcy + R,
                      fill=NUM_BG, outline=ORANGE, width=3)
        c.create_oval(rcx - 15, rcy - 15, rcx + 15, rcy + 15,
                      fill=BG, outline=ORANGE, width=2)
        self._reel_holes = []
        for i in range(6):
            self._reel_holes.append(
                c.create_oval(0, 0, 0, 0, fill=BG, outline=ORANGE, width=2))
        self._reel_angle = 0
        self._reel_center = (rcx, rcy, R - 18)

        # ── Popcorn bucket (center)
        bx, by, bw, bh = 240, 300, 90, 130
        for i in range(5):
            x0 = bx + i * (bw / 5)
            x1 = x0 + bw / 10
            c.create_rectangle(x0, by + 30, x1, by + bh,
                               fill="#D32F2F", outline="")
        c.create_rectangle(bx, by + 30, bx + bw, by + bh,
                           outline=FG, width=2)
        c.create_rectangle(bx - 6, by + 22, bx + bw + 6, by + 38,
                           fill=ORANGE, outline=FG, width=2)
        for (px, py, pr) in [(bx + 15, by + 10, 14),
                             (bx + 38, by - 2, 17),
                             (bx + 62, by + 8, 14),
                             (bx + 80, by - 4, 12)]:
            c.create_oval(px - pr, py - pr, px + pr, py + pr,
                          fill="#FFF8DC", outline=GOLD, width=2)

        # ── Ticket (right)
        tx, ty, tw, th = 400, 320, 120, 80
        c.create_rectangle(tx, ty, tx + tw, ty + th,
                           fill=ORANGE, outline=FG, width=2)
        c.create_oval(tx + tw / 2 - 9, ty - 9,
                      tx + tw / 2 + 9, ty + 9, fill=BG, outline="")
        c.create_oval(tx + tw / 2 - 9, ty + th - 9,
                      tx + tw / 2 + 9, ty + th + 9, fill=BG, outline="")
        c.create_text(tx + tw / 2, ty + th / 2 - 8,
                      text="ADMIT", fill=FG_ON_OR,
                      font=("Arial Black", 11, "bold"))
        c.create_text(tx + tw / 2, ty + th / 2 + 10,
                      text="ONE", fill=FG_ON_OR,
                      font=("Arial Black", 11, "bold"))

        # ── Loading dots
        c.create_text(W // 2, 560, text="LOADING THE SHOW",
                      fill=FG_MUT, font=("Arial Black", 10))
        self._splash_dots = []
        for i in range(3):
            cx = W // 2 - 30 + i * 30
            self._splash_dots.append(
                c.create_oval(cx - 6, 594, cx + 6, 606,
                              fill=GREY_BDR, outline=""))

        # ── Floating popcorn kernels (animated)
        self._kernels = []
        for _ in range(14):
            x = random.randint(40, W - 40)
            y = random.randint(440, H - 30)
            k = c.create_oval(x - 4, y - 4, x + 4, y + 4,
                              fill="#FFF8DC", outline=GOLD)
            self._kernels.append({
                "id": k, "x": x, "y": y,
                "vy": -random.uniform(1.2, 2.8),
                "vx": random.uniform(-0.6, 0.6),
            })

        self._splash_tick = 0
        self._splash_running = True
        self._animate_splash()
        self.after(3000, self._end_splash)

    def _animate_splash(self):
        if not self._splash_running:
            return
        import math
        c = self.splash_canvas
        self._splash_tick += 1

        # Pulse loading dots
        active = (self._splash_tick // 6) % 3
        for i, d in enumerate(self._splash_dots):
            c.itemconfig(d, fill=ORANGE if i == active else GREY_BDR)

        # Spin film reel sprocket holes
        self._reel_angle = (self._reel_angle + 4) % 360
        rcx, rcy, rr = self._reel_center
        for i, h in enumerate(self._reel_holes):
            ang = math.radians(self._reel_angle + i * 60)
            x = rcx + rr * math.cos(ang)
            y = rcy + rr * math.sin(ang)
            c.coords(h, x - 6, y - 6, x + 6, y + 6)

        # Float popcorn kernels upward
        W, H = 560, 720
        for k in self._kernels:
            k["x"] += k["vx"]
            k["y"] += k["vy"]
            if k["y"] < 80 or k["x"] < 15 or k["x"] > W - 15:
                k["x"] = random.randint(40, W - 40)
                k["y"] = H - 20
                k["vy"] = -random.uniform(1.2, 2.8)
                k["vx"] = random.uniform(-0.6, 0.6)
            c.coords(k["id"],
                     k["x"] - 4, k["y"] - 4,
                     k["x"] + 4, k["y"] + 4)

        self.after(40, self._animate_splash)

    def _end_splash(self):
        self._splash_running = False
        if hasattr(self, "splash") and self.splash.winfo_exists():
            self.splash.destroy()

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=SURFACE, padx=12, pady=8)
        bar.pack(fill=tk.X)
        tk.Label(bar, text="◆  TICKET BOOKING", bg=SURFACE, fg=ORANGE,
                 font=F_TITLE, anchor="w").pack(side=tk.LEFT)
        self.step_lbl = tk.Label(bar, text="STEP 1 / 7", bg=SURFACE,
                                 fg=FG_MUT, font=F_SEC)
        self.step_lbl.pack(side=tk.RIGHT)

    def _show(self, n):
        for f in self.pages.values():
            f.pack_forget()
        self.pages[n].pack(fill=tk.BOTH, expand=True)
        self.current = n
        self.step_lbl.config(text=f"STEP {n} / {self.total_pages}")
        if n == 3:
            self._render_movies()
        elif n == 4:
            self._render_theatres()
        elif n == 5:
            self._render_seats()
        elif n == 6:
            self._render_payment()
        elif n == 7:
            self._render_ticket()

    # ─── Helpers ──────────────────────────────────────────────────────
    def _heading(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=ORANGE,
                 font=F_HEAD, anchor="w").pack(fill=tk.X, pady=(4, 12))

    def _label(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=FG_MUT,
                 font=F_LBL, anchor="w").pack(fill=tk.X, pady=(8, 2))

    def _nav(self, parent, on_next, next_text="NEXT →", show_back=True):
        nav = tk.Frame(parent, bg=BG)
        nav.pack(side=tk.BOTTOM, fill=tk.X, pady=12)
        if show_back:
            styled_btn(nav, "← BACK", lambda: self._show(self.current - 1),
                       bg=CARD, bdr=GREY_BDR, fg=FG_MUT
                       ).pack(side=tk.LEFT)
        styled_btn(nav, next_text, on_next,
                   bg=ORANGE, fg=FG_ON_OR, bdr=ORANGE
                   ).pack(side=tk.RIGHT)

    def _combo(self, parent, var, values):
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", font=F_LBL)
        cb.pack(fill=tk.X, ipady=4)
        return cb

    # ─── Page 1: Location ─────────────────────────────────────────────
    def _page_location(self, p):
        self._heading(p, "WHERE ARE YOU?")
        self._label(p, "STATE")
        cb_state = self._combo(p, self.state_v, list(STATES.keys()))
        self._label(p, "CITY")
        cb_city = self._combo(p, self.city_v, [])

        def on_state(_=None):
            cities = STATES.get(self.state_v.get(), [])
            cb_city["values"] = cities
            self.city_v.set("")
        cb_state.bind("<<ComboboxSelected>>", on_state)

        def go():
            if not self.state_v.get() or not self.city_v.get():
                self._flash(p, "Pick state and city first.")
                return
            self._show(2)
        self._nav(p, go, show_back=False)

    # ─── Page 2: Date ─────────────────────────────────────────────────
    def _page_date(self, p):
        self._heading(p, "PICK A DATE")
        self._label(p, "DATE (NEXT 7 DAYS)")
        today = date.today()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(7)]
        cb = self._combo(p, self.date_v, dates)

        self._label(p, "DAY")
        day_lbl = tk.Label(p, text="—", bg=CARD, fg=GOLD, font=F_HEAD,
                           anchor="w", padx=10, pady=8,
                           highlightthickness=2, highlightbackground=ORANGE)
        day_lbl.pack(fill=tk.X)

        def on_pick(_=None):
            d = self.date_v.get()
            if d:
                day_lbl.config(text=date.fromisoformat(d).strftime("%A").upper())
        cb.bind("<<ComboboxSelected>>", on_pick)

        def go():
            if not self.date_v.get():
                self._flash(p, "Pick a date first.")
                return
            self._show(3)
        self._nav(p, go)

    # ─── Page 3: Movie ────────────────────────────────────────────────
    def _page_movie(self, p):
        self._heading(p, "MOVIES PLAYING")
        self.movie_info = tk.Label(p, text="", bg=BG, fg=FG_MUT,
                                   font=F_LBL, anchor="w")
        self.movie_info.pack(fill=tk.X)
        self.movie_list_frame = tk.Frame(p, bg=BG)
        self.movie_list_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        nav = tk.Frame(p, bg=BG)
        nav.pack(side=tk.BOTTOM, fill=tk.X, pady=12)
        styled_btn(nav, "← BACK", lambda: self._show(self.current - 1),
                   bg=CARD, bdr=GREY_BDR, fg=FG_MUT).pack(side=tk.LEFT)
        tk.Label(nav, text="Tap a movie to continue →",
                 bg=BG, fg=FG_MUT, font=F_SEC).pack(side=tk.RIGHT, padx=8)

    def _render_movies(self):
        for w in self.movie_list_frame.winfo_children():
            w.destroy()
        self.movie_info.config(
            text=f"{self.city_v.get()}  •  {self.date_v.get()}")
        for m in MOVIES:
            b = styled_btn(
                self.movie_list_frame, m,
                lambda mv=m: self._pick_movie(mv),
                bg=CARD, fg=ORANGE, bdr=GREY_BDR, width=40, height=1)
            if self.movie_v.get() == m:
                b.config(bg=ORANGE, fg=FG_ON_OR, bdr=ORANGE,
                         highlightbackground=ORANGE)
            b.pack(fill=tk.X, pady=2)

    def _pick_movie(self, m):
        self.movie_v.set(m)
        self.theatre_v.set("")
        self.show_v.set("")
        self._show(4)

    # ─── Page 4: Theatre + Showtime ───────────────────────────────────
    def _page_theatre(self, p):
        self._heading(p, "THEATRE & SHOWTIME")
        self.theatre_info = tk.Label(p, text="", bg=BG, fg=FG_MUT,
                                     font=F_LBL, anchor="w")
        self.theatre_info.pack(fill=tk.X)
        self.theatre_list_frame = tk.Frame(p, bg=BG)
        self.theatre_list_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        def go():
            if not self.theatre_v.get() or not self.show_v.get():
                self._flash(p, "Pick a theatre and showtime.")
                return
            self.selected_seats = set()
            self._show(5)
        self._nav(p, go)

    def _render_theatres(self):
        for w in self.theatre_list_frame.winfo_children():
            w.destroy()
        self.theatre_info.config(
            text=f"{self.movie_v.get()}  •  {self.date_v.get()}")
        for t in THEATRES.get(self.city_v.get(), []):
            row = tk.Frame(self.theatre_list_frame, bg=BG)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=t, bg=CARD, fg=FG, font=F_LBL,
                     anchor="w", padx=10, pady=6, width=22,
                     highlightthickness=2,
                     highlightbackground=GREY_BDR).pack(side=tk.LEFT, fill=tk.Y)
            for st in SHOWTIMES:
                selected = (self.theatre_v.get() == t and self.show_v.get() == st)
                b = styled_btn(
                    row, st,
                    lambda tt=t, ss=st: self._pick_show(tt, ss),
                    bg=ORANGE if selected else CARD,
                    fg=FG_ON_OR if selected else ORANGE,
                    bdr=ORANGE if selected else GREY_BDR,
                    width=7, height=1)
                b.pack(side=tk.LEFT, padx=3)

    def _pick_show(self, t, st):
        self.theatre_v.set(t)
        self.show_v.set(st)
        self._render_theatres()

    # ─── Page 5: Seats ────────────────────────────────────────────────
    def _page_seats(self, p):
        self._heading(p, "SELECT YOUR SEATS")
        self.seat_info = tk.Label(p, text="", bg=BG, fg=FG_MUT,
                                  font=F_LBL, anchor="w")
        self.seat_info.pack(fill=tk.X)

        screen = tk.Frame(p, bg=ORANGE, height=4)
        screen.pack(fill=tk.X, pady=(14, 4))
        tk.Label(p, text="───  SCREEN  ───",
                 bg=BG, fg=FG_MUT, font=F_SEC).pack()

        self.seat_grid = tk.Frame(p, bg=BG)
        self.seat_grid.pack(pady=12)

        legend = tk.Frame(p, bg=BG)
        legend.pack()
        for txt, c in [("AVAILABLE", NUM_BG), ("SELECTED", ORANGE),
                       ("BOOKED", BOOKED)]:
            tk.Label(legend, text="  ", bg=c, width=2, height=1,
                     highlightthickness=1,
                     highlightbackground=GREY_BDR).pack(side=tk.LEFT, padx=4)
            tk.Label(legend, text=txt, bg=BG, fg=FG_MUT,
                     font=F_SEC).pack(side=tk.LEFT, padx=(0, 10))

        # Tier price legend
        tier_row = tk.Frame(p, bg=BG)
        tier_row.pack(pady=(6, 0))
        tier_pairs = sorted({(r, SEAT_PRICES[r]) for r in SEAT_ROWS},
                            key=lambda x: x[1])
        seen = set()
        for _, price in tier_pairs:
            if price in seen:
                continue
            seen.add(price)
            rows_in_tier = "".join(r for r, p in SEAT_PRICES.items() if p == price)
            tk.Label(tier_row,
                     text=f"  {TIER_NAMES[price]} ({rows_in_tier})  ₹{price}  ",
                     bg=CARD, fg=GOLD, font=F_SEC,
                     highlightthickness=1,
                     highlightbackground=GREY_BDR).pack(side=tk.LEFT, padx=4)

        self.summary_lbl = tk.Label(p, text="", bg=BG, fg=GOLD,
                                    font=F_LBL, anchor="w", justify=tk.LEFT)
        self.summary_lbl.pack(fill=tk.X, pady=(10, 0))

        self.total_lbl = tk.Label(p, text="TOTAL  ₹0", bg=BG, fg=ORANGE,
                                  font=F_HEAD, anchor="e")
        self.total_lbl.pack(fill=tk.X, pady=(4, 0))

        nav = tk.Frame(p, bg=BG)
        nav.pack(side=tk.BOTTOM, fill=tk.X, pady=12)
        styled_btn(nav, "← BACK", lambda: self._show(self.current - 1),
                   bg=CARD, bdr=GREY_BDR, fg=FG_MUT).pack(side=tk.LEFT)
        self.proceed_btn = styled_btn(
            nav, "PROCEED →", self._proceed_to_payment,
            bg=ORANGE, fg=FG_ON_OR, bdr=ORANGE)
        self.proceed_btn.pack(side=tk.RIGHT)

    def _render_seats(self):
        for w in self.seat_grid.winfo_children():
            w.destroy()
        self.selected_seats = set()
        if self._backend_error:
            self._flash(self.pages[5], self._backend_error)
        try:
            availability = booking_client.fetch_availability(
                self.city_v.get(), self.theatre_v.get(),
                self.movie_v.get(), self.date_v.get(),
                self.show_v.get())
            booked = set(availability["booked"])
        except booking_client.ApiError as exc:
            self._flash(self.pages[5], exc.message)
            booked = set()
        self.seat_info.config(
            text=f"{self.theatre_v.get()}  •  {self.show_v.get()}  •  "
                 f"{self.movie_v.get()}  •  {self.date_v.get()}")

        self.seat_buttons = {}
        for r, row in enumerate(SEAT_ROWS):
            tk.Label(self.seat_grid, text=row, bg=BG, fg=FG_MUT,
                     font=F_SEAT, width=2).grid(row=r, column=0, padx=2)
            for c in SEAT_COLS:
                seat = f"{row}{c}"
                if seat in booked:
                    btn = tk.Button(
                        self.seat_grid, text=seat,
                        bg=BOOKED, fg=FG_MUT,
                        relief=tk.FLAT, bd=0, font=F_SEAT,
                        width=3, height=1, state=tk.DISABLED,
                        disabledforeground=FG_MUT,
                        highlightthickness=1,
                        highlightbackground=GREY_BDR)
                else:
                    btn = tk.Button(
                        self.seat_grid, text=seat,
                        bg=NUM_BG, fg=FG,
                        activebackground=ORANGE_A, activeforeground=FG_ON_OR,
                        relief=tk.FLAT, bd=0, cursor="hand2",
                        font=F_SEAT, width=3, height=1,
                        highlightthickness=1,
                        highlightbackground=ORANGE,
                        command=lambda s=seat: self._toggle_seat(s))
                btn.grid(row=r, column=c, padx=2, pady=2)
                self.seat_buttons[seat] = btn
        self._update_summary()

    def _toggle_seat(self, seat):
        if seat in self.selected_seats:
            self.selected_seats.remove(seat)
            self.seat_buttons[seat].config(bg=NUM_BG, fg=FG,
                                           highlightbackground=ORANGE)
        else:
            self.selected_seats.add(seat)
            self.seat_buttons[seat].config(bg=ORANGE, fg=FG_ON_OR,
                                           highlightbackground=ORANGE)
        self._update_summary()

    def _update_summary(self):
        seats = sorted(self.selected_seats)
        if seats:
            lines = [f"SELECTED ({len(seats)}): {', '.join(seats)}"]
            tier_counts = {}
            for s in seats:
                p = seat_price(s)
                tier_counts[p] = tier_counts.get(p, 0) + 1
            for price, n in sorted(tier_counts.items()):
                lines.append(
                    f"  {TIER_NAMES[price]:9s} {n} × ₹{price}  =  ₹{n * price}")
            self.summary_lbl.config(text="\n".join(lines))
            self.total_lbl.config(text=f"TOTAL  ₹{self._total()}")
            self.proceed_btn.config(state=tk.NORMAL)
        else:
            self.summary_lbl.config(text="No seats selected.")
            self.total_lbl.config(text="TOTAL  ₹0")
            self.proceed_btn.config(state=tk.DISABLED)

    def _total(self):
        return sum(seat_price(s) for s in self.selected_seats)

    def _proceed_to_payment(self):
        if not self.selected_seats:
            return
        # Re-check availability in case another flow booked these seats
        try:
            availability = booking_client.fetch_availability(
                self.city_v.get(), self.theatre_v.get(),
                self.movie_v.get(), self.date_v.get(),
                self.show_v.get())
        except booking_client.ApiError as exc:
            self._flash(self.pages[5], exc.message)
            return
        clash = self.selected_seats & set(availability["booked"])
        if clash:
            self._flash(self.pages[5],
                        f"Just got booked: {', '.join(sorted(clash))}. Re-pick.")
            self._render_seats()
            return
        self._show(6)

    # ─── Page 6: Payment ──────────────────────────────────────────────
    def _page_payment(self, p):
        self._heading(p, "PAYMENT")
        self.pay_summary = tk.Label(p, text="", bg=CARD, fg=FG,
                                    font=F_LBL, justify=tk.LEFT, anchor="w",
                                    padx=12, pady=10,
                                    highlightthickness=2,
                                    highlightbackground=ORANGE)
        self.pay_summary.pack(fill=tk.X, pady=(0, 10))

        self.pay_name = tk.StringVar()
        self.pay_card = tk.StringVar()
        self.pay_exp  = tk.StringVar()
        self.pay_cvv  = tk.StringVar()

        self._label(p, "CARDHOLDER NAME")
        tk.Entry(p, textvariable=self.pay_name, bg=CARD, fg=FG,
                 insertbackground=ORANGE, relief=tk.FLAT,
                 highlightthickness=2, highlightbackground=GREY_BDR,
                 highlightcolor=ORANGE, font=F_LBL
                 ).pack(fill=tk.X, ipady=5)

        self._label(p, "CARD NUMBER (16 DIGITS)")
        tk.Entry(p, textvariable=self.pay_card, bg=CARD, fg=FG,
                 insertbackground=ORANGE, relief=tk.FLAT,
                 highlightthickness=2, highlightbackground=GREY_BDR,
                 highlightcolor=ORANGE, font=F_LBL
                 ).pack(fill=tk.X, ipady=5)

        small = tk.Frame(p, bg=BG)
        small.pack(fill=tk.X, pady=(8, 0))
        ec = tk.Frame(small, bg=BG); ec.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
        cc = tk.Frame(small, bg=BG); cc.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))
        self._label(ec, "EXPIRY (MM/YY)")
        tk.Entry(ec, textvariable=self.pay_exp, bg=CARD, fg=FG,
                 insertbackground=ORANGE, relief=tk.FLAT,
                 highlightthickness=2, highlightbackground=GREY_BDR,
                 highlightcolor=ORANGE, font=F_LBL
                 ).pack(fill=tk.X, ipady=5)
        self._label(cc, "CVV")
        tk.Entry(cc, textvariable=self.pay_cvv, show="•", bg=CARD, fg=FG,
                 insertbackground=ORANGE, relief=tk.FLAT,
                 highlightthickness=2, highlightbackground=GREY_BDR,
                 highlightcolor=ORANGE, font=F_LBL
                 ).pack(fill=tk.X, ipady=5)

        self.pay_status = tk.Label(p, text="", bg=BG, fg=ERR,
                                   font=F_SEC, anchor="w")
        self.pay_status.pack(fill=tk.X, pady=(8, 0))

        nav = tk.Frame(p, bg=BG)
        nav.pack(side=tk.BOTTOM, fill=tk.X, pady=12)
        styled_btn(nav, "← BACK", lambda: self._show(5),
                   bg=CARD, bdr=GREY_BDR, fg=FG_MUT).pack(side=tk.LEFT)
        self.pay_btn = styled_btn(
            nav, "PAY NOW", self._do_payment,
            bg=ORANGE, fg=FG_ON_OR, bdr=ORANGE, width=16)
        self.pay_btn.pack(side=tk.RIGHT)

    def _render_payment(self):
        seats = sorted(self.selected_seats)
        lines = [
            f"MOVIE     :  {self.movie_v.get()}",
            f"THEATRE   :  {self.theatre_v.get()}  •  {self.show_v.get()}",
            f"DATE      :  {self.date_v.get()}",
            f"SEATS     :  {', '.join(seats)}",
            f"AMOUNT    :  ₹{self._total()}",
        ]
        self.pay_summary.config(text="\n".join(lines))
        self.pay_status.config(text="")
        self.pay_btn.config(text=f"PAY ₹{self._total()}", state=tk.NORMAL)

    def _do_payment(self):
        name = self.pay_name.get().strip()
        card = "".join(ch for ch in self.pay_card.get() if ch.isdigit())
        exp  = self.pay_exp.get().strip()
        cvv  = "".join(ch for ch in self.pay_cvv.get() if ch.isdigit())
        if not name:
            self.pay_status.config(text="Enter cardholder name."); return
        if len(card) != 16:
            self.pay_status.config(text="Card number must be 16 digits."); return
        if len(exp) != 5 or exp[2] != "/":
            self.pay_status.config(text="Expiry must be MM/YY."); return
        if len(cvv) != 3:
            self.pay_status.config(text="CVV must be 3 digits."); return

        # "Process" payment, then commit booking through the backend.
        try:
            booking = booking_client.create_booking(
                self.city_v.get(), self.theatre_v.get(),
                self.movie_v.get(), self.date_v.get(),
                self.show_v.get(), sorted(self.selected_seats), name)
        except booking_client.ApiError as exc:
            taken = exc.details.get("seats") if exc.details else None
            if taken:
                msg = f"Seat(s) just got taken: {', '.join(sorted(taken))}."
            else:
                msg = exc.message
            self.pay_status.config(
                text=msg)
            return
        self.last_booking = booking
        self.last_booked = booking["seats"]
        self.ticket_id = booking["ticket_id"]
        self.cardholder_name = name
        self._show(7)

    # ─── Page 7: Ticket ───────────────────────────────────────────────
    def _page_ticket(self, p):
        self._heading(p, "✓ PAYMENT SUCCESSFUL")
        self.ticket_box = tk.Frame(p, bg=CARD, padx=16, pady=16,
                                   highlightthickness=3,
                                   highlightbackground=ORANGE)
        self.ticket_box.pack(fill=tk.X, pady=8)

        self.ticket_top = tk.Label(self.ticket_box, text="", bg=CARD,
                                   fg=ORANGE, font=F_HEAD, anchor="w",
                                   justify=tk.LEFT)
        self.ticket_top.pack(fill=tk.X)
        tk.Frame(self.ticket_box, bg=ORANGE, height=2).pack(fill=tk.X, pady=8)
        self.ticket_body = tk.Label(self.ticket_box, text="", bg=CARD,
                                    fg=FG, font=F_LBL, justify=tk.LEFT,
                                    anchor="w")
        self.ticket_body.pack(fill=tk.X)
        tk.Frame(self.ticket_box, bg=ORANGE, height=2).pack(fill=tk.X, pady=8)
        self.ticket_footer = tk.Label(self.ticket_box, text="", bg=CARD,
                                      fg=GOLD, font=F_HEAD, anchor="e")
        self.ticket_footer.pack(fill=tk.X)

        nav = tk.Frame(p, bg=BG)
        nav.pack(side=tk.BOTTOM, fill=tk.X, pady=12)
        styled_btn(nav, "BOOK ANOTHER", self._reset,
                   bg=ORANGE, fg=FG_ON_OR, bdr=ORANGE,
                   width=18).pack(side=tk.RIGHT)
        styled_btn(nav, "EXIT", self.destroy,
                   bg=CARD, bdr=ERR, fg=ERR).pack(side=tk.LEFT)

    def _render_ticket(self):
        seats = self.last_booked
        day = date.fromisoformat(self.date_v.get()).strftime("%A").upper()
        self.ticket_top.config(
            text=f"{self.movie_v.get()}\n{self.ticket_id}")
        body = [
            f"NAME      :  {getattr(self, 'cardholder_name', '')}",
            f"CITY      :  {self.city_v.get()}, {self.state_v.get()}",
            f"THEATRE   :  {self.theatre_v.get()}",
            f"DATE      :  {self.date_v.get()}  ({day})",
            f"SHOWTIME  :  {self.show_v.get()}",
            f"SEATS     :  {', '.join(seats)}",
        ]
        self.ticket_body.config(text="\n".join(body))
        self.ticket_footer.config(text=f"PAID  ₹{self._total()}")

    def _reset(self):
        self.movie_v.set("")
        self.theatre_v.set("")
        self.show_v.set("")
        self.selected_seats = set()
        self.last_booked = []
        self.ticket_id = ""
        for v in (self.pay_name, self.pay_card, self.pay_exp, self.pay_cvv):
            v.set("")
        self._show(1)

    # ─── Tiny inline error flash ──────────────────────────────────────
    def _flash(self, parent, msg):
        if hasattr(parent, "_flash_lbl") and parent._flash_lbl.winfo_exists():
            parent._flash_lbl.config(text=msg)
            return
        lbl = tk.Label(parent, text=msg, bg=BG, fg=ERR, font=F_SEC,
                       anchor="w")
        lbl.pack(fill=tk.X, pady=(4, 0))
        parent._flash_lbl = lbl


if __name__ == "__main__":
    BookingApp().mainloop()
