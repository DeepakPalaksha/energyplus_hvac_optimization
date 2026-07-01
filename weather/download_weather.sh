#!/usr/bin/env bash
# EPW weather files are NOT reliably available on GitHub — they live on
# energyplus.net/weather and climate.onebuilding.org, which most sandboxed/CI
# network policies (including the one this repo was scaffolded in) don't allowlist.
#
# Get them manually (one-time, ~1-2 MB each):
#
#   EnergyPlus official weather library:
#     https://energyplus.net/weather
#     -> Europe -> Sweden -> Stockholm (SWE_ST_Stockholm-Arlanda.AP.024600_TMYx)
#     -> Europe -> Norway  -> Oslo (NOR_OS_Oslo-Blindern.014920_TMYx)
#
#   Broader archive (more stations, historical + TMYx):
#     https://climate.onebuilding.org
#
# Place downloaded .epw files here as:
#   weather/stockholm.epw
#   weather/oslo.epw
#   weather/<scenario_name>.epw   (must match names in config/weather_scenarios.yaml)
#
# If you have network access to energyplus.net from your machine, this will work:

set -euo pipefail
cd "$(dirname "$0")"

declare -A STATIONS=(
  ["stockholm"]="https://energyplus-weather.s3.amazonaws.com/europe_wmo_region_6/SWE/SWE_Stockholm.024600_IWEC/SWE_Stockholm.024600_IWEC.epw"
  ["oslo"]="https://energyplus-weather.s3.amazonaws.com/europe_wmo_region_6/NOR/NOR_Oslo.014880_IWEC/NOR_Oslo.014880_IWEC.epw"
)

for name in "${!STATIONS[@]}"; do
  url="${STATIONS[$name]}"
  echo "Fetching ${name}.epw ..."
  if curl -fsSL "${url}" -o "${name}.epw"; then
    echo "  OK -> weather/${name}.epw"
  else
    echo "  FAILED — download manually from https://energyplus.net/weather and save as weather/${name}.epw"
  fi
done
