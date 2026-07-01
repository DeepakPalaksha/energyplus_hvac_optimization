# Why there's no custom `energyplus_env.py` here

I considered hand-rolling a Gymnasium wrapper around the EnergyPlus Python API
(`pyenergyplus`) for the RL controller, but that duplicates a lot of fiddly,
already-solved plumbing: co-simulation callback timing, warmup-period handling,
observation/action space definition, reward shaping for comfort vs energy.

**Use [Sinergym](https://github.com/ugr-sail/sinergym) instead** — it's a
maintained, published (IEEE) Gymnasium wrapper purpose-built for this exact
problem (EnergyPlus + RL for building control). `src/controllers/rl_agent.py`
uses it directly via `gym.make("Eplus-...")`.

If you outgrow Sinergym's building templates and need the DOE Medium Office
exactly as used in the rule-based baseline, look at Sinergym's
`DEFAULT_5ZONE_CONFIG` / custom building registration docs — you can point it
at `buildings/medium_office/RefBldgMediumOffice.idf` directly rather than
using one of its bundled templates. That's the next real piece of work if you
want an apples-to-apples RL vs rule-based comparison on the identical
building geometry.
