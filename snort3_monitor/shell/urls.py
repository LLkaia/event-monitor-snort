from django.urls import path

from shell.views import post_shell_command, start_rule_profiling, get_last_profiler_record


urlpatterns = [
    path("", post_shell_command, name='shell-post'),
    path("profiler/", start_rule_profiling, name='start-profiler'),
    path("profiler/last/", get_last_profiler_record, name='get-profiler')
]
