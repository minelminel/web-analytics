#!/usr/bin/env bash

python3 -c "from app import startup; startup()"
python3 -m flask run --host=0.0.0.0
