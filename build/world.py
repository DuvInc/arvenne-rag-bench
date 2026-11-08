"""The fictional company behind the corpus. Every fact a document states comes from here,
so that two documents never disagree by accident. Planned disagreements are listed in
CONTRADICTIONS and documented in docs/DESIGN.md."""

from datetime import date

YEAR = 2025
COMPANY = "Arvenne Cycles SAS"
HQ = "14 rue des Tanneurs, 69007 Lyon, France"
PLANT = "Villefranche-sur-Saône"
FOUNDED = 2019

PEOPLE = {
    "Inès Marchetti": ("Chief Executive Officer", None, "Executive"),
    "Tomasz Wielgosz": ("Chief Technology Officer", "Inès Marchetti", "Engineering"),
    "Priya Raman": ("Lead Engineer, Battery & Electronics", "Tomasz Wielgosz", "Engineering"),
    "Jonas Eberhardt": ("Lead Engineer, Frame & Mechanical", "Tomasz Wielgosz", "Engineering"),
    "Lucie Ferrand": ("Test Engineer", "Jonas Eberhardt", "Engineering"),
    "Camille Dufresne": ("Chief Financial Officer", "Inès Marchetti", "Finance & Admin"),
    "Hugo Lambert": ("Financial Controller", "Camille Dufresne", "Finance & Admin"),
    "Aurélie Moreau": ("HR Manager", "Camille Dufresne", "Finance & Admin"),
    "Mathieu Okafor": ("Head of Operations", "Inès Marchetti", "Operations"),
    "Elena Vasquez": ("Plant Manager", "Mathieu Okafor", "Operations"),
    "Karim Benali": ("Logistics Manager", "Mathieu Okafor", "Operations"),
    "Nadia Kowalczyk": ("Quality Manager", "Mathieu Okafor", "Operations"),
    "Ruth Achterberg": ("Head of Sales", "Inès Marchetti", "Sales"),
    "Felix Hartmann": ("Key Account Manager DACH", "Ruth Achterberg", "Sales"),
    "Chloé Martin": ("Dealer Network Manager France & Benelux", "Ruth Achterberg", "Sales"),
    "Ben Whitaker": ("UK & Fleet Sales Manager", "Ruth Achterberg", "Sales"),
    "Marco Bellini": ("Customer Care Lead", "Ruth Achterberg", "Sales"),
    "Léa Fontaine": ("Head of Marketing", "Inès Marchetti", "Marketing"),
}

# Prices: rrp = recommended retail price incl. 20% French VAT, in EUR. CHF and GBP are export
# list prices excl. VAT. The Mule went up 4% in every market on 2025-07-01, rounded to the
# nearest 10 in local currency (board minutes of 2025-06-24).
PRODUCTS = {
    "Mule": dict(kind="Longtail", motor="Mid-drive, 85 Nm", torque=85, battery_wh=625,
                 range_km=(50, 90), max_load=210, weight=32.0, rrp=4290, rrp_after=4460,
                 chf=3590, chf_after=3730, gbp=3050, gbp_after=3170, line="A", supplier="Voltaris",
                 charge_h=4.5),
    "Barge": dict(kind="Front-loader (first generation)", motor="Mid-drive, 85 Nm", torque=85,
                  battery_wh=500, range_km=(40, 75), max_load=250, weight=41.0, rrp=5190,
                  chf=4340, gbp=3690, line="B", supplier="Voltaris", charge_h=4.0),
    "Barge 2": dict(kind="Front-loader", motor="Mid-drive, 90 Nm", torque=90, battery_wh=750,
                    range_km=(60, 120), max_load=260, weight=39.5, rrp=5690, chf=4760,
                    gbp=4050, line="B", supplier="Voltaris", charge_h=5.0),
    "Trike": dict(kind="Tilting three-wheeler", motor="Front hub, 65 Nm", torque=65,
                  battery_wh=625, range_km=(35, 60), max_load=280, weight=52.0, rrp=6490,
                  chf=5430, gbp=4610, line="B", supplier="Voltaris", charge_h=4.5),
    "Pup": dict(kind="Compact family carrier", motor="Rear hub, 50 Nm", torque=50,
                battery_wh=400, range_km=(30, 55), max_load=180, weight=26.5, rrp=3190,
                chf=2670, gbp=2270, line="A", supplier="Kelda Energy", charge_h=3.5),
}
VAT_FR = 0.20
PRICE_RISE_DATE = date(2025, 7, 1)
BARGE_END_OF_SALE = date(2025, 9, 30)
BARGE2_FIRST_ORDER = date(2025, 9, 22)
BARGE2_LAUNCH_EVENT = date(2025, 9, 15)
BARGE2_DELIVERIES = date(2025, 10, 1)
RANGE_EXTENDER_WH = 500
RANGE_EXTENDER_PRICE = 690
BARGE2_RANGE_WITH_EXTENDER = 140

FX = {"EUR": 1.0, "CHF": 0.94, "GBP": 0.85}  # units of currency per 1 EUR, budget assumption
VAT = {"FR": 20, "DE": 19, "NL": 21, "BE": 21, "AT": 20, "CH": 8.1, "UK": 20}
REVENUE_TARGET_EUR = 12_000_000
TIER_DISCOUNT = {"Gold": 30, "Silver": 27, "Bronze": 25}

DEALERS = [
    # id, name, city, country, tier, onboarded, status
    ("D001", "Cycles du Dauphiné", "Grenoble", "FR", "Gold", "2021-04-12", "Active"),
    ("D002", "Vélo Cargo Lyon", "Lyon", "FR", "Gold", "2020-09-01", "Active"),
    ("D003", "Atelier Roue Libre", "Nantes", "FR", "Silver", "2022-02-14", "Active"),
    ("D004", "Bicyclettes de Bordeaux", "Bordeaux", "FR", "Silver", "2022-06-20", "Active"),
    ("D005", "Cargo & Co Paris 11", "Paris", "FR", "Gold", "2021-01-18", "Active"),
    ("D006", "Rayons Verts", "Lille", "FR", "Bronze", "2023-03-06", "Active"),
    ("D007", "Le Biclou", "Strasbourg", "FR", "Silver", "2022-10-03", "Active"),
    ("D008", "Cyclopolis Toulouse", "Toulouse", "FR", "Bronze", "2023-09-11", "Active"),
    ("D009", "Vélo Sud Marseille", "Marseille", "FR", "Bronze", "2024-02-05", "Active"),
    ("D010", "Les Pédales Rennaises", "Rennes", "FR", "Silver", "2022-04-25", "Active"),
    ("D011", "Lastenrad Kontor", "Hamburg", "DE", "Gold", "2021-06-07", "Active"),
    ("D012", "Radhaus Freiburg", "Freiburg", "DE", "Silver", "2022-03-21", "Active"),
    ("D013", "Kiezrad Berlin", "Berlin", "DE", "Gold", "2021-11-15", "Active"),
    ("D014", "Velo Werk München", "Munich", "DE", "Silver", "2022-08-29", "Terminated 2025-06-30"),
    ("D015", "Rheinrad Köln", "Cologne", "DE", "Bronze", "2023-05-15", "Active"),
    ("D016", "Pedalwerk Leipzig", "Leipzig", "DE", "Bronze", "2024-01-22", "Active"),
    ("D017", "Bakfiets Centraal", "Amsterdam", "NL", "Gold", "2021-03-01", "Active"),
    ("D018", "Fietsmaat Utrecht", "Utrecht", "NL", "Silver", "2022-05-09", "Active"),
    ("D019", "De Groene Trapper", "Rotterdam", "NL", "Silver", "2022-11-14", "Active"),
    ("D020", "Haags Fietshuis", "The Hague", "NL", "Bronze", "2023-08-28", "Active"),
    ("D021", "Eindhoven Cargo", "Eindhoven", "NL", "Bronze", "2024-04-15", "Active"),
    ("D022", "Vélo Bruxelles Cargo", "Brussels", "BE", "Silver", "2022-09-12", "Active"),
    ("D023", "Gentse Bakfietsen", "Ghent", "BE", "Bronze", "2023-10-02", "Active"),
    ("D024", "Velostation Zürich", "Zurich", "CH", "Gold", "2022-01-10", "Active"),
    ("D025", "Cycles Léman", "Lausanne", "CH", "Silver", "2023-04-03", "Active"),
    ("D026", "Cargo Cycle Bristol", "Bristol", "UK", "Silver", "2023-02-20", "Active"),
    ("D027", "Long Haul Bikes", "London", "UK", "Gold", "2022-07-04", "Active"),
    ("D028", "Lastenrad Wien", "Vienna", "AT", "Silver", "2023-06-12", "Active"),
    ("D029", "Bakfietsenhuis Utrecht", "Utrecht", "NL", "Bronze", "2025-10-06", "Active"),
    ("D030", "Leidse Lastfiets", "Leiden", "NL", "Bronze", "2025-10-20", "Active"),
    ("D031", "Antwerp Cargo Bikes", "Antwerp", "BE", "Bronze", "2025-11-03", "Active"),
    ("D032", "Zwolle Fietswerk", "Zwolle", "NL", "Bronze", "2025-12-01", "Active"),
]
ACCOUNT_MANAGER = {"FR": "Chloé Martin", "BE": "Chloé Martin", "NL": "Chloé Martin",
                   "DE": "Felix Hartmann", "AT": "Felix Hartmann", "CH": "Felix Hartmann",
                   "UK": "Ben Whitaker"}

# Fleet (B2B) orders, planted by hand: customer, date, country, model, qty, discount, status
FLEET = [
    ("Fietskoerier Utrecht", "2025-02-25", "NL", "Barge", 10, 12, "Delivered"),
    ("Pédalo Logistique", "2025-03-12", "FR", "Barge", 20, 15, "Delivered"),
    ("Hôtel Groupe Alpin", "2025-03-27", "FR", "Mule", 12, 12, "Delivered"),
    ("Stadtbote Berlin", "2025-04-08", "DE", "Trike", 12, 14, "Delivered"),
    ("Thames Florists Group", "2025-04-15", "UK", "Pup", 8, 12, "Delivered"),
    ("Kita Sonnenschein Verbund", "2025-05-06", "DE", "Pup", 9, 12, "Delivered"),
    ("GreenDrop London", "2025-05-21", "UK", "Mule", 18, 12, "Delivered"),
    ("Bruxelles Propre", "2025-06-10", "BE", "Trike", 8, 12, "Delivered"),
    ("Stadtbote Berlin", "2025-06-17", "DE", "Trike", 8, 14, "Delivered"),
    ("Courses Vertes Lyon", "2025-07-03", "FR", "Mule", 16, 13, "Delivered"),
    ("Fietskoerier Utrecht", "2025-08-19", "NL", "Barge", 12, 12, "Delivered"),
    ("GreenDrop London", "2025-09-09", "UK", "Mule", 16, 12, "Cancelled"),
    ("Kita Sonnenschein Verbund", "2025-09-30", "DE", "Barge", 11, 14, "Delivered"),
    ("Pédalo Logistique", "2025-10-20", "FR", "Barge 2", 25, 15, "Delivered"),
    ("Stadtbote Berlin", "2025-11-04", "DE", "Barge 2", 15, 16, "Delivered"),
    ("Courses Vertes Lyon", "2025-11-18", "FR", "Pup", 10, 12, "Delivered"),
    ("GreenDrop London", "2025-12-02", "UK", "Barge 2", 14, 13, "Delivered"),
    ("Hôtel Groupe Alpin", "2025-12-09", "FR", "Mule", 8, 12, "Delivered"),
]

BLACK_FRIDAY = (date(2025, 11, 24), date(2025, 12, 1))

# Voltaris battery lots, by production start date window (inclusive)
VOLTARIS_LOTS = [
    ("VL-2501-A", "2025-01-01", "2025-02-09"),
    ("VL-2502-A", "2025-02-10", "2025-03-20"),
    ("VL-2503-A", "2025-03-21", "2025-04-25"),
    ("VL-2504-A", "2025-04-26", "2025-05-28"),
    ("VL-2505-B", "2025-05-29", "2025-07-02"),
    ("VL-2507-A", "2025-07-03", "2025-07-13"),
    ("VL-2507-B", "2025-07-14", "2025-08-27"),
    ("VL-2508-C", "2025-08-28", "2025-10-10"),
    ("VL-2510-A", "2025-10-11", "2025-11-15"),
    ("VL-2511-A", "2025-11-16", "2025-12-31"),
]
KELDA_LOTS = [
    ("KE-2501", "2025-01-01", "2025-03-31"),
    ("KE-2504", "2025-04-01", "2025-06-30"),
    ("KE-2507", "2025-07-01", "2025-09-30"),
    ("KE-2510", "2025-10-01", "2025-12-31"),
]
BAD_LOT = "VL-2507-B"
PLANT_CLOSURE = (date(2025, 8, 4), date(2025, 8, 17))

# Voltaris contract and the late lot
CONTRACT = dict(
    late_pct_per_week=1.5, late_cap_pct=9.0, fm_notice_business_days=5,
    failure_threshold_pct=1.0, handling_fee=40, payment_days=45,
)
LATE_LOT = "VL-2508-C"
LATE_LOT_PROMISED = date(2025, 8, 4)
LATE_LOT_ETA_EMAIL = date(2025, 8, 26)
LATE_LOT_DELIVERED = date(2025, 8, 27)
LATE_LOT_VALUE = 185_160  # 240 x VP-625 at 268 + 380 x VP-750 at 318
LATE_LOT_PACKS = {"VP-625": 240, "VP-750": 380}
PACK_PRICES = {"VP-500": 214, "VP-625": 268, "VP-750": 318, "VP-RX500": 236}
STRIKE_START = date(2025, 7, 30)
FM_NOTICE_DATE = date(2025, 8, 18)

# Expense policy
HOTEL_CAP_OLD_EUR = 150
PER_DIEM_OLD = 45
PER_DIEM_NEW = 55
PER_DIEM_NEW_CH = 60  # CHF
TRAVEL_UPDATE_DATE = date(2025, 9, 1)
HOTEL_CAPS_NEW = {"France": "EUR 140 (Paris EUR 190)", "Germany": "EUR 150",
                  "Netherlands": "EUR 160", "Belgium": "EUR 150", "Austria": "EUR 150",
                  "Switzerland": "CHF 230", "United Kingdom": "GBP 170"}
ZURICH_ROOM_CHF = 238.00
ZURICH_TAX_CHF = 3.50
ZURICH_NIGHTS = 2
ZURICH_BREAKFAST_CHF = 0  # included

# Intentional disagreements (see docs/DESIGN.md)
TRIKE_MAX_LOAD_FAQ = 250
HEADCOUNT_Q3_DECK = 81
HEADCOUNT_Q3_MINUTES_Q4 = 79

# Customer letter
LETTER_NAME = "Margot Leclerc"
LETTER_CITY = "Grenoble"
LETTER_DATE = date(2025, 11, 3)
LETTER_TAXI = 65
