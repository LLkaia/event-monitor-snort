from django.urls import path

from performance_log.views import PerformanceList


urlpatterns = [
    path("", PerformanceList.as_view(), name='performance-list'),
]
