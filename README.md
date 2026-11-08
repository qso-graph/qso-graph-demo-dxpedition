# DXpedition Propagation Analysis Demo

Interactive web app for exploring propagation data from major DXpeditions. Part of the [qso-graph](https://qso-graph.io) project.

## Live Demo

**[https://qso-graph.io/qso-graph-demo-dxpedition/](https://qso-graph.io/qso-graph-demo-dxpedition/)**

## Current: 3Y0K Bouvet Island (March 2026)

Bouvet Island (DXCC #24), ranked #2 most wanted worldwide (Club Log). 102,000+ QSOs from 54°S in the South Atlantic.

### Pages

- **Overview**—DXpedition info, key stats, solar summary
- **Solar Conditions**—SFI, Kp, Bz timeline across the analysis window
- **Activity Timeline**—Hourly spot rates by band
- **Band Performance**—Per-band statistics and SNR distributions
- **Geographic Reach**—Great-circle paths, distance histograms, continental breakdown
- **Greyline Analysis**—Solar terminator, day/night propagation paths
- **Predictions**—IONIS-AI V22-gamma vs VOACAP vs observed, 3-way comparison

## Data Sources

- [Reverse Beacon Network](https://reversebeacon.net)—CW skimmer observations
- [PSK Reporter](https://pskreporter.info)—FT8/FT4 digital spots
- [NOAA SWPC](https://www.swpc.noaa.gov)—Solar flux, Kp index
- [GFZ Potsdam](https://www.gfz-potsdam.de)—Historical solar indices
- [DSCOVR L1](https://www.swpc.noaa.gov/products/real-time-solar-wind)—Solar wind Bz, speed, density

## Tech Stack

- Next.js 16 / TypeScript / Tailwind CSS
- Recharts for data visualization
- Leaflet for maps
- Static export—no server required

## Data Pipeline

```
export_dxpedition_analysis.py → SQLite dataset
sqlite-to-json.py → Static JSON files
Next.js static export → GitHub Pages (Actions → Publish)
```

## Development

```bash
npm install
npm run dev    # http://localhost:3000
npm run build  # static export to out/
```

## License

GPL-3.0-or-later—see [LICENSE](LICENSE).

## Credits

Built by [KI7MT](https://qrz.com/db/KI7MT) as part of [IONIS-AI](https://github.com/IONIS-AI).
