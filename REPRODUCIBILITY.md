# Reproducing the 3Y0K Analysis

This document describes the analysis pipeline from raw spot data to the live demo site.

The dataset it produces is published: download
[`3y0k-bouvet-island-2026.sqlite`](https://sourceforge.net/projects/ionis-ai/files/dxpeditions/)
and start at Step 4 to rebuild the site from it. Steps 1 to 3 record how that file was made; the
export and VOACAP runner scripts they name are not published with this demo.

## Prerequisites

For Step 4 onwards: Python 3.10+ and Node.js 20+. For Steps 1 to 3:

- ClickHouse with `rbn.bronze`, `pskr.bronze`, `solar.bronze`, `solar.dscovr`
- `voacapl` (v16.1207W) installed at `/usr/local/bin/voacapl`
- `~/itshfbc/` initialized via `makeitshfbc`
- IONIS-AI V22-gamma checkpoint (for model predictions — requires PyTorch + MPS or CUDA)

## Step 1 — Export Dataset from ClickHouse

```bash
python dxpeditions/export_dxpedition_analysis.py \
  --callsign 3Y0K \
  --start 2026-03-01 \
  --end 2026-03-14 \
  --grid JD04 \
  --entity "Bouvet Island" \
  --output /mnt/sourceforge/dxpeditions/
```

**Script**: `export_dxpedition_analysis.py` (not published)
**Output**: `3y0k-bouvet-island-2026.sqlite` with 5 tables (rbn_spots,
rbn_signatures, pskr_signatures, solar_timeline, dxpedition_info)

## Step 2 — Generate IONIS-AI V22-gamma Predictions

This step requires the production V22-gamma checkpoint and PyTorch. Run on a
machine with MPS (Mac) or CUDA (Linux) backend.

**Method**: Load the DXpedition SQLite signatures, run V22-gamma inference on
each (grid_pair, band, hour, SFI, Kp) tuple, output predictions CSV.
**Script**: `ionis-jupyter/notebooks/dxpedition-3y0k-bouvet-2026.ipynb` (Section 7)
**Output**: `3y0k-predictions.csv` (6,964 rows)

The predictions CSV is then inserted into the SQLite `predictions` table:

```python
import csv, sqlite3

conn = sqlite3.connect("3y0k-bouvet-island-2026.sqlite")
conn.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        band INTEGER, hour INTEGER, observed_snr REAL,
        predicted_sigma REAL, distance REAL, kp REAL,
        overridden INTEGER, source TEXT,
        predicted_snr_db REAL, observed_sigma REAL
    )
""")
with open("3y0k-predictions.csv") as f:
    reader = csv.DictReader(f)
    rows = [(
        int(r['band']), int(r['hour']), float(r['observed_snr']),
        float(r['predicted_sigma']), float(r['distance']), float(r['kp']),
        1 if r['overridden'] == 'True' else 0, r['source'],
        float(r['predicted_snr_db']), float(r['observed_sigma'])
    ) for r in reader]
conn.executemany("INSERT INTO predictions VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
conn.commit()
conn.close()
```

## Step 3 — Run VOACAP Predictions

```bash
python dxpeditions/voacap_dxpedition_runner.py \
  --input /mnt/sourceforge/dxpeditions/3y0k-bouvet-island-2026.sqlite \
  --workers 8 \
  --lat -54.42 \
  --lon 3.38
```

**Script**: `voacap_dxpedition_runner.py` (not published)
**Output**: Adds `voacap_snr` column to the `predictions`, `rbn_signatures`,
and `pskr_signatures` tables in the SQLite file.

**Important**: The `--lat` and `--lon` flags provide the exact DXpedition
coordinates. VOACAP's Fortran `antcalc.for` can crash at certain grid centroids
due to fixed-column format sensitivity. Use actual coordinates, not grid centroids.

**VOACAP configuration**: CCIR coefficients, Method 30 (complete system
performance), const17.voa antenna model (17 dBi constant gain). SSN derived
from SFI via `SSN ≈ SFI × 0.7`.

## Step 4 — Convert to Demo Site JSON

```bash
python scripts/sqlite-to-json.py \
  --input 3y0k-bouvet-island-2026.sqlite \
  --slug 3y0k \
  --output src/data/3y0k
```

**Script**: `scripts/sqlite-to-json.py`
**Output**: 8 JSON files in `src/data/3y0k/` (info, rbn-signatures,
pskr-signatures, solar-timeline, activity-timeline, band-stats, geography,
predictions)

## Step 5 — Build and Deploy

```bash
npm ci
npm run build   # Static export to out/
```

Merging into `main` publishes nothing. **Actions → Publish → Run workflow** builds it for
https://qso-graph.io/qso-graph-demo-dxpedition/ and deploys it to GitHub Pages, once CI has passed on
that commit.

## Data Sources

| Source | URL | Data Used |
|--------|-----|-----------|
| Reverse Beacon Network | reversebeacon.net | CW skimmer spots (dx_call = '3Y0K') |
| PSK Reporter | pskreporter.info | FT8/FT4 digital spots (sender_call = '3Y0K') |
| GFZ Potsdam | gfz-potsdam.de | Historical SFI, SSN, Kp, Ap indices |
| NOAA DSCOVR L1 | swpc.noaa.gov | Solar wind Bz, speed, density |
| VOACAP | github.com/jawatson/voacapl | HF propagation prediction engine (v16.1207W) |
