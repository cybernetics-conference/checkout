#!/bin/bash

# disable autofocus and set focus manually 
v4l2-ctl -c focus_auto=0
v4l2-ctl -c focus_absolute=20

# switch output to headphone jack
amixer cset numid=3 1 

# set volume to 100$
amixer sset PCM,0 100%

# set display
export DISPLAY=:0

python3 main.py
