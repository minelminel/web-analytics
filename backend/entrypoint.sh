#!/usr/bin/env bash

python3 -c "from app import db; db.create_all()"
python3 -m flask run --host=0.0.0.0
