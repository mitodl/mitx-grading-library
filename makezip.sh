#!/bin/bash
# Creates python_lib.zip for the library
# Note that it includes all .pyc files, which make the library load faster

# Begin by ensuring that all pyc files are up-to-date
echo Updating .pyc files...
python basic_demo.py > /dev/null

# Kill all .DS_Store files and __pycache__ folders
echo Removing all .DS_Store and __pycache__ files...
find . | grep -E "(__pycache__|\.DS_Store)" | xargs rm -rf

# Remove the old python_lib.zip
file="python_lib.zip"
if [ -f $file ] ; then
    echo Removing old python_lib.zip...
    rm $file
fi

# Copy the license into the grading folder
cp LICENSE ./mitxgraders/LICENSE

# Create the zip file
echo Building python_lib.zip...
zip -r $file mitxgraders

# Remove the license from the grading folder
rm ./mitxgraders/LICENSE

echo Done!
