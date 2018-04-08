#!/usr/bin/env python

from google.appengine.ext import blobstore

import logging
import webapp2

from app.views.base_handler import BaseHandler, user_required
from app.views.auth_views import SignupHandler, VerificationHandler, SetPasswordHandler, LoginHandler
from app.views.auth_views import LogoutHandler, ForgotPasswordHandler
from app.views.file_handlers import FileDownloadHandler, FileUploadHandler, FilePartUploadHandler, \
    UploadURL, MergeFile, MergeIsDone, DownloadURL, FileDownloadHandlerGSN

logger = logging.getLogger('blob_app')
logger.setLevel(logging.WARNING)
#logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)



class MainHandler(BaseHandler):
    @user_required
    def get(self):
        upload_url = blobstore.create_upload_url('/upload_file')
        self.render_template('home.html', params = {'upload_url': upload_url})


class MainHandlerPart(BaseHandler):
    @user_required
    def get(self):
        self.render_template('home_part.html')


config = {
    'webapp2_extras.auth': {
        'user_model': 'app.models.User',
        'user_attributes': ['name']
    },
        'webapp2_extras.sessions': {
        'secret_key': 'YOUR_SECRET_KEY'
    }
}

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandlerPart, name='home'),
    webapp2.Route('/main_part', MainHandlerPart, name='home_part'),
    webapp2.Route('/signup', SignupHandler),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
      handler=VerificationHandler, name='verification'),
    webapp2.Route('/password', SetPasswordHandler),
    webapp2.Route('/login', LoginHandler, name='login'),
    webapp2.Route('/logout', LogoutHandler, name='logout'),
    webapp2.Route('/forgot', ForgotPasswordHandler, name='forgot'),
    ('/upload_file', FileUploadHandler),
    ('/upload_file_part', FilePartUploadHandler),
    ('/merge_file', MergeFile),
    webapp2.Route('/merge_is_done/<task_id:.+>', MergeIsDone),
    ('/upload_url', UploadURL),
    webapp2.Route('/download_url/<task_id:.+>', DownloadURL),
    #webapp2.Route('/gs/<bucket:.+>/<file_name:.+>', FileDownloadHandlerGS),
    webapp2.Route('/gsn/', FileDownloadHandlerGSN),
    ('/download/([^/]+)?', FileDownloadHandler)
], debug=True, config=config)

