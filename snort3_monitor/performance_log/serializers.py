from rest_framework import serializers


class PerformanceSerializer(serializers.Serializer):
    module = serializers.CharField(max_length=128)
    pegcounts = serializers.JSONField()
