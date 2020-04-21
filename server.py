import socket
import os
import mimetypes

class TCPServer:
    host = '127.0.0.1'
    port = 8888

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))

        s.listen(5)
        print("Listening at", s.getsockname())

        while True:
            conn, addr = s.accept()
            print("Connected to", addr)
            data = conn.recv(1024)

            response = self.handle_request(data)
            try:
                if(response):
                    conn.sendall(response)
            except TypeError as e:
                print("Error:", e)
            conn.close()

    def handle_request(self, data):
        """
        Handles incoming requests. Must be overridden in subclass
        :param data: request header
        :return: response
        """
        return data


class HTTPServer(TCPServer):
    headers = {
        'Server': 'The Ultimate Super Server',
        'Content-Type': 'text/html',
    }
    status_codes = {
        200: 'OK',
        404: 'Not Found',
        501: 'Not Implemented'
    }

    def __init__(self):
        self.request = None

    def handle_request(self, data):
        self.request = HTTPRequest()
        self.request.parse(data)
        if self.request.method is not None:
            try:
                handler = getattr(self, f'handle_{self.request.method.lower()}')
            except AttributeError:
                handler = self.handle_501
        else:
            return
        result = handler()
        return result

    def handle_get(self):
        filename = self.request.uri.strip('/')
        if not filename:
            filename = "index.html"
        if os.path.exists(filename):
            response_line = self.response_line(200)
            content_type, _ = mimetypes.guess_type(filename)

            extra_headers = {'Content-Type': content_type}
            response_headers = self.response_headers(extra_headers)

            if content_type.startswith('image'):
                with open(filename, 'rb') as input_file:
                    response_body = input_file.read()
                    b = bytes(f"{response_line}{response_headers}\r\n", 'utf-8')
                    return b + response_body
            else:
                with open(filename, errors='ignore') as input_file:
                    response_body = input_file.read()
        else:
            response_line = self.response_line(404)
            response_headers = self.response_headers()
            response_body = '<h1>404 Not Found</h1>'

        return bytes(f"{response_line}{response_headers}\r\n{response_body}", 'utf-8')

    def handle_options(self):
        response_line = self.response_line(200)
        extra_headers = {
            'Allow': 'OPTIONS, GET'
        }
        response_headers = self.response_headers(extra_headers)
        return bytes(f"{response_line}{response_headers}\r\n", "utf-8")

    def handle_501(self):
        response_line = self.response_line(501)
        response_headers = self.response_headers()
        response_body = "<h1>501 Not Implemented</h1>"
        return bytes(f"{response_line}{response_headers}\r\n{response_body}", "utf-8")

    def response_line(self, status_code):
        reason = self.status_codes[status_code]
        return f"HTTP/1.1 {status_code} {reason}\r\n"

    def response_headers(self, extra_headers=None):
        headers_copy = self.headers.copy()
        if extra_headers:
            headers_copy.update(extra_headers)
        headers = ""
        for h in headers_copy:
            headers += f"{h}: {headers_copy[h]}\r\n"
        return headers


class HTTPRequest:
    def __init__(self):
        self.method = None
        self.uri = None
        self.http_version = 'HTTP/1.1'
        self.headers = {}

    def parse(self, data):
        line = str(data).split("\\r\\n")
        line = line[0].replace("b\'", "")
        line = line.replace('b"', "")
        lines = line.split(" ")
        if len(lines) == 1:
            return
        self.method = lines[0]
        self.uri = lines[1]
        if len(lines) > 2:
            self.http_version = lines[2]


def main():
    server = HTTPServer()
    server.start()


if __name__ == '__main__':
    main()
