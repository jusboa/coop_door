uv run --locked --no-default-groups --group deploy -- mpremote fs mkdir :coop_door
# Expand the source glob in the local shell before invoking mpremote.
uv run --locked --no-default-groups --group deploy -- mpremote fs cp coop_door/*.py :coop_door/
uv run --locked --no-default-groups --group deploy -- mpremote fs cp __init__.py main.py :/
uv run --locked --no-default-groups --group deploy -- mpremote mip install logging
uv run --locked --no-default-groups --group deploy -- mpremote soft-reset
