# coop_door

Chicken coop door that opens and closes based on daylight. A photoresistor detects daylight and a DC motor operates the door. The software runs on a battery-powered Raspberry Pi Pico using MicroPython.

## Host development

Install [uv](https://docs.astral.sh/uv/), then set up the test and lint tools:

```sh
uv sync --locked --no-default-groups --group test --group lint
uv run --locked --group test pytest
uv run --locked --group lint flake8 . --exclude=.env,.venv --count --select=E9,F63,F7,F82 --show-source --statistics
uv run --locked --group lint flake8 . --exclude=.env,.venv --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
uv run --locked --group lint pylint $(git ls-files '[^tests]*.py')
```

## Deploy

Connect the Pico, then run the deployment script from the repository root:

```sh
uv run --locked --no-default-groups --group deploy bash install.sh
```

The script uses `mpremote` from the deployment dependency group to copy the MicroPython files and install the device-side `logging` module with MIP. `mip` is run on the device; it is not a host dependency.

The project intentionally uses uv's non-package mode: the MicroPython application is copied to the device, not installed as a host Python package.

Regenerate and commit `uv.lock` after dependency or metadata changes with `uv lock`.
