#! /bin/bash
set -e
echo "Retrieving the latest version of the overlay debugger..."
cd ../aichallenge
git pull
cd ../ants
echo "Copying ants.py and CanvasElement.js..."
cp ../aichallenge/ants/ants.py tools/ants.py
cp ../aichallenge/ants/visualizer/js/CanvasElement.js tools/visualizer/js/CanvasElement.js 
