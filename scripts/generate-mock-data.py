#!/usr/bin/env python3
"""Generate realistic mock JSON data for 3Y0K Bouvet demo.

Superseded by sqlite-to-json.py, which converts the published SQLite.
"""
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).parent.parent / "src" / "data" / "3y0k"
random.seed(42)

BANDS = {
    102: "160m", 103: "80m", 104: "60m", 105: "40m", 106: "30m",
    107: "20m", 108: "17m", 109: "15m", 110: "12m", 111: "10m",
}

# Realistic skimmer grids worldwide
SKIMMER_GRIDS = [
    "FN31", "FN42", "FM19", "EM73", "EN91", "DN70", "DM79",
    "CM87", "JN48", "JO31", "JO59", "JO22", "IO91", "IO80",
    "KO85", "KO02", "PM95", "QM06", "PK04", "OF88",
    "RE78", "QF22", "QF56", "LO23", "GF05", "FF46",
]


def grid_to_latlon(grid):
    g = grid.upper()
    lon = (ord(g[0]) - 65) * 20 - 180 + int(g[2]) * 2 + 1
    lat = (ord(g[1]) - 65) * 10 - 90 + int(g[3]) + 0.5
    return lat, lon


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# --- Solar Timeline ---
def gen_solar():
    rows = []
    start = datetime(2026, 2, 27)
    end = datetime(2026, 3, 17)
    d = start
    base_sfi = 158
    while d < end:
        for h in range(0, 24, 3):
            day_offset = (d - start).days
            sfi = base_sfi + 8 * math.sin(day_offset * 0.4) + random.uniform(-3, 3)
            ssn = max(0, 120 + 15 * math.sin(day_offset * 0.3) + random.uniform(-10, 10))
            # Storm event around Mar 8-9
            storm = 1 if 9 <= day_offset <= 11 else 0
            kp = 1.0 + storm * 2.5 + random.uniform(0, 1.5)
            ap = kp * 4 + random.uniform(-2, 2)
            bz = -2 + storm * (-5) + random.uniform(-3, 3)
            rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "hour": h,
                "sfi": round(sfi, 1),
                "ssn": round(ssn),
                "kp": round(min(kp, 6), 2),
                "ap": round(max(0, ap)),
                "bz_min": round(bz - 2, 1),
                "bz_max": round(bz + 2, 1),
                "bz_avg": round(bz, 1),
                "wind_speed": round(380 + storm * 150 + random.uniform(-50, 50)),
                "density": round(4 + storm * 8 + random.uniform(-1, 3), 1),
            })
        d += timedelta(days=1)
    return rows


# --- Activity Timeline ---
def gen_activity():
    rows = []
    start = datetime(2026, 3, 1)
    end = datetime(2026, 3, 15)
    d = start
    while d < end:
        for h in range(24):
            entry = {"date": d.strftime("%Y-%m-%d"), "hour": h, "total": 0}
            for band_id, name in BANDS.items():
                # More spots on 20m/15m/10m during daytime (UTC), less at night
                base = 0
                if band_id in (107, 109, 111):  # 20m, 15m, 10m
                    base = 80 if 8 <= h <= 20 else 10
                elif band_id in (105, 106):  # 40m, 30m
                    base = 50 if h <= 6 or h >= 18 else 25
                elif band_id in (102, 103):  # 160m, 80m
                    base = 20 if h <= 4 or h >= 22 else 2
                elif band_id in (108, 110):  # 17m, 12m WARC
                    base = 30 if 10 <= h <= 18 else 5
                else:
                    base = 5
                count = max(0, int(base + random.uniform(-base * 0.4, base * 0.4)))
                entry[f"band_{band_id}"] = count
                entry["total"] += count
            rows.append(entry)
        d += timedelta(days=1)
    return rows


# --- Band Stats ---
def gen_band_stats():
    stats = []
    for band_id, name in BANDS.items():
        base_spots = {102: 2100, 103: 5800, 104: 800, 105: 18200, 106: 12400,
                      107: 48300, 108: 9600, 109: 32100, 110: 6200, 111: 21400}
        total = base_spots.get(band_id, 1000) + random.randint(-500, 500)
        snr_base = {102: 8, 103: 10, 105: 14, 106: 15, 107: 16,
                    108: 14, 109: 18, 110: 15, 111: 20}
        snr_mid = snr_base.get(band_id, 12)
        dist = sorted([max(1, int(random.gauss(snr_mid, 5))) for _ in range(20)])
        stats.append({
            "band": band_id,
            "band_name": name,
            "total_spots": total,
            "unique_skimmers": random.randint(80, 450),
            "snr_min": max(1, snr_mid - 12),
            "snr_max": min(45, snr_mid + 15),
            "snr_median": snr_mid,
            "snr_mean": round(snr_mid + random.uniform(-1, 1), 1),
            "peak_hour": random.choice([14, 15, 16, 17, 18]),
            "first_spot_hour": random.randint(6, 10),
            "last_spot_hour": random.randint(20, 23),
            "snr_distribution": dist,
        })
    return stats


# --- Geography ---
def gen_geography():
    bouvet_lat, bouvet_lon = -54.42, 3.38
    arcs = []
    continent_map = {}
    distance_bins_map = {}

    for grid in SKIMMER_GRIDS:
        lat, lon = grid_to_latlon(grid)
        dist = haversine(bouvet_lat, bouvet_lon, lat, lon)
        # Determine continent from grid
        if grid.startswith(("FN", "FM", "EM", "EN", "DN", "DM", "CM")):
            cont = "NA"
        elif grid.startswith(("JN", "JO", "IO", "KO")):
            cont = "EU"
        elif grid.startswith(("PM", "QM", "PK")):
            cont = "AS"
        elif grid.startswith(("QF",)):
            cont = "OC"
        elif grid.startswith(("RE", "OF")):
            cont = "AF"
        elif grid.startswith(("GF", "FF")):
            cont = "SA"
        elif grid.startswith("LO"):
            cont = "EU"
        else:
            cont = "OC"

        for band_id in [105, 106, 107, 108, 109, 110, 111]:
            spots = random.randint(20, 800)
            snr = round(random.uniform(5, 25), 1)
            arcs.append({
                "rx_grid_4": grid,
                "rx_lat": lat,
                "rx_lon": lon,
                "band": band_id,
                "spot_count": spots,
                "median_snr": snr,
            })
            key = (cont, band_id)
            continent_map[key] = continent_map.get(key, 0) + spots

            bin_start = int(dist // 2000) * 2000
            dkey = (band_id, bin_start)
            distance_bins_map[dkey] = distance_bins_map.get(dkey, 0) + spots

    continent_breakdown = [
        {"continent": c, "band": b, "band_name": BANDS[b], "spot_count": cnt}
        for (c, b), cnt in sorted(continent_map.items())
    ]
    distance_bins = [
        {"band": b, "band_name": BANDS[b], "bin_start": bs, "bin_end": bs + 2000, "count": cnt}
        for (b, bs), cnt in sorted(distance_bins_map.items())
    ]

    return {
        "continent_breakdown": continent_breakdown,
        "distance_bins": distance_bins,
        "arcs": arcs,
    }


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    solar = gen_solar()
    with open(OUT / "solar-timeline.json", "w") as f:
        json.dump(solar, f, separators=(",", ":"))
    print(f"solar-timeline.json: {len(solar)} rows")

    activity = gen_activity()
    with open(OUT / "activity-timeline.json", "w") as f:
        json.dump(activity, f, separators=(",", ":"))
    print(f"activity-timeline.json: {len(activity)} rows")

    band_stats = gen_band_stats()
    with open(OUT / "band-stats.json", "w") as f:
        json.dump(band_stats, f, separators=(",", ":"))
    print(f"band-stats.json: {len(band_stats)} bands")

    geography = gen_geography()
    with open(OUT / "geography.json", "w") as f:
        json.dump(geography, f, separators=(",", ":"))
    print(f"geography.json: {len(geography['arcs'])} arcs")

    # Empty placeholders for signature files (real data later)
    for name in ["rbn-signatures.json", "pskr-signatures.json"]:
        with open(OUT / name, "w") as f:
            json.dump([], f)
        print(f"{name}: placeholder")

    print("Done.")
