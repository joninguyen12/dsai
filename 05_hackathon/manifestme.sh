#!/bin/bash
# manifestme.sh

# Write a manifest.json file for the Shiny dashboard
# (Shiny for Python app) for deploying to Posit Connect.

# Install / upgrade rsconnect package for Python
pip install --upgrade rsconnect-python

# From the 05_hackathon folder, write (or overwrite) a manifest.json file
# for the Shiny app in this directory. rsconnect will detect app.py.
rsconnect write-manifest shiny . --overwrite
