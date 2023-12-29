from django.db import models


class Performance(models.Model):
    timestamp = models.DateTimeField()
    module = models.CharField(max_length=128)
    pegcounts = models.JSONField()

