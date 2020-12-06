#!/bin/bash
EXEC=GraphPreprocessor
# echo pyinstaller -F Preprocessing.py --onefile -n GraphPreprocessor.exe --hidden-import NETLIST:VLIB:SDF:util
pyinstaller -F Preprocessing.py --onefile -n ${EXEC} --hidden-import NETLIST:VLIB:SDF:util
mv ./dist/${EXEC} ./
rm -rf ./dist ./build ${EXEC}.spec ./__pycache__