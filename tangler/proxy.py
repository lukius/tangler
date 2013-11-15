import logging

from twisted.web import http, proxy
from twisted.internet import reactor
from twisted.web.http import HTTPChannel, Request

from http_client import TanglerHTTPClientFactory, TanglerHTTPClient


class TanglerProxy(object):

    def __init__(self, options):
        self.options = options
    
    def run(self):
        http_factory = http.HTTPFactory(timeout=self.options.timeout)
        http_factory.protocol = TanglerProtocol
        TanglerHTTPClient.initialize(self.options.plugins)
        reactor.listenTCP(self.options.port, http_factory)
        logging.log(logging.INFO, 'Starting Tangler on port %d' %\
                                   self.options.port)
        reactor.run()        

    
class TanglerRequest(Request):
    
    BANNED_HEADERS = ['accept-encoding', 'cache-control', 'if-modified-since',
                      'if-none-match', 'keep-alive']
    
    def __init__(self, channel, queued, reactor=reactor):
        Request.__init__(self, channel, queued)
        self.reactor = reactor

    def process_headers(self):
        headers = self.getAllHeaders().copy()
        for header in self.BANNED_HEADERS:
            if header in headers:
                del headers[header]
        return headers

    def path_from_uri(self):
        if (self.uri.find("http://") == 0):
            index = self.uri.find('/', 7)
            return self.uri[index:]
        return self.uri

    def handle_host_resolved(self, address):
        host = self.getHeader("host")
        new_headers = self.process_headers()
        client = self.getClientIP()
        path = self.path_from_uri()

        self.content.seek(0,0)
        data = self.content.read()

        self.connect(host, self.method, path, data, new_headers)

    def handle_error_resolving_host(self, error):
        try:
            self.finish()
        except Exception:
            pass
        
    def resolve_host(self, host):
        return reactor.resolve(host)

    def process(self):
        host = self.getHeader('host')
        deferred = self.resolve_host(host)
        deferred.addCallback(self.handle_host_resolved)
        deferred.addErrback(self.handle_error_resolving_host)
        return deferred

    def connect(self, host, method, path, data, headers):
        logging.log(logging.INFO, 'Connecting to %s' % host)
        connection_factory = TanglerHTTPClientFactory(method, path, data,
                                                      headers, self)
        connection_factory.protocol = TanglerHTTPClient
        self.reactor.connectTCP(host, 80, connection_factory)
        
        
class TanglerProtocol(HTTPChannel):
    requestFactory = TanglerRequest        