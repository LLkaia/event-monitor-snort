import threading
from datetime import timedelta, datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request

from shell.models import Profiler
from shell.telnet import run_command, run_profiler


@api_view(['POST'])
def post_shell_command(request: Request) -> Response:
    """Process command.

    Take command from field 'command', run it
    in snort shell and return stdout.
    """
    command = request.data.get('command')
    if not command:
        return Response({'message': 'Provide a command!'}, status=status.HTTP_204_NO_CONTENT)
    try:
        stdout = run_command(command)
    except OSError:
        return Response({'message': 'Shell is not available!'}, status=status.HTTP_204_NO_CONTENT)
    return Response({'message': stdout}, status=status.HTTP_200_OK)


def is_previous_profiler_finished(time_now: datetime):
    """Check if previous profiler finished his work."""
    last_record = Profiler.objects.latest('start_time')
    if last_record.end_time >= time_now:
        return Response(
            {'message': f'Previous request in process. End: {timezone.localtime(last_record.end_time)}'},
            status=status.HTTP_226_IM_USED
        )
    elif last_record.rules is None:
        if (time_now - last_record.end_time) < timedelta(seconds=20):
            return Response(
                {'message': f'Previous request in process. End: {timezone.localtime(last_record.end_time)}'},
                status=status.HTTP_226_IM_USED
            )
        else:
            last_record.delete()
            raise Profiler.RecordMalformed
    return last_record


@api_view(['GET'])
def start_rule_profiling(request: Request) -> Response:
    """Process profiler request.

    Take duration of profiling from 'time' or
    'until', create new record in db and start
    rule profiler.
    """
    time_now = timezone.now()

    # check if previous request finished
    try:
        result = is_previous_profiler_finished(time_now)
        if isinstance(result, Response):
            return result
    except (Profiler.DoesNotExist, Profiler.RecordMalformed):
        pass

    time = request.query_params.get('time')
    until = request.query_params.get('until')

    # drop when both 'time' and 'until' are in query
    if time and until:
        return Response({'message': 'You can not provide both params!'}, status=status.HTTP_400_BAD_REQUEST)

    # when 'time' is provided
    if time:
        try:
            wait = int(time) * 60
            new_record = Profiler.objects.create(start_time=time_now)
            new_record.end_time = new_record.start_time + timedelta(seconds=wait)
            new_record.save()

            threading.Thread(target=run_profiler, args=(new_record, wait), name='Profiler').start()

            return Response(
                {'message': f'Rule profiler has been started. End: {timezone.localtime(new_record.end_time)}'},
                status=status.HTTP_202_ACCEPTED
            )
        except ValueError:
            return Response(
                {'message': f"'time' {time} is not in appropriate format. Provide minutes (integer)."},
                status=status.HTTP_400_BAD_REQUEST
            )

    # when 'until' is provided
    if until:
        try:
            timestamp_format = "%Y-%m-%d %H:%M:%S"
            end_time = timezone.make_aware(datetime.strptime(until, timestamp_format))
            if end_time < time_now:
                return Response({'message': 'Provide time in future, not in the past.'},
                                status=status.HTTP_400_BAD_REQUEST)
            new_record = Profiler.objects.create(start_time=time_now, end_time=end_time)
            wait = int((new_record.end_time - new_record.start_time).total_seconds())

            threading.Thread(target=run_profiler, args=(new_record, wait), name='Profiler').start()

            return Response(
                {'message': f'Rule profiler has been started. End: {timezone.localtime(new_record.end_time)}'},
                status=status.HTTP_202_ACCEPTED
            )
        except ValueError:
            return Response({'message': "Use format YYYY-MM-DD HH:MM:SS in 'until'."},
                            status=status.HTTP_400_BAD_REQUEST)

    # when period is not provided
    return Response({'message': "Provide 'time' in minutes or 'until' in format YYYY-MM-DD HH:MM:SS."},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_last_profiler_record(request: Request) -> Response:
    """Provide last profiler record."""
    try:
        result = is_previous_profiler_finished(timezone.now())
        if isinstance(result, Response):
            return result

    except Profiler.DoesNotExist:
        return Response({'message': 'Profiler records are clear.'}, status=status.HTTP_204_NO_CONTENT)

    except Profiler.RecordMalformed:
        return Response({'message': 'Previous profiler record was malformed.'},
                        status=status.HTTP_204_NO_CONTENT)

    return Response({'rules': result.rules}, status=status.HTTP_200_OK)
