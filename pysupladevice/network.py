import ssl
import socket
import select


def connect_secure(address, port):
    print(f"Connecting to {address}:{port} (secure)")
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.VerifyMode.CERT_NONE
    sock = socket.create_connection((address, port))
    ssock = context.wrap_socket(sock, server_hostname=address)
    ssock.settimeout(0.1)
    return ssock


def connect(address, port):
    print(f"Connecting to {address}:{port} (insecure)")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.1)
    sock.connect((address, port))
    return sock


class NetworkError(Exception):
    pass


class Socket(object):
    def __init__(self, server, port, secure):
        if secure:
            self._socket = connect_secure(server, port)
        else:
            self._socket = connect(server, port)
        self._buffer = b""

    def read(self):
        try:
            if len(self._buffer) == 0:
                sockets = [self._socket]
                ready_to_read, ready_to_write, in_error = select.select(
                    sockets, sockets, sockets, 0.1
                )
                if len(ready_to_read) > 0:
                    data = self._socket.recv(2048)
                    if len(data) == 0:
                        raise NetworkError("No data, connection reset by peer?")
                    self._buffer += data

            if len(self._buffer) > 0:
                # only return some of the data at a time, to test partial data receipt
                MAXLEN = 1024
                result = self._buffer[:MAXLEN]
                self._buffer = self._buffer[MAXLEN:]
                return result
            else:
                return b""
        except BrokenPipeError as exn:
            raise NetworkError(str(exn))
            reconnect = True
        except ConnectionResetError as exn:
            raise NetworkError(str(exn))
        except ssl.SSLZeroReturnError as exn:
            raise NetworkError(str(exn))

    def write(self, data):
        self._socket.sendall(data)
