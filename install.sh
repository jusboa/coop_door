mpr -v rmd --rf /
mpr -v mkdir coop_door
mpr -v put coop_door/*.py coop_door/
mpr -v put __init__.py main.py /
mpr -v mip install logging
mpr -v reset
