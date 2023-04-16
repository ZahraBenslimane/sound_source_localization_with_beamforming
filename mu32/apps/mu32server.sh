#!/bin/bash

# le port usb n'est pas visible au reboot. Il faut brancher/débrancher le câble...
# no more used: command line is set in the systemctl service file

echo 'megamicro.sh script starting...'

export PYTHONPATH=$PYTHONPATH:/home/jetson/Mu32/src
cd /home/jetson/Mu32 && source venv/bin/activate && python src/mu32/apps/mu32server.py &
