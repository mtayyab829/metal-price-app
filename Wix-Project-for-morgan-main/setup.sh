#!/bin/bash
apt-get update
apt-get install -y wget chromium chromium-driver
pip install -r requirements.txt
