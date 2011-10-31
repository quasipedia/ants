#! /bin/bash
set -e
if [ ! $1 ]
	then
		echo "You must specify your opponent!"
		exit 1
fi
OPPONENT=old_bots/${1}/MyBot.py3
python tools/playgame.py "python3 MyBot.py3" \
                         "python3 ${OPPONENT}" \
                         --map_file tools/maps/random_walk/random_walk_03p_01.map \
                         --log_dir game_logs \
                         --turns 300 \
                         --verbose \
                         --log_stderr \
                         --turntime=5000 \
                         --fill
