#!/usr/bin/env python3
"""Run Rocket Chip's canonical SCCodeTable generator."""
import pathlib, runpy
runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1] /
                  'generators/rocket-chip/scripts/gen-ssa-rom.py'), run_name='__main__')
