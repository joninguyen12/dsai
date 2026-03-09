#!/bin/bash
# manifestme.sh

# Write a manifest.json file for a Shiny Python app,
# for deploying to Posit Connect.

# Install rsconnect package for Python
pip install --upgrade rsconnect-python

# Write (or overwrite) a manifest.json file for the Shiny Python app in this folder.
# We point to the current directory (.) and use app:app as the entrypoint,
# which matches the Shiny Express app object defined in app.py.
rsconnect write-manifest shiny . --entrypoint app:app --overwrite
