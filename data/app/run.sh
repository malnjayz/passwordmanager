#!/bin/bash
cd /app
export FLASK_APP=app.py
flask run --host=0.0.0.0
