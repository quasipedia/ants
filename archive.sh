#! /bin/bash
set -e
if [ ! $1 ]
	then
		echo "You must specify the archive name of the bot."
		exit 1
fi
TARGET=old_bots/$1
mkdir $TARGET
cp *.py $TARGET
