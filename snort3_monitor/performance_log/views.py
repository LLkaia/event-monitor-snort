from collections import Counter
from datetime import timedelta, datetime

from django.db.models import QuerySet
from django.utils.timezone import make_aware, utc
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from performance_log.models import Performance
from performance_log.serializers import PerformanceSerializer


class PerformanceList(generics.ListAPIView):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer

    def get_queryset(self) -> QuerySet:
        """Process query params

        Client can use only allowed_params in query.
        """
        queryset = super().get_queryset()

        allowed_params = ['period_start', 'period_stop', 'module']
        params = [key for key in self.request.query_params]
        self.validate_params(params, allowed_params)

        # checks if timestamp params are included
        period_start = self.request.query_params.get('period_start')
        period_stop = self.request.query_params.get('period_stop')
        if not (period_start and period_stop):
            raise ValidationError({"error": "You should define 'period_start' and 'period_stop'."})

        # checks if format is proper
        period_start = self.validate_date(period_start)
        period_stop = self.validate_date(period_stop) + timedelta(days=1)
        queryset = queryset.filter(timestamp__gte=period_start, timestamp__lte=period_stop)

        return queryset.order_by('id')

    def list(self, request, *args, **kwargs):
        """Aggregate json field with pegcounts"""
        queryset = self.filter_queryset(self.get_queryset())

        aggregated_queryset = {}
        for record in queryset:
            if record.module not in aggregated_queryset.keys():
                aggregated_queryset[record.module] = Counter()
            aggregated_queryset[record.module].update(record.pegcounts)

        # fit to serializer
        new_queryset = []
        for module, pegs in aggregated_queryset.items():
            new_queryset.append({
                'module': module,
                'pegcounts': pegs
            })

        # paginate
        page = self.paginate_queryset(new_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # if pagination is turned off
        serializer = self.get_serializer(new_queryset, many=True)
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
                return make_aware(date, utc)
            except ValueError:
                pass
        raise ValidationError({"error": "Use format YYYY-MM-DD HH:MM:SS (you can skip SS, MM, HH)"})

    @staticmethod
    def validate_params(entered, allowed: list) -> None:
        """Validate query parameters

        :param entered: Params of query, which user entered
        :param allowed: Params that are allowed in endpoint
        """
        allowed.append('page')
        only_allowed_params_present = set(entered).issubset(set(allowed))
        if not only_allowed_params_present:
            raise ValidationError(
                {"error": f"You can use only {', '.join(allowed)} as query filters."})
