"""
Rule-based HVAC setpoint controller — the baseline every other strategy
(MPC, RL) needs to beat.

Two implementation paths, pick based on how much control granularity you need:

1. STATIC SCHEDULE (implemented here): generate EnergyPlus Schedule:Compact
   objects and inject them into the IDF before simulation. Fixed
   occupied/unoccupied setpoints — this is what most real commercial
   buildings actually run, so it's the fair baseline.

2. DYNAMIC / REACTIVE (stub below): use EnergyPlus EMS (Energy Management
   System) actuators to adjust setpoints in response to conditions (e.g.
   outdoor temp, occupancy sensor, time-of-use price signal). More
   representative of "smart" rule-based control, still not learned.

Both are deterministic and cheap to evaluate — always run these first
before touching RL, so you have a real baseline number.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from eppy.modeleditor import IDF


@dataclass
class SetpointSchedule:
    """Simple occupied/unoccupied deadband schedule."""
    occupied_heating_c: float = 21.0
    occupied_cooling_c: float = 24.0
    unoccupied_heating_setback_c: float = 16.0
    unoccupied_cooling_setback_c: float = 30.0
    occupied_start_hour: int = 7
    occupied_end_hour: int = 19
    weekday_only: bool = True


def _compact_schedule_fields(name: str, sched: SetpointSchedule, heating: bool) -> list[str]:
    """Build the field list for an EnergyPlus Schedule:Compact object."""
    setpoint = sched.occupied_heating_c if heating else sched.occupied_cooling_c
    setback = sched.unoccupied_heating_setback_c if heating else sched.unoccupied_cooling_setback_c

    fields = [
        name,
        "Temperature",
        "Through: 12/31",
    ]
    if sched.weekday_only:
        fields += ["For: Weekdays"]
        fields += [
            f"Until: {sched.occupied_start_hour:02d}:00", f"{setback}",
            f"Until: {sched.occupied_end_hour:02d}:00", f"{setpoint}",
            "Until: 24:00", f"{setback}",
            "For: Weekends Holidays AllOtherDays",
            "Until: 24:00", f"{setback}",
        ]
    else:
        fields += ["For: AllDays"]
        fields += [
            f"Until: {sched.occupied_start_hour:02d}:00", f"{setback}",
            f"Until: {sched.occupied_end_hour:02d}:00", f"{setpoint}",
            "Until: 24:00", f"{setback}",
        ]
    return fields


def apply_rule_based_schedule(
    idf: IDF,
    sched: SetpointSchedule = SetpointSchedule(),
    heating_sched_name: str = "RuleBased_HtgSetp",
    cooling_sched_name: str = "RuleBased_ClgSetp",
) -> IDF:
    """
    Inject/overwrite heating & cooling setpoint schedules on the given eppy
    IDF object, then point every ThermostatSetpoint:DualSetpoint at them.

    Call this BEFORE saving/simulating the IDF. Does not run the simulation.
    """
    # Remove any existing schedule objects with these names to avoid duplicates
    for obj_type in ("Schedule:Compact",):
        for obj in list(idf.idfobjects[obj_type]):
            if obj.Name in (heating_sched_name, cooling_sched_name):
                idf.removeidfobject(obj)

    htg_fields = _compact_schedule_fields(heating_sched_name, sched, heating=True)
    clg_fields = _compact_schedule_fields(cooling_sched_name, sched, heating=False)

    idf.newidfobject("SCHEDULE:COMPACT", *_to_field_kwargs(htg_fields))
    idf.newidfobject("SCHEDULE:COMPACT", *_to_field_kwargs(clg_fields))

    # Point every dual-setpoint thermostat at our new schedules
    for tstat in idf.idfobjects.get("THERMOSTATSETPOINT:DUALSETPOINT", []):
        tstat.Heating_Setpoint_Temperature_Schedule_Name = heating_sched_name
        tstat.Cooling_Setpoint_Temperature_Schedule_Name = cooling_sched_name

    return idf


def _to_field_kwargs(fields: list[str]):
    # eppy's newidfobject takes positional field values after the object type;
    # this passes them through as-is. Kept as a separate function so the field
    # construction logic above stays readable.
    return fields


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply rule-based HVAC schedule to an IDF")
    parser.add_argument("--idf", required=True, help="Path to input IDF")
    parser.add_argument("--idd", required=True, help="Path to Energy+.idd (ships with EnergyPlus)")
    parser.add_argument("--out", required=True, help="Path to write modified IDF")
    args = parser.parse_args()

    IDF.setiddname(args.idd)
    idf = IDF(args.idf)
    apply_rule_based_schedule(idf)
    idf.saveas(args.out)
    print(f"Wrote rule-based-controlled IDF to {args.out}")
