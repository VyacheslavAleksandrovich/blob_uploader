import os

from app.aux import send_download_url_gs, get_download_url
from google.appengine.ext import blobstore
from google.appengine.api import app_identity, memcache
import cloudstorage as gcs
import webapp2

from app.models import UserFilePart


import logging

logger = logging.getLogger('merger')
#logger.setLevel(logging.WARNING)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


class MergeFile(webapp2.RequestHandler):
    def post(self):
        logger.debug("merge begin")
        import time
        time.sleep(3)
        file_name = self.request.get('file_name')
        number_batches = int(self.request.get('number_batches'))
        task_id = self.request.get('task_id')
        buffer_size = 1048576
        bucket_name = os.environ.get('BUCKET_NAME',
                                     app_identity.get_default_gcs_bucket_name())
        write_retry_params = gcs.RetryParams(backoff_factor=1.1)
        file_name = '/' + bucket_name + '/' + file_name
        gcs_file = gcs.open(file_name,
                      'w',
                      options={'x-goog-acl': 'public-read'},
                      retry_params=write_retry_params)
        parts = list(UserFilePart.query(UserFilePart.task_id == task_id).order(UserFilePart.part_num).iter())
        if len(parts) != number_batches:
            logger.error("number parts not eq.")
        for i, ufp in enumerate(parts):
            blob_reader = blobstore.BlobReader(ufp.blob_key, buffer_size=buffer_size)
            while True:
                data = blob_reader.read(1048576)
                gcs_file.write(data)
                if data == '':
                    break
        gcs_file.close()
        #https://storage.googleapis.com/blob-uploader2.appspot.com/tags
        memcache.set(key=task_id, value=True)
        email_addr = memcache.get(key=(task_id + '_mail'))
        blobstore_filename = '/gs{}'.format(file_name)
        blob_key = blobstore.create_gs_key(blobstore_filename)
        #memcache.set(key=task_id+'_url', value=get_download_url(blob_key))
        memcache.set(key=task_id+'_url', value='https://storage.googleapis.com{}'.format(file_name))
        send_download_url_gs(email_addr, 'https://storage.googleapis.com{}'.format(file_name))

application = webapp2.WSGIApplication([
    ('/merge_start', MergeFile)
], debug=True)
