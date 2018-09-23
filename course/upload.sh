find . -name '*.DS_Store' -type f -delete
if [ -f 'course.tar.gz' ]
then
  rm course.tar.gz
fi
tar -cLzhf course.tar.gz *
echo "Tar file created. Beginning upload."
python uploader.py https://studio.edge.edx.org course-v1:MITx+grading-library+examples course.tar.gz
