"""
Parses EnergyPlus output across (controller, weather) runs and computes
comparable energy KPIs: total energy use intensity, peak demand, heating vs
cooling split, comfort violations.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def compute_kpis(df: pd.DataFrame, building_area_m2: float) -> pd.DataFrame:
    """
    Given a combined timeseries dataframe (columns from eplusout.csv, plus a
    'scenario' column added by simulation_runner.combine_results), compute
    per-scenario annual KPIs.

    Expects columns matching the `output_variables` in
    config/weather_scenarios.yaml — adjust column name matching below if you
    change the requested output variables (EnergyPlus's CSV headers include
    the full variable name + units + key, e.g.
    "Zone Ideal Loads Supply Air Total Heating Energy [J](Hourly)").
    """
    kpi_rows = []
    for scenario, g in df.groupby("scenario"):
        heating_col = _find_col(g, "Heating Energy")
        cooling_col = _find_col(g, "Cooling Energy")
        elec_demand_col = _find_col(g, "Electricity Demand Rate")

        heating_kwh = g[heating_col].sum() / 3.6e6 if heating_col else None  # J -> kWh
        cooling_kwh = g[cooling_col].sum() / 3.6e6 if cooling_col else None
        peak_demand_kw = g[elec_demand_col].max() / 1000 if elec_demand_col else None

        total_kwh = (heating_kwh or 0) + (cooling_kwh or 0)
        eui = total_kwh / building_area_m2 if building_area_m2 else None

        kpi_rows.append({
            "scenario": scenario,
            "heating_kwh": heating_kwh,
            "cooling_kwh": cooling_kwh,
            "total_hvac_kwh": total_kwh,
            "eui_kwh_per_m2": eui,
            "peak_electric_demand_kw": peak_demand_kw,
        })

    return pd.DataFrame(kpi_rows).sort_values("scenario").reset_index(drop=True)


def _find_col(df: pd.DataFrame, substring: str) -> str | None:
    matches = [c for c in df.columns if substring.lower() in c.lower()]
    return matches[0] if matches else None


def plot_energy_by_scenario(kpis: pd.DataFrame, out_path: str | Path):
    fig, ax = plt.subplots(figsize=(8, 5))
    kpis.plot(x="scenario", y=["heating_kwh", "cooling_kwh"], kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("Energy (kWh/year)")
    ax.set_title("HVAC Energy Demand by Weather Scenario")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def compare_controllers(kpi_frames: dict[str, pd.DataFrame], out_path: str | Path):
    """
    kpi_frames: {controller_name: kpis_dataframe}, each indexed the same way
    (one row per weather scenario). Produces a grouped bar chart comparing
    total energy across controllers per scenario.
    """
    combined = []
    for controller, kpis in kpi_frames.items():
        k = kpis.copy()
        k["controller"] = controller
        combined.append(k)
    combined_df = pd.concat(combined, ignore_index=True)

    pivot = combined_df.pivot(index="scenario", columns="controller", values="total_hvac_kwh")
    fig, ax = plt.subplots(figsize=(9, 5))
    pivot.plot(kind="bar", ax=ax)
    ax.set_ylabel("Total HVAC Energy (kWh/year)")
    ax.set_title("Controller Comparison Across Weather Scenarios")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)

    return combined_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze EnergyPlus batch run results")
    parser.add_argument("--results-dir", required=True, help="Directory of per-scenario results/ subfolders")
    parser.add_argument("--building-area-m2", type=float, default=4982.0, help="DOE Medium Office ~4982 m2")
    parser.add_argument("--out-dir", default="results/analysis")
    args = parser.parse_args()

    from src.simulation_runner import combine_results, run_batch, load_scenarios, SimulationResult

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    # Rebuild SimulationResult objects from existing output dirs (assumes
    # run_experiment.py already populated results/<scenario>/eplusout.csv)
    results_root = Path(args.results_dir)
    frames = []
    for scenario_dir in sorted(results_root.iterdir()):
        csv_path = scenario_dir / "eplusout.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df["scenario"] = scenario_dir.name
            frames.append(df)

    if not frames:
        raise SystemExit(f"No eplusout.csv found under {results_root} — run scripts/run_experiment.py first.")

    combined = pd.concat(frames, ignore_index=True)
    kpis = compute_kpis(combined, args.building_area_m2)
    print(kpis.to_string(index=False))
    kpis.to_csv(Path(args.out_dir) / "kpis.csv", index=False)
    plot_energy_by_scenario(kpis, Path(args.out_dir) / "energy_by_scenario.png")
    print(f"\nSaved KPIs and plot to {args.out_dir}/")
