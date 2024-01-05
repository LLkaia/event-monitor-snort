import telnetlib


HOST = "localhost"
PORT = 12345


def run_command(command: str) -> str:
    """Run command in snort shell and return stdout"""
    command = command.encode('utf-8')
    with telnetlib.Telnet(HOST, PORT) as tn:
        tn.read_until(b'o")~')
        tn.write(command + b'\n')
        output = tn.read_until(b'o")~', timeout=5)
    return output.decode('utf-8').strip('o")~\n ')
