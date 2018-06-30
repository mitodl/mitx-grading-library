find . -name '*.DS_Store' -type f -delete
if [ -f 'course.tar.gz' ]
then
  rm course.tar.gz
fi
tar -cLzhf course.tar.gz *
echo "Done"
