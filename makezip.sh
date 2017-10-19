#!/bin/bash
# Creates python_lib.zip for the library
# Note that it includes all .pyc files, which make the library load faster

# Begin by ensuring that all pyc files are up-to-date
echo Updating .pyc files...
python basic_demo.py > /dev/null

# Kill all .DS_Store files
echo Removing all .DS_Store files...
find . -name '.DS_Store' -type f -delete

# Remove the old python_lib.zip
file="python_lib.zip"
if [ -f $file ] ; then
    echo Removing old python_lib.zip...
    rm $file
fi

# Create the zip file
echo Building python_lib.zip...
zip -r $file graders

echo Done!
