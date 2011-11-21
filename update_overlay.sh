#! /bin/bash
set -e
echo "Retrieving the latest version of the overlay debugger..."
cd ../aichallenge
git pull
cd ../ants
echo "Copying ants.py..."
cp ../aichallenge/ants/ants.py tools/ants.py
echo "Removing standard visualizer..."
rm -r -d tools/visualizer
echo "Copying enhanced visualizer files..."
mkdir tools/visualizer
cp -r ../aichallenge/ants/visualizer/* tools/visualizer/
echo "Done!"
