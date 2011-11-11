#! /bin/bash
set -e
if [ ! $1 ]
        then
                echo "You must specify how many games you would like to play"
                exit 1
fi
GAMES=${1}
python tcpclient.py ants.fluxid.pl 2081 "python MyBot.py" mac verysillypassword $GAMES
#python tcpclient.py 213.88.39.97 2080 "python MyBot.py" mac verysillypassword $GAMES
#python tcpclient.py 209.62.17.40 2081 "python MyBot.py" mac verysillypassword $GAMES
