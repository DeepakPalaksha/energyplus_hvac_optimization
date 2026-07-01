#!/usr/bin/env python3
"""
End-to-end: pick a controller, run it across every configured weather
scenario, save results.

Usage:
    python scripts/run_experiment.py --controller rule_based
    python scripts/run_experiment.py --controller rule_based --scenarios stockholm oslo
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.simulation_runner import load_scenarios, run_batch, combine_results

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run HVAC controller experiment across weather scenarios")
    parser.add_argument("--controller", required=True, choices=["rule_based", "rl", "mpc"])
    parser.add_argument("--config", default="config/weather_scenarios.yaml")
    parser.add_argument("--scenarios", nargs="*", default=None, help="Subset of scenario names to run (default: all)")
    parser.add_argument("--output-root", default="results")
    args = parser.parse_args()

    scenarios = load_scenarios(args.config)
    if args.scenarios:
        scenarios = [s for s in scenarios if s.name in args.scenarios]
        if not scenarios:
            raise SystemExit(f"No matching scenarios found for {args.scenarios}")

    import yaml
    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    idf_path = Path(args.config).parent.parent / cfg["building"]["idf"]

    if args.controller == "rule_based":
        # Apply rule-based schedule to a working copy of the IDF before running.
        # (See src/controllers/rule_based.py for the eppy-based injection logic.)
        logger.info("Controller: rule-based setpoint schedule")
        # NOTE: for a first pass you can also just run the IDF as-is (DOE
        # prototype buildings ship with their own default HVAC schedules,
        # which is itself a reasonable baseline). Swap in apply_rule_based_schedule()
        # once you want to test your own setpoint strategy against theirs.
        run_idf = idf_path

    elif args.controller == "rl":
        raise NotImplementedError(
            "RL controller requires the Sinergym environment loop, not the "
            "batch subprocess runner used here — see src/controllers/rl_agent.py "
            "and run that module directly after training."
        )
    elif args.controller == "mpc":
        raise NotImplementedError("MPC controller not yet implemented — see TASKS.md Phase 5.")

    logger.info("Running %d scenario(s): %s", len(scenarios), [s.name for s in scenarios])
    results = run_batch(run_idf, scenarios, output_root=f"{args.output_root}/{args.controller}")

    n_ok = sum(r.success for r in results)
    logger.info("Completed: %d/%d simulations succeeded", n_ok, len(results))

    if n_ok:
        combined = combine_results(results)
        combined.to_csv(f"{args.output_root}/{args.controller}/combined_timeseries.csv", index=False)
        logger.info("Saved combined timeseries to %s/%s/combined_timeseries.csv", args.output_root, args.controller)


if __name__ == "__main__":
    main()
