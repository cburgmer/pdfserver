from django.conf import settings
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.core.files import storage

upload_location = getattr(settings, 'UPLOAD_TO', settings.MEDIA_ROOT)

class Upload(models.Model):
    """Uploaded files."""
    file = models.FileField(storage=storage.FileSystemStorage(location=upload_location), upload_to='upload')
    filename = models.CharField(max_length=255)
    page_count = models.IntegerField(blank=True, null=True)
    
    def __unicode__(self):
        return u"%s" % (self.file)

    @property
    def size(self):
        return filesizeformat(self.file.size)
