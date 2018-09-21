#!/usr/bin/env bash
# Creates python_lib.zip for the library

# Kill all .DS_Store and .pyc files and __pycache__ folders
echo Removing all unwanted files...
find . | grep -E "(__pycache__|\.DS_Store|\.pyc)" | xargs rm -rf

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
zip -r $file mitxgraders voluptuous

# Remove the license from the grading folder
rm ./mitxgraders/LICENSE

echo Done!
