#!/bin/bash
amixer cset numid=3 1
amixer sset PCM,0 100%
export DISPLAY=:0
python3 main.py
