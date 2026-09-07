STATES = {
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Karnataka":   ["Bengaluru", "Mysuru"],
    "Delhi":       ["New Delhi"],
    "Tamil Nadu":  ["Chennai", "Coimbatore", "Madurai", "Virudhunagar",
                    "Tirunelveli", "Kovilpatti"],
    "Telangana":   ["Hyderabad"],
    "West Bengal": ["Kolkata"],
}

MOVIES = [
    "Jawan", "Pathaan", "RRR", "12th Fail", "Dune: Part Two", "Animal",
    "Leo", "Jailer", "Ponniyin Selvan II", "Salaar",
    "Vikram", "Kalki 2898 AD", "Oppenheimer", "Maharaja",
]

THEATRES = {
    "Mumbai":     ["PVR Phoenix", "INOX Nariman", "Cinepolis Andheri"],
    "Pune":       ["PVR Pavillion", "INOX Bund Garden"],
    "Nagpur":     ["INOX Eternity", "PVR Empress"],
    "Bengaluru":  ["PVR Orion", "INOX Garuda", "Cinepolis Forum"],
    "Mysuru":     ["INOX Mall of Mysore"],
    "New Delhi":  ["PVR Saket", "INOX Nehru Place", "Cinepolis DLF"],
    "Chennai":    ["PVR Express Avenue", "INOX Citi Centre"],
    "Coimbatore":   ["INOX Brookefields"],
    "Madurai":      ["INOX Vishaal de Mal", "PVR The Mall", "Ananda Theatre"],
    "Virudhunagar": ["Sri Krishna Cinemas", "Lakshmi Theatre"],
    "Tirunelveli":  ["Galaxy Cinemas", "PVR Tirunelveli", "Sangam Theatre"],
    "Kovilpatti":   ["Kovilpatti Cinemas", "Surya Theatre"],
    "Hyderabad":  ["PVR Forum", "INOX GVK One"],
    "Kolkata":    ["INOX Quest", "PVR South City"],
}

SHOWTIMES = ["10:00", "14:00", "19:00"]

SEAT_ROWS = ["A", "B", "C", "D", "E"]
SEAT_COLS = list(range(1, 9))

# Row-tier pricing (INR). Front rows are economy, back rows are premium.
SEAT_PRICES = {
    "A": 120,  # economy (front)
    "B": 120,
    "C": 180,  # standard
    "D": 180,
    "E": 250,  # premium (back)
}
TIER_NAMES = {120: "ECONOMY", 180: "STANDARD", 250: "PREMIUM"}


def seat_price(seat):
    return SEAT_PRICES[seat[0]]


def booking_key(city, theatre, movie, date, showtime):
    return f"{city}|{theatre}|{movie}|{date}|{showtime}"
