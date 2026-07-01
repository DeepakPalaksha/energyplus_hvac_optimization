# EnergyPlus HVAC Optimization — Commercial Building

Simulate a DOE reference commercial building (Medium Office) in EnergyPlus across multiple
weather patterns, quantify its energy demand, and benchmark HVAC control strategies —
starting with rule-based setpoint scheduling, extending to MPC / RL controllers.

## Why this exists

Building HVAC typically accounts for 40-50% of commercial building energy use. This repo:

1. Runs the DOE Medium Office reference building through EnergyPlus under different
   weather scenarios (Nordic climates by default — Stockholm, Oslo — plus reference
   US climate zones for comparison).
2. Extracts and analyzes energy demand: heating/cooling loads, peak demand, load shape
   by season/weather.
3. Benchmarks HVAC control strategies against the EnergyPlus baseline:
   - Rule-based setpoint scheduling (baseline)
   - Model Predictive Control (MPC)
   - RL agent (SAC/PPO via Sinergym + stable-baselines3)
4. Compares energy consumption, comfort violations (PMV/temperature deadband), and
   peak demand reduction across strategies and weather scenarios.

## Architecture

```
buildings/medium_office/   DOE reference building IDF (download script, not committed)
weather/                   EPW weather files per scenario (download script, not committed)
config/                    Weather scenario list, HVAC setpoint schedules, run config
src/simulation_runner.py   Batch-runs EnergyPlus across (building, weather) pairs via eppy
src/controllers/           Rule-based baseline + RL agent wrapper
src/env/                   Gymnasium env wrapping EnergyPlus (via Sinergym)
src/analysis/              Parses .csv/.eso output, computes energy KPIs, plots
scripts/run_experiment.py  End-to-end: pick building + weather scenarios + controller, run, analyze
```

## Prerequisites (you run these locally, not in this environment)

- EnergyPlus ≥ 23.x installed and on `PATH` (https://energyplus.net/downloads)
- Python 3.10+
- `pip install -r requirements.txt`

## Quickstart

```bash
# 1. Get the building model
bash buildings/medium_office/download_building.sh

# 2. Get weather files for your scenarios
bash weather/download_weather.sh

# 3. Run baseline rule-based simulation across all weather scenarios
python scripts/run_experiment.py --controller rule_based --config config/weather_scenarios.yaml

# 4. Run RL agent (requires training first — see src/controllers/rl_agent.py)
python scripts/run_experiment.py --controller rl --config config/weather_scenarios.yaml

# 5. Analyze and compare
python -m src.analysis.analyze_results --results-dir results/
```

## Weather scenarios

Configured in `config/weather_scenarios.yaml`. Defaults to Nordic climates
(Stockholm, Oslo) plus 2 US DOE reference climate zones for cross-validation
against published DOE benchmark numbers.

## Building model

Uses the DOE Commercial Reference Building — Medium Office (ASHRAE 90.1,
post-1980 or new-construction vintage, selectable). Source: NREL
`OpenStudio-Prototype-Buildings` repo. ~4,982 m² / 3-story, VAV with reheat,
gas boiler + electric chiller — representative of a mid-size Nordic office too,
though envelope U-values will need adjusting for Nordic building codes (see
`buildings/medium_office/README.md`).

## Status

Scaffold stage — see TASKS.md for build sequence.
