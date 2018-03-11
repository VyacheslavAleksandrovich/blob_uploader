from google.appengine.api import mail, app_identity

import logging

logger = logging.getLogger('aux_log')
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()
logger.addHandler(ch)


def get_download_url(key):
        return 'https://{0}.appspot.com/download/{1}'.format(
                app_identity.get_application_id(), key)


def send_download_url_blobstore(email_address, key):
    to_ = email_address
    txt_ = 'download url {0}'.format(
        get_download_url(key))
    from_ = 'uploader@{0}.appspotmail.com'.format(app_identity.get_application_id())
    mail.send_mail(sender=from_,
                   to=to_,
                   subject='download url',
                   body=txt_)
    logger.debug("mail msg: %s", txt_)


def send_download_url_gs(email_address, url):
    to_ = email_address
    txt_ = 'download url {0}'.format(
        url)
    from_ = 'uploader@{0}.appspotmail.com'.format(app_identity.get_application_id())
    mail.send_mail(sender=from_,
                   to=to_,
                   subject='download url',
                   body=txt_)
    logger.debug("mail from: %s; to: %s; msg: %s;", from_, to_, txt_)
