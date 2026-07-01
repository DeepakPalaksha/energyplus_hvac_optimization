"""
RL-based HVAC controller, built on Sinergym (Gymnasium-compatible EnergyPlus
environments: https://github.com/ugr-sail/sinergym).

Why Sinergym instead of hand-rolling the EnergyPlus<->Python bridge:
- It already handles the EnergyPlus co-simulation loop (via the EnergyPlus
  Python API / pyenergyplus), timestep synchronization, and observation/
  action space definition.
- It ships several DOE-derived building templates with configurable weather
  variability, which is exactly what "different weather patterns" needs.
- Reward functions (comfort + energy) are already implemented and tunable.

This module is a thin wrapper: build the env, train, and evaluate against
the rule-based baseline on the same weather scenarios.

NOT runnable in a sandbox without EnergyPlus + Sinergym installed. Run locally.
"""
from __future__ import annotations

from pathlib import Path

import gymnasium as gym
from stable_baselines3 import SAC
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import EvalCallback


def build_env(env_id: str = "Eplus-5zone-mixed-continuous-v1", weather_file: str | None = None):
    """
    Build a Sinergym environment.

    Sinergym env IDs follow the pattern Eplus-<building>-<weather-type>-<action-space>-v1.
    See https://ugr-sail.github.io/sinergym/ for the current registry — building
    options include several office-like configs; swap in the DOE Medium Office
    IDF via the `building_file` kwarg on `gym.make` if you want the exact same
    building as the rule-based baseline (requires registering a custom Sinergym
    config pointing at buildings/medium_office/RefBldgMediumOffice.idf).
    """
    kwargs = {}
    if weather_file:
        kwargs["weather_files"] = [weather_file]
    env = gym.make(env_id, **kwargs)
    return env


def train_sac(
    env,
    total_timesteps: int = 200_000,
    log_dir: str = "runs/sac_hvac",
    eval_env=None,
) -> SAC:
    """Train a SAC agent. SAC over PPO because HVAC control is continuous-action
    and benefits from off-policy sample efficiency — EnergyPlus co-sim steps
    are slow (real wall-clock time per episode), so sample efficiency matters."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    monitored_env = Monitor(env, log_dir)

    model = SAC(
        "MlpPolicy",
        monitored_env,
        verbose=1,
        tensorboard_log=log_dir,
        learning_rate=3e-4,
        buffer_size=100_000,
        batch_size=256,
    )

    callbacks = []
    if eval_env is not None:
        callbacks.append(
            EvalCallback(
                eval_env,
                best_model_save_path=log_dir,
                log_path=log_dir,
                eval_freq=10_000,
                deterministic=True,
            )
        )

    model.learn(total_timesteps=total_timesteps, callback=callbacks or None)
    model.save(f"{log_dir}/final_model")
    return model


def evaluate(model: SAC, env, n_episodes: int = 1) -> dict:
    """Run the trained policy and collect energy/comfort metrics."""
    results = {"episode_rewards": [], "total_energy_kwh": [], "comfort_violations": []}

    for _ in range(n_episodes):
        obs, info = env.reset()
        done = truncated = False
        episode_reward = 0.0
        while not (done or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = env.step(action)
            episode_reward += reward
        results["episode_rewards"].append(episode_reward)
        # Sinergym's info dict typically carries cumulative energy/comfort —
        # field names vary by version, check `info.keys()` and adjust.
        results["total_energy_kwh"].append(info.get("total_power_demand", None))
        results["comfort_violations"].append(info.get("comfort_violation_time", None))

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train an RL HVAC controller")
    parser.add_argument("--env-id", default="Eplus-5zone-mixed-continuous-v1")
    parser.add_argument("--weather", default=None, help="Path to .epw to override default weather")
    parser.add_argument("--timesteps", type=int, default=200_000)
    parser.add_argument("--log-dir", default="runs/sac_hvac")
    args = parser.parse_args()

    env = build_env(args.env_id, args.weather)
    model = train_sac(env, total_timesteps=args.timesteps, log_dir=args.log_dir)
    print(f"Training complete. Model saved to {args.log_dir}/final_model")
