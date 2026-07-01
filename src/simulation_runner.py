"""
Batch-runs EnergyPlus across (building, weather) pairs and collects results.

Requires EnergyPlus installed and on PATH. This module shells out to the
`energyplus` CLI rather than using the EnergyPlus Python API directly, so it
works with any EnergyPlus 9.x+ installation without version-specific bindings.
"""
from __future__ import annotations

import subprocess
import shutil
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


@dataclass
class WeatherScenario:
    name: str
    epw_path: Path
    label: str = ""
    climate_zone: str = ""


@dataclass
class SimulationResult:
    scenario: WeatherScenario
    output_dir: Path
    success: bool
    stdout: str
    stderr: str

    def load_timeseries(self) -> pd.DataFrame:
        """Load the variable timeseries CSV EnergyPlus writes (eplusout.csv)."""
        csv_path = self.output_dir / "eplusout.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"No eplusout.csv in {self.output_dir} — did the run fail? "
                f"Check {self.output_dir / 'eplusout.err'}"
            )
        df = pd.read_csv(csv_path)
        df["scenario"] = self.scenario.name
        return df


def check_energyplus_available() -> str:
    """Raise a clear error early if EnergyPlus isn't on PATH."""
    exe = shutil.which("energyplus")
    if exe is None:
        raise RuntimeError(
            "EnergyPlus not found on PATH. Install it from "
            "https://energyplus.net/downloads and ensure `energyplus` is callable, "
            "or set the full path via the `energyplus_binary` argument."
        )
    return exe


def load_scenarios(config_path: str | Path) -> list[WeatherScenario]:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    root = Path(config_path).parent.parent  # config/ -> repo root
    scenarios = []
    for s in cfg["scenarios"]:
        scenarios.append(
            WeatherScenario(
                name=s["name"],
                epw_path=root / s["file"],
                label=s.get("label", s["name"]),
                climate_zone=s.get("climate_zone", ""),
            )
        )
    return scenarios


def run_single_simulation(
    idf_path: str | Path,
    scenario: WeatherScenario,
    output_root: str | Path = "results",
    energyplus_binary: str | None = None,
) -> SimulationResult:
    """Run one EnergyPlus simulation for a given (IDF, weather) pair."""
    idf_path = Path(idf_path)
    exe = energyplus_binary or check_energyplus_available()

    if not scenario.epw_path.exists():
        raise FileNotFoundError(
            f"Weather file not found: {scenario.epw_path}. "
            f"Run weather/download_weather.sh or place the .epw manually."
        )
    if not idf_path.exists():
        raise FileNotFoundError(
            f"Building IDF not found: {idf_path}. "
            f"Run buildings/medium_office/download_building.sh first."
        )

    out_dir = Path(output_root) / scenario.name
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        exe,
        "-w", str(scenario.epw_path),
        "-d", str(out_dir),
        "-r",  # readvars — produces eplusout.csv
        str(idf_path),
    ]
    logger.info("Running: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)

    return SimulationResult(
        scenario=scenario,
        output_dir=out_dir,
        success=proc.returncode == 0,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def run_batch(
    idf_path: str | Path,
    scenarios: list[WeatherScenario],
    output_root: str | Path = "results",
) -> list[SimulationResult]:
    """Run the same building across every weather scenario."""
    results = []
    for scenario in scenarios:
        logger.info("=== Simulating %s (%s) ===", scenario.name, scenario.label)
        try:
            result = run_single_simulation(idf_path, scenario, output_root)
            status = "OK" if result.success else "FAILED"
            logger.info("  %s", status)
            if not result.success:
                logger.error(result.stderr[-2000:])
        except FileNotFoundError as e:
            logger.error("  SKIPPED: %s", e)
            continue
        results.append(result)
    return results


def combine_results(results: list[SimulationResult]) -> pd.DataFrame:
    """Combine timeseries from all successful runs into one long dataframe."""
    frames = []
    for r in results:
        if not r.success:
            continue
        try:
            frames.append(r.load_timeseries())
        except FileNotFoundError as e:
            logger.warning(str(e))
    if not frames:
        raise RuntimeError("No successful simulations produced output to combine.")
    return pd.concat(frames, ignore_index=True)
