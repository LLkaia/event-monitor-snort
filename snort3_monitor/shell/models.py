from django.db import models


class Profiler(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    rules = models.JSONField(null=True, blank=True)

    class RecordMalformed(Exception):
        """
        Custom exception raised when record
        exists without 'rules' data too long
        after end_time was expired.
        """
        pass
