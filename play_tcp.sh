#! /bin/bash
set -e
if [ ! $1 ]
        then
                echo "You must specify how many games you would like to play"
                exit 1
fi
GAMES=${1}
python tcpclient.py ants.fluxid.pl 2081 "python MyBot.py" mac verysillypassword $GAMES
