uv run --locked --no-default-groups --group deploy -- mpr -v rmd --rf /
uv run --locked --no-default-groups --group deploy -- mpr -v mkdir coop_door
uv run --locked --no-default-groups --group deploy -- mpr -v put coop_door/*.py coop_door/
uv run --locked --no-default-groups --group deploy -- mpr -v put __init__.py main.py /
uv run --locked --no-default-groups --group deploy -- mpr -v mip install logging
uv run --locked --no-default-groups --group deploy -- mpr -v reset
