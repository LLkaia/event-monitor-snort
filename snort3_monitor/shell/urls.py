from django.urls import path

from .views import post_shell_command


urlpatterns = [
    path("", post_shell_command, name='shell-post'),
]
