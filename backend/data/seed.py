"""
Seed script: Reads JSON files and inserts data into Supabase tables.
Run: python -m backend.data.seed   (from project root)
"""
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from supabase import create_client
from config import settings

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "files")

BATCH_SIZE = 500


def load_json(filename):
    with open(os.path.join(FILES_DIR, filename), "r") as f:
        return json.load(f)


def batch_upsert(table: str, rows: list, batch_size: int = BATCH_SIZE):
    """Upsert rows in batches."""
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        supabase.table(table).upsert(batch).execute()
        total += len(batch)
        print(f"  {table}: {total}/{len(rows)}")


def seed_states():
    data = load_json("state-data.json")["state_data"]
    rows = [{"state_id": s["state_id"], "state_name": s["state_name"]} for s in data]
    batch_upsert("states", rows)


def seed_districts():
    data = load_json("district-data.json")["district_data"]
    rows = [
        {
            "id": d["id"],
            "state_id": d.get("state_id"),
            "district_name": d["district_name"],
        }
        for d in data
    ]
    batch_upsert("districts", rows)


def seed_markets():
    data = load_json("market-data.json")["market_data"]
    rows = [
        {
            "id": m["id"],
            "mkt_name": m["mkt_name"],
            "state_id": m.get("state_id"),
            "district_id": m.get("district_id"),
        }
        for m in data
    ]
    batch_upsert("markets", rows)


def seed_commodity_groups():
    data = load_json("cmdt-group-data.json")["cmdt_group_data"]
    rows = [{"id": g["id"], "cmdt_grp_name": g["cmdt_grp_name"]} for g in data]
    batch_upsert("commodity_groups", rows)


def seed_commodities():
    data = load_json("cmdt-data.json")["cmdt_data"]
    rows = [
        {
            "cmdt_id": c["cmdt_id"],
            "cmdt_name": c["cmdt_name"],
            "cmdt_group_id": c.get("cmdt_group_id"),
            "cmdt_type_flag": c.get("cmdt_type_flag"),
        }
        for c in data
    ]
    batch_upsert("commodities", rows)


def seed_varieties():
    data = load_json("variety-data.json")["variety_data"]
    rows = [{"id": v["id"], "variety_name": v["variety_name"]} for v in data]
    batch_upsert("varieties", rows)


def seed_grades():
    data = load_json("grade-data.json")["grade_data"]
    rows = [{"id": g["id"], "grade_name": g["grade_name"]} for g in data]
    batch_upsert("grades", rows)


def main():
    print("Seeding Supabase tables...")
    # Order matters: parents before children
    seed_states()
    seed_districts()
    seed_commodity_groups()
    seed_commodities()
    seed_varieties()
    seed_grades()
    seed_markets()  # last — depends on states + districts
    print("Done!")


if __name__ == "__main__":
    main()
