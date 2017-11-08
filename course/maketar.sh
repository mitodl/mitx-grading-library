find . -name '*.DS_Store' -type f -delete
rm course.tar.gz
tar -cLzf course.tar.gz *
echo "Done"
