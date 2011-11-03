#! /bin/bash
rm *.pyc
set -e
if [ ! $1 ]
	then
		echo "You must specify your opponent!"
		exit 1
fi
OPPONENT=old_bots/${1}/MyBot.py
python tools/playgame.py "python MyBot.py" \
                         "python ${OPPONENT}" \
                         --map_file tools/maps/random_walk/random_walk_03p_01.map \
                         --log_dir game_logs \
                         --turns 20 \
                         --verbose \
                         --log_stderr \
                         --turntime=5000 \
                         --fill
