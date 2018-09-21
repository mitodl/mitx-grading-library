"""
uploader.py

Script to upload a tarball to an edX course.

Based on
https://github.com/mitodl/git2edx/blob/master/edxStudio.py
by Ike Chuang
"""
import os
import sys
import time
import requests
import argparse
import json

# Import username and password
from config import username, password

class edxStudio(object):

    def __init__(self, site):
        self.session = requests.session()
        self.site = site

    def login(self, username, password):
        url = '{}/signin'.format(self.site)
        self.session.get(url)
        csrf = self.session.cookies['csrftoken']
        url = '{}/login_post'.format(self.site)
        headers = {'X-CSRFToken': csrf, 'Referer': '{}/signin'.format(self.site)}
        r2 = self.session.post(url,
                               data={'email': username, 'password': password},
                               headers=headers)

        if not r2.status_code == 200:
            print("Login failed!")
            print(r2.content)
            sys.stdout.flush()
            sys.exit(-1)

    def do_upload(self, course_id, tar_file, nwait=20):

        filename = os.path.basename(tar_file)
        url = '{}/import/{}'.format(self.site, course_id)

        files = {'course-data': (filename, open(tar_file, 'rb'), 'application/x-gzip')}

        csrf = self.session.cookies['csrftoken']

        headers = {'X-CSRFToken': csrf,
                   'Referer': url,
                   'Accept': 'application/json, text/javascript, */*; q=0.01',
                   }

        print("Uploading to {}".format(url))

        try:
            r3 = self.session.post(url, files=files, headers=headers)
        except Exception as err:
            print("Error uploading file: {}".format(err))
            print("url={}, files={}, headers={}".format(url, files, headers))
            sys.stdout.flush()
            sys.exit(-1)

        print("File uploaded. Response: {}".format(r3.status_code))

        status = json.loads(r3.content.decode("utf-8"))["ImportStatus"]
        if status == 0:
            print("Status: 0: No status info found (import done or upload still in progress)")
        elif status == 1:
            print("Status: 1: Unpacking")
        elif status == 2:
            print("Status: 2: Verifying")
        elif status == 3:
            print("Status: 3: Updating")
        elif status == 4:
            print("Status: 4: Import successful")
            return
        else:
            print("Error in upload")
            print("Status: {}".format(status))

        url = '{}/import_status/{}/{}'.format(self.site, course_id, filename)
        print("File is being processed...")
        print("Status URL: {}".format(url))

        for k in range(nwait):
            r4 = self.session.get(url)
            # -X : Import unsuccessful due to some error with X as stage [0-3]
            # 0 : No status info found (import done or upload still in progress)
            # 1 : Unpacking
            # 2 : Verifying
            # 3 : Updating
            # 4 : Import successful
            status = json.loads(r4.content.decode("utf-8"))["ImportStatus"]
            if status == 0:
                print("Status: 0: No status info found (import done or upload still in progress)")
            elif status == 1:
                print("Status: 1: Unpacking")
            elif status == 2:
                print("Status: 2: Verifying")
            elif status == 3:
                print("Status: 3: Updating")
            elif status == 4:
                print("Status: 4: Import successful")
                return
            else:
                print("Error in upload")
                print("Status: {}".format(status))

            sys.stdout.flush()
            time.sleep(2)

# Deal with command line arguments
parser = argparse.ArgumentParser(description="Uploads tar.gz files to an edX instance using credentials in config.py")
parser.add_argument("site", help="URL of edX site (eg: https://studio.edge.edx.org)")
parser.add_argument("course_id", help="Course ID (eg: course-v1:MITx+8.04.1x+3T2018)")
parser.add_argument("tar_file", help="Name of .tar.gz file to upload")
args = parser.parse_args()

# Get things started
print("Uploading {}".format(args.tar_file))
print("to {}".format(args.site))
print("with course id {}".format(args.course_id))
es = edxStudio(args.site)

# Connect to studio
print("Connecting...")
sys.stdout.flush()
es.login(username, password)
print("Login successful")

# Do the upload
print("Uploading...")
es.do_upload(args.course_id, args.tar_file)
