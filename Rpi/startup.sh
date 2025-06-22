#!/bin/bash
#please run with "sudo -E -u $USER ./startup.sh"

cd /home/pi/Desktop/MidProject
source .venv/bin/activate
export PYTHONPATH=.

for i in {1..300}; do
    if ping -c 1 8.8.8.8 &>/dev/null; then
        echo "Network connected successfully!"
        break
    else
        echo "Waiting for network connection..."
        sleep 1
    fi
done

python3 ./src/main.py
