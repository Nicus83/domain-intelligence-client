#!/bin/sh
# Read-only demonstration. No signature or payment is created.
set -eu
curl -fsS --max-time 20 https://api.x4-02.fr/health
printf '\n'
python3 client.py --domain example.com
# To perform a separate, explicitly authorized TESTNET payment after setup:
# python client.py --domain example.com --pay
