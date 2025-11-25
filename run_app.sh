#!/bin/bash

# Unset PYTHONPATH to prevent system packages from interfering
unset PYTHONPATH

# Activate virtual environment
source venv/bin/activate

# Run Streamlit
streamlit run app.py
