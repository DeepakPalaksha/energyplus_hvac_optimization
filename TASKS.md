# Build Sequence

## Phase 1 — Baseline simulation (get one honest EnergyPlus run working)
- [ ] Download DOE Medium Office IDF (`buildings/medium_office/download_building.sh`)
- [ ] Download EPW weather files for target scenarios (`weather/download_weather.sh`)
- [ ] Confirm IDF version matches installed EnergyPlus version (`IDVConverter` if not —
      DOE files from ~2010-2013 are IDF v7.2/8.x, need upgrading to your installed version)
- [ ] Run single simulation manually: `energyplus -w weather/stockholm.epw -d results/test buildings/medium_office/RefBldgMediumOfficeNew2004.idf`
- [ ] Sanity-check output: annual heating/cooling energy should be in a plausible range
      (~80-150 kWh/m²/yr for a non-Nordic-optimized envelope in Nordic climate)

## Phase 2 — Adapt envelope for Nordic context (optional but recommended)
- [ ] Adjust wall/roof/window U-values to Swedish BBR or Norwegian TEK17 minimums
      via `eppy` script (`src/adapt_envelope.py` — not yet created)
- [ ] Re-run and compare energy demand vs unmodified DOE envelope

## Phase 3 — Batch runner across weather scenarios
- [ ] `src/simulation_runner.py` — loop over weather files, run each, collect output
- [ ] Parse `.csv`/`.eso` output into a unified dataframe (energy by end-use, by timestep)

## Phase 4 — Rule-based HVAC controller (the baseline to beat)
- [ ] `src/controllers/rule_based.py` — implement setpoint schedule
      (e.g. occupied 21-24°C, unoccupied setback 16-30°C, or an ASHRAE-style
      economizer + deadband strategy)
- [ ] Inject via EnergyPlus `Schedule:Compact` objects or Energy Management System (EMS)
      actuators for finer control

## Phase 5 — RL / MPC controller
- [ ] Wrap the building+weather combo as a Gymnasium env (`src/env/energyplus_env.py`),
      ideally via Sinergym rather than hand-rolling the EnergyPlus-Python bridge
- [ ] Train SAC or PPO agent (`src/controllers/rl_agent.py`) with reward = 
      -(energy_cost + comfort_penalty)
- [ ] (Stretch) MPC controller using a linear/RC thermal model identified from
      EnergyPlus data, solved via `cvxpy` or `pyomo`

## Phase 6 — Analysis & comparison
- [ ] `src/analysis/analyze_results.py` — energy KPIs, peak demand, comfort violations,
      per-weather-scenario breakdown
- [ ] Plots: load duration curves, energy by weather scenario, controller comparison bar chart
- [ ] Write up findings in `RESULTS.md`
