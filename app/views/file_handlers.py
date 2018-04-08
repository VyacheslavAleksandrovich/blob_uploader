from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore
from google.appengine.api import taskqueue, memcache

import logging
import json
from base64 import decodestring
from urllib import unquote

from .base_handler import BaseHandler, user_required
from ..models import UserFile, UserFilePart
from ..aux import send_download_url_blobstore

logger = logging.getLogger('blob_app.file_handler')


class FileUploadHandler(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    @user_required
    def post(self):
        logger.debug('request %s', self.request)
        logger.debug('user_id %s', self.user.get_id())
        upload = self.get_uploads()[0]
        user_file = UserFile(
            user=self.user.get_id(),
            blob_key=upload.key())
        user_file.put()
        send_download_url_blobstore(self.user.email_address, str(upload.key()))
        self.redirect('/')


class FilePartUploadHandler(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    @user_required
    def post(self):
        logger.debug('request %s', self.request)
        logger.debug('user_id %s', self.user.get_id())
        upload = self.get_uploads()[0]
        part_num = int(self.request.get('part_num',0))
        file_name = self.request.get('file_name', 'no_name')
        task_id = self.request.get('task_id')
        user_file = UserFilePart(
            user=self.user.get_id(),
            blob_key=upload.key(),
            part_num=part_num,
            file_name=file_name,
            task_id=task_id)
        user_file.put()
        self.redirect('/')


class MergeFile(BaseHandler):
    @user_required
    def post(self):
        logger.debug('request %s', self.request)
        logger.debug('user_id %s', self.user.get_id())
        number_batches = self.request.get('number_batches')
        file_name = self.request.get('file_name')
        task_id = self.request.get('task_id')

        memcache.add(key=task_id, value=False, time=1200)
        to_ = self.user.email_address
        memcache.add(key=(task_id + '_mail'), value=to_, time=1200)
        logger.debug('mem cache add %s', 'mem')

        task = taskqueue.add(
            url='/merge_start',
            target='merger',
            params={
                'file_name': file_name,
                'number_batches': number_batches,
                'task_id': task_id
            })
        logger.debug('task add %s', task_id)
        self.redirect('/')


class UploadURL(BaseHandler):
    @user_required
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        upload_url = blobstore.create_upload_url('/upload_file_part')
        obj = {'UploadURL': upload_url}
        self.response.out.write(json.dumps(obj))


class DownloadURL(BaseHandler):
    @user_required
    def get(self, *args, **kwargs):
        self.response.headers['Content-Type'] = 'application/json'
        task_id = kwargs['task_id']
        download_url = memcache.get(task_id+'_url')
        obj = {'DownloadURL': download_url}
        self.response.out.write(json.dumps(obj))


class MergeIsDone(BaseHandler):
    @user_required
    def get(self, *args, **kwargs):
        task_id = kwargs['task_id']
        is_done = memcache.get(task_id)
        logger.debug('task id {} is done {}'.format(task_id, is_done))
        self.response.headers['Content-Type'] = 'application/json'
        if is_done:
            obj = {'isDone': True}
        else:
            obj = {'isDone': False}
        self.response.out.write(json.dumps(obj))


class FileDownloadHandler(BaseHandler, blobstore_handlers.BlobstoreDownloadHandler):
    @user_required
    def get(self, key):
        if not blobstore.get(key):
            self.error(404)
        else:
            self.send_blob(blobstore.BlobInfo.get(key),
                           save_as=True)


#class FileDownloadHandlerGS(BaseHandler, blobstore_handlers.BlobstoreDownloadHandler):
#    @user_required
#    def get(self, *args, **kwargs):
#        file_name = kwargs['file_name']
#        bucket_name = kwargs['bucket']
#        file_name_gs = '/' + bucket_name + '/' + file_name
#        blobstore_filename = '/gs{}'.format(file_name_gs)
#        blob_key = blobstore.create_gs_key(blobstore_filename)
#        print('blob_key: ', blob_key)
#        #print(blob_key)
#        #print(type(blob_key))
#        #data = blobstore.fetch_data(blob_key, 0, 6)
#        #print('fetching data', data)
#        self.send_blob(blob_key,
#                       save_as=file_name)


class FileDownloadHandlerGSN(BaseHandler, blobstore_handlers.BlobstoreDownloadHandler):
    @user_required
    def get(self, *args, **kwargs):
        file_name = self.request.get('file_name')
        file_name_gs = self.request.get('file_name_gs')
        blob_key = blobstore.create_gs_key(file_name_gs)
        print('blob_key: ', blob_key)
        self.send_blob(blob_key,
                       save_as=file_name)













