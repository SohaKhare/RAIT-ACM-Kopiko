# curl -X POST "https://api.agmarknet.gov.in/v1/dashboard-data/" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json" \
#   -d '{
#     "dashboard": "marketwise_price_arrival",
#     "date": "2026-06-18",
#     "group": [100000],
#     "commodity": [100001],
#     "variety": 100021,
#     "state": 20,
#     "district": [356],
#     "market": [100009],
#     "grades": [4],
#     "limit": 30,
#     "format": "json"
#   }'
# {
#   "status": "success",
#   "message": "Data fetched successfully.",
#   "pagination": {
#     "total_count": 9,
#     "total_pages": 1,
#     "current_page": 1,
#     "next_page": null,
#     "previous_page": null,
#     "items_per_page": 10
#   },
#   "data": {
#     "columns": [
#       {
#         "key": "commodity_info",
#         "columns": [
#           {
#             "key": "cmdt_grp_name",
#             "title": "Commodity Group"
#           },
#           {
#             "key": "cmdt_name",
#             "title": "Commodity"
#           },
#           {
#             "key": "msp_price",
#             "title": "MSP (Rs./Quintal) 2026-27"
#           }
#         ]
#       },
#       {
#         "key": "price_group",
#         "title": "Price (Rs./Quintal)",
#         "columns": [
#           {
#             "key": "as_on_price",
#             "title": "17 Jun, 2026"
#           },
#           {
#             "key": "one_day_ago_price",
#             "title": "16 Jun, 2026"
#           },
#           {
#             "key": "two_day_ago_price",
#             "title": "15 Jun, 2026"
#           }
#         ]
#       },
#       {
#         "key": "arrival_group",
#         "title": "Arrival (Metric Tonnes)",
#         "columns": [
#           {
#             "key": "as_on_arrival",
#             "title": "17 Jun, 2026"
#           },
#           {
#             "key": "one_day_ago_arrival",
#             "title": "16 Jun, 2026"
#           },
#           {
#             "key": "two_day_ago_arrival",
#             "title": "15 Jun, 2026"
#           }
#         ]
#       }
#     ],
#     "records": [
#       {
#         "trend": "up",
#         "cmdt_name": "Bajra(Pearl Millet/Cumbu)",
#         "msp_price": "2775.00",
#         "as_on_price": "4000.00",
#         "as_on_arrival": "35.70",
#         "cmdt_grp_name": "Cereals",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": "4000.00",
#         "two_day_ago_price": "4000.00",
#         "one_day_ago_arrival": "88.90",
#         "two_day_ago_arrival": "79.80"
#       },
#       {
#         "trend": "up",
#         "cmdt_name": "Maize",
#         "msp_price": "2400.00",
#         "as_on_price": "2700.00",
#         "as_on_arrival": "29.90",
#         "cmdt_grp_name": "Cereals",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": "2700.00",
#         "two_day_ago_price": "2700.00",
#         "one_day_ago_arrival": "30.70",
#         "two_day_ago_arrival": "32.40"
#       },
#       {
#         "trend": "up",
#         "cmdt_name": "Wheat",
#         "msp_price": "2585.00",
#         "as_on_price": "4250.00",
#         "as_on_arrival": "473.60",
#         "cmdt_grp_name": "Cereals",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": "3950.00",
#         "two_day_ago_price": "3950.00",
#         "one_day_ago_arrival": "702.50",
#         "two_day_ago_arrival": "867.20"
#       },
#       {
#         "trend": "up",
#         "cmdt_name": "Mustard",
#         "msp_price": "6200.00",
#         "as_on_price": "8100.00",
#         "as_on_arrival": "18.20",
#         "cmdt_grp_name": "Oil Seeds",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": "8100.00",
#         "two_day_ago_price": null,
#         "one_day_ago_arrival": "4.60",
#         "two_day_ago_arrival": null
#       },
#       {
#         "trend": "up",
#         "cmdt_name": "Sesamum(Sesame,Gingelly,Til)",
#         "msp_price": "9846.00",
#         "as_on_price": "14500.00",
#         "as_on_arrival": "8.00",
#         "cmdt_grp_name": "Oil Seeds",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": "14500.00",
#         "two_day_ago_price": "14500.00",
#         "one_day_ago_arrival": "22.40",
#         "two_day_ago_arrival": "1.40"
#       },
#       {
#         "trend": "up",
#         "cmdt_name": "Bengal Gram(Gram)(Whole)",
#         "msp_price": "5875.00",
#         "as_on_price": "7200.00",
#         "as_on_arrival": "50.30",
#         "cmdt_grp_name": "Pulses",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": "7200.00",
#         "two_day_ago_price": "7200.00",
#         "one_day_ago_arrival": "201.50",
#         "two_day_ago_arrival": "134.30"
#       },
#       {
#         "trend": "up",
#         "cmdt_name": "Black Gram(Urd Beans)(Whole)",
#         "msp_price": "7800.00",
#         "as_on_price": "9250.00",
#         "as_on_arrival": "16.50",
#         "cmdt_grp_name": "Pulses",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": null,
#         "two_day_ago_price": "9250.00",
#         "one_day_ago_arrival": null,
#         "two_day_ago_arrival": "10.60"
#       },
#       {
#         "trend": "up",
#         "cmdt_name": "Green Gram(Moong)(Whole)",
#         "msp_price": "8768.00",
#         "as_on_price": "10500.00",
#         "as_on_arrival": "60.70",
#         "cmdt_grp_name": "Pulses",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": "10500.00",
#         "two_day_ago_price": "10500.00",
#         "one_day_ago_arrival": "49.50",
#         "two_day_ago_arrival": "59.90"
#       },
#       {
#         "trend": "up",
#         "cmdt_name": "Lentil(Masur)(Whole)",
#         "msp_price": "7000.00",
#         "as_on_price": "9050.00",
#         "as_on_arrival": "47.70",
#         "cmdt_grp_name": "Pulses",
#         "reported_date": "17-06-2026",
#         "one_day_ago_price": "9050.00",
#         "two_day_ago_price": "9050.00",
#         "one_day_ago_arrival": "26.50",
#         "two_day_ago_arrival": "37.50"
#       }
#     ],
#     "count": {}
#   }
# }

import requests
from datetime import date as dt_date
from typing import Optional
from supabase import create_client
from config import settings

# Defaults (All)
DEFAULT_STATE = 100006
DEFAULT_DISTRICT = [100007]
DEFAULT_MARKET = [100009]

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def _resolve_location(state: Optional[str], district: Optional[str], market: Optional[str]):
    """
    Resolve state/district/market strings to IDs from Supabase.
    Hierarchy enforcement: market -> district -> state (child overrides parent).
    """
    state_id = DEFAULT_STATE
    district_id = DEFAULT_DISTRICT
    market_id = DEFAULT_MARKET
    state_name = "All States"
    district_name = "All Districts"
    market_name = "All Markets"

    # 1. Resolve market first (highest priority)
    if market:
        result = (
            supabase.table("markets")
            .select("id, mkt_name, state_id, district_id")
            .neq("id", 100009)
            .ilike("mkt_name", f"%{market}%")
            .limit(1)
            .execute()
        )
        if result.data:
            m = result.data[0]
            market_id = [m["id"]]
            market_name = m["mkt_name"]

            # enforce hierarchy: market dictates district and state
            if m.get("district_id"):
                district_id = [m["district_id"]]
                dt = supabase.table("districts").select("district_name").eq("id", m["district_id"]).limit(1).execute()
                if dt.data:
                    district_name = dt.data[0]["district_name"]

            if m.get("state_id"):
                state_id = m["state_id"]
                st = supabase.table("states").select("state_name").eq("state_id", m["state_id"]).limit(1).execute()
                if st.data:
                    state_name = st.data[0]["state_name"]

            return {
                "state_id": state_id, "state_name": state_name,
                "district_id": district_id, "district_name": district_name,
                "market_id": market_id, "market_name": market_name,
            }

    # 2. Resolve district (medium priority)
    if district:
        result = (
            supabase.table("districts")
            .select("id, district_name, state_id")
            .neq("id", 100007)
            .ilike("district_name", f"%{district}%")
            .limit(1)
            .execute()
        )
        if result.data:
            d = result.data[0]
            district_id = [d["id"]]
            district_name = d["district_name"]

            # enforce hierarchy: district dictates state
            if d.get("state_id"):
                state_id = d["state_id"]
                st = supabase.table("states").select("state_name").eq("state_id", d["state_id"]).limit(1).execute()
                if st.data:
                    state_name = st.data[0]["state_name"]

            return {
                "state_id": state_id, "state_name": state_name,
                "district_id": district_id, "district_name": district_name,
                "market_id": market_id, "market_name": market_name,
            }

    # 3. Resolve state (lowest priority)
    if state:
        result = (
            supabase.table("states")
            .select("state_id, state_name")
            .neq("state_id", 100006)
            .ilike("state_name", f"%{state}%")
            .limit(1)
            .execute()
        )
        if result.data:
            s = result.data[0]
            state_id = s["state_id"]
            state_name = s["state_name"]

            return {
                "state_id": state_id, "state_name": state_name,
                "district_id": district_id, "district_name": district_name,
                "market_id": market_id, "market_name": market_name,
            }

    # No match — all defaults
    return {
        "state_id": state_id, "state_name": state_name,
        "district_id": district_id, "district_name": district_name,
        "market_id": market_id, "market_name": market_name,
    }


def get_mandi_data(state: Optional[str] = None, district: Optional[str] = None, market: Optional[str] = None):
    """
    Accepts optional state, district, market strings.
    Resolves IDs from Supabase with hierarchy enforcement.
    Returns API JSON with resolved_location metadata.
    """
    resolved = _resolve_location(state, district, market)
    today = dt_date.today().isoformat()

    url = "https://api.agmarknet.gov.in/v1/dashboard-data/"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; Kopiko/1.0)"
    }

    payload = {
        "dashboard": "marketwise_price_arrival",
        "date": today,
        "group": [100000],
        "commodity": [100001],
        "variety": 100021,
        "state": resolved["state_id"],
        "district": resolved["district_id"],
        "market": resolved["market_id"],
        "grades": [4],
        "limit": 30,
        "format": "json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        api_data = response.json()
    except requests.exceptions.RequestException as e:
        api_data = {"status": "error", "message": str(e)}

    return {
        "resolved_location": {
            "state": resolved["state_name"],
            "district": resolved["district_name"],
            "market": resolved["market_name"]
        },
        "api_response": api_data
    }
