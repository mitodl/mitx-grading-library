#!/usr/bin/env bash
# Ensure that script is run in the correct directory
SCRIPT_PATH=${0%/*}
if [ "$0" != "$SCRIPT_PATH" ] && [ "$SCRIPT_PATH" != "" ]; then
    cd $SCRIPT_PATH
fi

# Make docs
echo Making docs...
mkdocs gh-deploy

# Make zip file
echo Making zip file...
./makezip.sh

# Update course - no longer works, because edX changed their login process
#echo Updating course...
#cd course
#./upload.sh
#cd ..

# Done!
echo Done!
