import os
import re

from django.conf.urls.defaults import *
from django.conf import settings

static_files = os.path.join(os.path.dirname(__file__), 'media')
urlpatterns = patterns('pdfserver.views',
    url(r'^$', 'main', name='uploads'),
    url(r'^upload/$', 'upload_file', name='upload'),
#    url(r'^confirmdelete/$', 'confirm_delete', name='confirm_delete'),
    url(r'^confirmdelete/all/$', 'confirm_delete_all', name='confirm_delete_all'),
    url(r'^delete/$', 'delete', name='delete'),
    url(r'^deleteall/$', 'delete_all', name='delete_all'),
    
    url(r'^combine/$', 'combine_pdfs', name='combine_pdfs'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^' + re.escape(settings.MEDIA_URL.strip('/')) + '(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': static_files, 'show_indexes': True}),
    )
