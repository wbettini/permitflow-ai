#!/bin/bash
# For breakpoints, live reload, and step‑through debugging in Codespaces

clear
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000