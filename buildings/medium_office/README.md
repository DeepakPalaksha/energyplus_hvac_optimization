# DOE Medium Office Reference Building

Run `download_building.sh` to fetch a ready-to-simulate IDF.

**Verified 2026-07-01:** the script successfully pulls
`ASHRAE90.1_OfficeMedium_STD2013_Duluth.idf` from the NREL
`OpenStudio-Prototype-Buildings` GitHub repo (502 KB, EnergyPlus IDF v8.0 format).

- **Location baked into the file:** Duluth, MN (46.83°N) — DOE climate zone 7,
  the coldest zone in the US reference set and the closest available match to
  Stockholm/Oslo climate severity. Design days, ground temperatures, and HVAC
  autosizing are all calibrated to this climate.
- **Building:** ~4,982 m², 3-story, 15 zones (5 per floor: 4 perimeter + 1 core),
  VAV with reheat, packaged rooftop units.
- **Vintage:** ASHRAE 90.1-2013 (new construction code minimum at time of
  publication — i.e. not a high-performance building, a code-baseline one).

## Before you simulate

1. **Update the IDF version.** This file is v8.0; if your installed EnergyPlus
   is newer (check `energyplus --version`), run it through `IDFVersionUpdater`
   (ships with every EnergyPlus install, in the `PreProcess/IDFVersionUpdater`
   folder) to avoid silent misinterpretation of changed object fields.

2. **Decide how to handle the Nordic mismatch.** Two honest options:
   - **Keep US envelope, swap only weather** (fast, what `run_experiment.py`
     does by default): tells you how *this specific envelope* would perform
     under Nordic weather — useful for weather-sensitivity analysis, not for
     claiming realistic Nordic energy numbers, since Nordic building codes
     (Swedish BBR, Norwegian TEK17) require substantially better insulation
     than US 90.1-2013.
   - **Adjust envelope U-values to Nordic code minimums** (more correct, more
     work): edit `Material`/`Construction` objects for walls/roof/windows via
     `eppy` before running. Not yet scripted — see TASKS.md Phase 2.

3. **Re-run sizing if you change climate or envelope.** `SimulationControl`
   in the IDF has `Do Zone/System Sizing Calculation = Yes`, so EnergyPlus
   will auto-resize HVAC capacity for whatever weather file you point it at —
   good, this means Duluth-sized equipment won't silently apply to a Stockholm
   run. But if you only care about a fixed installed capacity (e.g. testing an
   already-built Nordic office), you'll want to lock sizing instead.
