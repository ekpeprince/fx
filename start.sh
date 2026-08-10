#!/bin/bash
echo "Starting ICT Autonomous Trading Suite..."

# Start the supervisor in the background
python supervisor.py &

# Start the streamlit dashboard in the foreground
python -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
