from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from shell.telnet import run_command


@api_view(['POST'])
def post_shell_command(request):
    """Process command

    Take command from field 'command', run it
    in snort shell and return stdout.
    """
    command = request.data.get('command')
    if not command:
        return Response({'message': 'Provide a command!'}, status=status.HTTP_204_NO_CONTENT)
    stdout = run_command(command)
    return Response({'message': stdout}, status=status.HTTP_200_OK)
