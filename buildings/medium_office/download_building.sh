#!/usr/bin/env bash
# Downloads the DOE Commercial Reference Building - Medium Office IDF.
#
# Source: NREL OpenStudio-Prototype-Buildings repo (GitHub mirror of the
# official DOE/PNNL reference building files). These IDFs are old
# (EnergyPlus v7.2/8.x vintage) — you will likely need to run them through
# IDFVersionUpdater (ships with EnergyPlus) before simulating with a modern
# EnergyPlus version.
#
# If this specific path has moved, browse:
#   https://github.com/NREL/OpenStudio-Prototype-Buildings
# and search for "MediumOffice" — there are variants per vintage
# (DOE Ref Pre-1980, DOE Ref 1980-2004, 90.1-2004, 90.1-2010, 90.1-2013).

set -euo pipefail
cd "$(dirname "$0")"

# Verified working source (checked 2026-07-01): the "legacy prototype idf files"
# folder in this repo contains ready-to-run ASHRAE 90.1 prototype IDFs (EnergyPlus
# v8.0 format — you WILL need to run these through IDFVersionUpdater, which ships
# with EnergyPlus, to bring them up to your installed version).
#
# Naming is inconsistent across vintages: "ASHRAE90.1_" (older) vs "ASHRAE901_"
# (newer STD years). Climate is baked into the file (design days, ground temps,
# HVAC sizing) via the reference city — there is no separate "climate-neutral"
# version. For Nordic-relevant analysis, closest cold-climate reference cities
# in the DOE set are Duluth (zone 7), Helena (6B), Minneapolis (6A), Chicago (5A).
BASE="https://github.com/NREL/OpenStudio-Prototype-Buildings/raw/refs/heads/master/regression%20test/legacy%20prototype%20idf%20files"

CANDIDATES=(
  "ASHRAE90.1_OfficeMedium_STD2013_Duluth.idf"
  "ASHRAE901_OfficeMedium_STD2013_Duluth.idf"
  "ASHRAE90.1_OfficeMedium_STD2013_Minneapolis.idf"
  "ASHRAE901_OfficeMedium_STD2013_Minneapolis.idf"
  "ASHRAE90.1_OfficeMedium_STD2013_Chicago.idf"
  "ASHRAE90.1_OfficeMedium_STD2013_El_Paso.idf"   # confirmed to exist — reliable fallback for pipeline testing
)

echo "Attempting to fetch a DOE Medium Office prototype IDF..."
for fname in "${CANDIDATES[@]}"; do
  url="${BASE}/${fname}"
  echo "  trying: ${fname}"
  if curl -fsSL "${url}" -o "RefBldgMediumOffice.idf"; then
    echo "Downloaded ${fname} -> buildings/medium_office/RefBldgMediumOffice.idf"
    echo "NOTE: this is climate-zone-specific (design days/HVAC sizing baked in)."
    echo "Run IDFVersionUpdater before simulating. Swap the weather file at runtime"
    echo "via the -w flag or Site:Location object — envelope/HVAC sizing stays as-is"
    echo "unless you also re-run sizing (see TASKS.md Phase 2)."
    exit 0
  fi
done

cat <<'EOF'

Automatic download failed — the exact file path in the GitHub repo changes
over time. Get the file manually from one of:

  1. https://github.com/NREL/OpenStudio-Prototype-Buildings (search "MediumOffice")
  2. https://www.energy.gov/eere/buildings/commercial-reference-buildings
     (official DOE source — ZIP includes IDF + EPW per climate zone)
  3. https://data.openei.org/submissions/160 (OpenEI mirror with docs)

Place the .idf file at: buildings/medium_office/RefBldgMediumOffice.idf
EOF
exit 1
