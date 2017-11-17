#!/bin/bash
v4l2-ctl -c focus_auto=0
v4l2-ctl -c focus_absolute=20
amixer cset numid=3 1
amixer sset PCM,0 100%
export DISPLAY=:0
python3 main.py
