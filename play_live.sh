#!/usr/bin/env sh
rm *.pyc
set -e
if [ ! $1 ]
        then
                echo "You must specify your opponent!"
                exit 1
fi
OPPONENT=old_bots/${1}/MyBot.py
cd tools
./playgame.py -So \
              "python ../MyBot.py" \
              "python ../${OPPONENT}" \
              --player_seed 42 \
              --end_wait=0.25 \
              --verbose \
              --log_dir game_logs \
              --turns 1000 \
              --map_file maps/maze/maze_02p_02.map \
              --log_stderr \
              --turntime=500 \
              --fill |
java -jar visualizer.jar
cd ..
