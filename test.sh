#! /bin/bash
tools/playgame.py --engine_seed 42 \
				  --player_seed 42 \
				  --food none \
				  --end_wait=0.25 \
				  --verbose \
				  --log_dir game_logs \
				  --turns 30 \
				  --map_file tools/submission_test/test.map \
				  "./MyBot.py3" \
				  "python tools/submission_test/TestBot.py" \
				  --nolaunch \
				  --log_stderr \
				  --strict \
				  --capture_errors
