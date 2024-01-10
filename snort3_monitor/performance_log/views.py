from collections import Counter
from datetime import datetime

from django.db.models import QuerySet
from django.utils.timezone import make_aware
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from performance_log.models import Performance
from performance_log.serializers import PerformanceSerializer, PerformanceDeltaSerializer


class PerformanceList(generics.ListAPIView):
    queryset = Performance.objects.all()

    def get_queryset(self):
        """Process query params"""
        queryset = super().get_queryset()
        PerformanceList.serializer_class = PerformanceSerializer

        # check for only allowed params
        allowed_params = ['period_start', 'period_stop', 'module', 'delta']
        params = [key for key in self.request.query_params]
        self.validate_params(params, allowed_params)

        # check if timestamp params are included
        period_start = self.request.query_params.get('period_start')
        period_stop = self.request.query_params.get('period_stop')
        if not (period_start and period_stop):
            raise ValidationError({"error": "You should define 'period_start' and 'period_stop'."})

        # checks if format is proper and filter by them
        period_start = self.validate_date(period_start)
        period_stop = self.validate_date(period_stop)
        queryset = queryset.filter(timestamp__gte=period_start, timestamp__lte=period_stop)

        # filter by 'module' prefix
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module__startswith=module)

        # aggregate pegcounts in each module
        if self.request.query_params.get('delta') == 'true':
            PerformanceList.serializer_class = PerformanceDeltaSerializer
            queryset = self.get_sum_queryset(queryset)

        return queryset

    def list(self, request, *args, **kwargs) -> Response:
        """Paginate and serialize queryset and send response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    def validate_date(date: str) -> datetime:
        """Validate date format

        Only formats(list) are allowed in date params.
        """
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H", "%Y-%m-%d"]
        for frmt in formats:
            try:
                date = datetime.strptime(date, frmt)
                return make_aware(date)
            except ValueError:
                pass
        raise ValidationError({"error": "Use format YYYY-MM-DD HH:MM:SS (you can skip SS, MM, HH)"})

    @staticmethod
    def validate_params(entered: list, allowed: list) -> None:
        """Validate query parameters

        :param entered: Params of query, which user entered
        :param allowed: Params that are allowed in endpoint
        """
        allowed.append('page')
        only_allowed_params_present = set(entered).issubset(set(allowed))
        if not only_allowed_params_present:
            raise ValidationError(
                {"error": f"You can use only {', '.join(allowed)} as query filters."})

    @staticmethod
    def get_sum_queryset(queryset: QuerySet):
        """Calculate pegcounts sum of all records
        between two mentioned timestamps.
        """
        aggregated_queryset = {}
        for record in queryset:
            if record.module not in aggregated_queryset.keys():
                aggregated_queryset[record.module] = Counter()
            aggregated_queryset[record.module].update(record.pegcounts)
        new_queryset = []
        for module, pegs in aggregated_queryset.items():
            new_queryset.append({
                'module': module,
                'pegcounts': pegs
            })
        return new_queryset
