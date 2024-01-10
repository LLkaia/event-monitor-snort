from rest_framework import serializers


class PerformanceSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    module = serializers.CharField(max_length=128)
    pegcounts = serializers.JSONField()


class PerformanceDeltaSerializer(serializers.Serializer):
    module = serializers.CharField(max_length=128)
    pegcounts = serializers.JSONField()
