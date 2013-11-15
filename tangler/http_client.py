import logging
import random

from twisted.internet.protocol import ClientFactory
from twisted.web.http import HTTPClient


class TanglerHTTPClient(HTTPClient):

    shutdown_complete = False

    @classmethod
    def initialize(cls, plugins):
        cls.plugins = plugins

    def __init__(self, command, path, data, headers, client):
        self.command = command
        self.path = path
        self.data = data
        self.headers = headers
        self.client = client
        self.headers_received = dict()
        self.connection_lost = False

    def send_request(self):
        logging.log(logging.INFO, 'Sending request: %s %s' %\
                                   (self.command, self.path))
        self.sendCommand(self.command, self.path)

    def send_headers(self):
        logging.log(logging.INFO, 'Sending headers:')
        self.headers['connection'] = 'close'    
        for header, value in self.headers.items():
            logging.log(logging.INFO, '%s: %s' % (header, value))
            self.sendHeader(header, value)
        self.endHeaders()

    def send_post_data(self):
        self.transport.write(self.data)

    def connectionMade(self):
        self.send_request()
        self.send_headers()

        if self.command == 'POST':
            self.send_post_data()

    def handleStatus(self, version, code, message):
        logging.log(logging.INFO, 'Response: %s %s %s (to %s %s)' %\
                                   (version, code, message,
                                    self.command, self.path))
        self.client.setResponseCode(int(code), message)

    def handleHeader(self, key, value):
        self.headers_received[key] = value

    def handleEndHeaders(self):
       if self.length == 0:
           self.shutdown()

    def apply_plugins_to(self, data):
        suitable_plugins = filter(lambda plugin: plugin.can_handle(self),
                                  self.plugins)
        new_data = data
        for plugin in suitable_plugins:
            new_data = plugin.value(new_data)
        return new_data
    
    def set_headers(self, data=None):
        if data is not None:
            self.headers_received['Content-Length'] = len(data)
        for header_key, header_value in self.headers_received.items():
            self.client.setHeader(header_key, header_value)

    def handleEndHeaders(self):
        return
        content_length = int(self.headers_received.get('Content-Length', 0))
        if content_length == 0:
            self.set_headers()
            self.shutdown()

    def handleResponse(self, data):
        logging.log(logging.INFO, 'Data successfully received')
        if not self.shutdown_complete:
            new_data = self.apply_plugins_to(data)
            self.set_headers(new_data)
            logging.log(logging.INFO, 'Sending data back to client')
            self.client.write(new_data)
            self.shutdown()

    def shutdown(self):
        if not self.shutdown_complete:
            self.shutdown_complete = True
            try:
                self.client.finish()
                self.transport.loseConnection()
            except Exception:
                pass
                        

class TanglerHTTPClientFactory(ClientFactory):
    
    def __init__(self, command, uri, data, headers, client):
        self.command = command
        self.path = uri
        self.data = data
        self.headers = headers
        self.client = client

    def buildProtocol(self, addr):
        return self.protocol(self.command, self.path, self.data,
                             self.headers, self.client)

    def clientConnectionFailed(self, connector, reason):
        self.client.finish()