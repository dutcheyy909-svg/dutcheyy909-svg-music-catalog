def completeness_score(record):

    fields = [
        "website",
        "submission_url",
        "licensing_email",
        "source_url"
    ]

    completed = sum(
        1 for field in fields
        if record.get(field)
    )

    return round(
        (completed / len(fields)) * 100,
        2
    )

DATABASE = Path("research/batch_03_production_libraries.json")

COMPANIES = [
    "Universal Production Music",
    "APM Music",
    "Extreme Music",
    "Audio Network",
    "BMG Production Music",
    "Warner Chappell Production Music",
    "West One Music Group",
    "KPM Music",
    "Megatrax",
    "FirstCom Music",
    "Cavendish Music",
    "Score Production Music",
    "Alibi Music",
    "5 Alarm Music",
    "Jingle Punks"
]


def load_database():
    if DATABASE.exists():
        with open(DATABASE, "r", encoding="utf-8") as f:
            return json.load(f)

    return []


def save_database(data):
    with open(DATABASE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def create_record(company):
    return {
        "company": company,
        "country": "",
        "website": "",
        "submission_url": "",
        "licensing_email": "",
        "ar_email": "",
        "date_collected": datetime.utcnow().strftime("%Y-%m-%d"),
        "source_url": "",
        "verification_status": "Needs Review",

        "accepts_unsolicited": "",
        "indie_friendly": "",
        "exclusive_only": "",

        "focus": [],
        "genres": [],
        "moods": [],

        "major_clients": [],
        "major_networks": [],
        "major_streamers": [],

        "territories": [],

        "placement_count": 0,

        "past_placements": [],

        "metadata_notes": ""
    }


def initialize_batch():
    records = []

    for company in COMPANIES:
        records.append(create_record(company))

    save_database(records)

    print(f"Created {len(records)} records")


if __name__ == "__main__":
    initialize_batch()

def add_placement(record,
                  artist,
                  track,
                  production,
                  platform,
                  brand,
                  placement_type,
                  year,
                  source_url):

    placement = {
        "artist": artist,
        "track": track,
        "production": production,
        "platform": platform,
        "brand": brand,
        "placement_type": placement_type,
        "year": year,
        "source_url": source_url
    }

    record["past_placements"].append(placement)
    record["placement_count"] += 1

