import os
import pprint

from google.appengine.api import memcache
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext import blobstore

from app.models import UserFile, UserFilePart

query = UserFilePart.query(UserFilePart.file_name == 'full_anna_fc2_report.pdf').order(UserFilePart.part_num)
#pprint.pprint(query.get())
#pprint.pprint(query.get())
for i, ufp in enumerate(query.iter()):
    print(ufp.part_num, i)
    blob_reader = blobstore.BlobReader(ufp.blob_key, buffer_size=1048576)
    while True:
        data = blob_reader.read(1048576)
        print(data)
        if data == '':
            print('end of part', i)
