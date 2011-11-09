#! /bin/bash
set -e
cd ../aichallenge
git pull
cd ../ants
cp ../aichallenge/ants/ants.py tools/ants.py
cp ../aichallenge/ants/visualizer/js/CanvasElement.js tools/visualizer/js/CanvasElement.js 
