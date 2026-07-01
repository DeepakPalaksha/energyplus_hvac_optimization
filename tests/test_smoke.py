"""
Smoke tests that don't require EnergyPlus to be installed — verify config
loading, controller logic, and analysis functions work on synthetic data.
Run the real integration tests (actual EnergyPlus simulation) manually once
you have EnergyPlus installed: see TASKS.md Phase 1.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.simulation_runner import load_scenarios, WeatherScenario
from src.controllers.rule_based import SetpointSchedule, _compact_schedule_fields
from src.analysis.analyze_results import compute_kpis, _find_col


def test_load_scenarios(tmp_path):
    config = tmp_path / "config" / "weather_scenarios.yaml"
    config.parent.mkdir()
    config.write_text("""
scenarios:
  - name: test_city
    file: weather/test.epw
    label: "Test City"
    climate_zone: "Test Zone"
building:
  idf: buildings/medium_office/test.idf
""")
    scenarios = load_scenarios(config)
    assert len(scenarios) == 1
    assert scenarios[0].name == "test_city"
    assert isinstance(scenarios[0], WeatherScenario)


def test_setpoint_schedule_fields():
    sched = SetpointSchedule(occupied_heating_c=21.0, unoccupied_heating_setback_c=16.0)
    fields = _compact_schedule_fields("TestHtg", sched, heating=True)
    assert fields[0] == "TestHtg"
    assert "21.0" in fields
    assert "16.0" in fields


def test_compute_kpis_basic():
    df = pd.DataFrame({
        "scenario": ["stockholm"] * 3,
        "Zone Ideal Loads Supply Air Total Heating Energy [J](Hourly)": [3.6e6, 7.2e6, 0],
        "Zone Ideal Loads Supply Air Total Cooling Energy [J](Hourly)": [0, 0, 3.6e6],
        "Facility Total HVAC Electricity Demand Rate [W](Hourly)": [1000, 2000, 1500],
    })
    kpis = compute_kpis(df, building_area_m2=1000.0)
    assert len(kpis) == 1
    row = kpis.iloc[0]
    assert row["heating_kwh"] == pytest.approx(3.0)  # (3.6+7.2) MJ -> kWh
    assert row["cooling_kwh"] == pytest.approx(1.0)
    assert row["peak_electric_demand_kw"] == pytest.approx(2.0)
    assert row["eui_kwh_per_m2"] == pytest.approx(4.0 / 1000)


def test_find_col():
    df = pd.DataFrame({"Zone Ideal Loads Supply Air Total Heating Energy [J](Hourly)": [1]})
    assert _find_col(df, "Heating Energy") is not None
    assert _find_col(df, "Nonexistent") is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
