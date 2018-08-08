import sys
import urllib2
from argparse import ArgumentParser
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from ConfigParser import RawConfigParser
from Queue import Queue
from thread import interrupt_main
from threading import Thread
from time import sleep
from traceback import print_exception
import logging


logger = logging.getLogger(__name__)
log_fmt = '%(asctime)s [%(levelname)s]: %(message)s (%(filename)s: %(lineno)d)'
logging.basicConfig(format=log_fmt)


class BugsnagAgent(object):
    """
    The BugsnagAgent sits on your server and forwards exception payloads to
    https://notify.bugsnag.com/.

    It's designed to protect you against any latency spikes that may
    occur talking across the internet in an exception handler.
    """
    DEFAULTS = {
        'endpoint': 'https://notify.bugsnag.com/',
        'listen': '127.0.0.1',
        'log_level': 'INFO',
        'port': 3829,
        'queue_length': 1000
    }

    FORWARDED_HEADERS = [
        'bugsnag-sent-at',
        'bugsnag-api-key',
        'bugsnag-payload-version'
    ]

    def __init__(self):
        self.parse_config()
        self.queue = Queue(self.DEFAULTS['queue_length'])

        if self.log_level:
            logger.setLevel(getattr(logging, self.log_level.upper()))
        else:
            logger.setLevel(getattr(logging, self.DEFAULTS['log_level']))

    def parse_config(self):
        """
        Initializes self.port, self.listen, self.endpoint and self.connection
        """

        parser = ArgumentParser(description='Bugsnag Agent')
        parser.add_argument(
            '-c', '--config',
            dest='config_file',
            default='/etc/bugsnag.conf',
            help='The path to your config file (default /etc/bugsnag.conf)'
        )
        parser.add_argument(
            '-e', '--endpoint',
            dest='endpoint',
            help=("The URL of your Bugsnag server (default {})".format(
                self.DEFAULTS['endpoint']))
        )
        parser.add_argument(
            '-p', '--port',
            dest='port',
            type=int,
            help=("The port to bind to (default {})".format(
                self.DEFAULTS['port']))
        )
        parser.add_argument(
            '-i', '--ip',
            dest='listen',
            help=("The IP to listen on (use 0.0.0.0 to allow anyone to "
                  "connect , default {})".format(self.DEFAULTS['listen']))
        )
        parser.add_argument(
            '-l', '--log-level',
            dest='log_level',
            help=("Logging verbosity, default {}".format(
                self.DEFAULTS['log_level']))
        )

        args = parser.parse_args()

        config = RawConfigParser()
        config.read(args.config_file)

        # Iterate over arguments and set values in oder of precedence:
        # 1 - Arguments
        # 2 - Config file
        # 3 - Internal defaults
        conf_opts = {"port": config.getint,
                     "endpoint": config.get,
                     "listen": config.get,
                     "log_level": config.get,
                     "ip": config.get}
        for opt, _ in vars(args).iteritems():
            if getattr(args, opt) is not None:
                setattr(self, opt, getattr(args, opt))
            elif config.has_option('bugsnag', opt) and opt in conf_opts:
                setattr(self, opt, conf_opts[opt]('bugsnag', opt))
            else:
                setattr(self, opt, self.DEFAULTS[opt])

    def start(self):
        """
        Run the agent, and wait for a SIGINT or SIGTERM.
        """
        try:
            server = Thread(target=self._thread(self._server), name='server')
            server.setDaemon(True)
            server.start()

            for _ in range(0, 10):
                client = Thread(
                    target=self._thread(self._client),
                    name='client'
                )
                client.setDaemon(True)
                client.start()

            logger.info("Bugsnag Agent started. http://{ip}:{port} -> "
                        "{endpoint}".format(
                            ip=self.listen,
                            port=self.port,
                            endpoint=self.endpoint
                        ))
            while True:
                sleep(1000)
        except KeyboardInterrupt:
            # give threads time to print exceptions
            sleep(0.1)

    def enqueue(self, body, headers={}):
        """
        Add a new payload to the queue.
        """
        try:
            self.queue.put_nowait({
                'body':body,
                'headers':headers
            })

            logger.info("Enqueued {body_length} bytes "
                        "({queue_size}/{queue_max_size})".format(
                            body_length=len(body),
                            queue_size=self.queue.qsize(),
                            queue_max_size=self.queue.maxsize
                        )
                        )
        except:
            logger.info(
                "Discarding report as queue is full: {}".format(repr(body)))

    def _server(self):
        """
        Run the HTTP server on (self.listen, self.port) that puts
        payloads into the queue.
        """
        server = HTTPServer((self.listen, self.port),
                            BugsnagHTTPRequestHandler)
        server.bugsnag = self
        server.serve_forever()

    def _client(self):
        """
        Continually monitor the queue and send anything in it to Bugsnag.
        """
        while True:
            request = self.queue.get(True)
            body = request['body']
            headers = request['headers']
            logger.info("Sending {body_length} bytes ({queue_size}/"
                "{queue_max_size})".format(
                    body_length=len(body),
                    queue_size=self.queue.qsize(),
                    queue_max_size=self.queue.maxsize
                )
            )

            try:
                req = urllib2.Request(self.endpoint, body, headers)
                res = urllib2.urlopen(req)
                res.read()
            except urllib2.URLError as e:
                if hasattr(e, 'code') and e.code in (400, 500):
                    logger.warning('Bad response, removing report ({code}: {msg})'.format(
                        code=e.code,
                        msg=e.msg
                    ))
                else:
                    logger.warning('Cannot send request. Retrying in 5 seconds')
                    if logger.isEnabledFor(logging.DEBUG):
                        print_exception(*sys.exc_info())
                    sleep(5)
                    self.enqueue(body)

    def _thread(self, target):
        def run():
            try:
                target()
            except:
                interrupt_main()
                print_exception(*sys.exc_info())
            pass
        return run


class BugsnagHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """
        Enable CORS while running on a different host
        """
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, POST, HEAD')
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        """
        Show the current status of the agent
        """
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        bugsnag = self.server.bugsnag
        self.wfile.write("Bugsnag agent: {listen}:{port} -> {endpoint} " \
            "({queue_size}/{queue_max_size})\n".format(
                listen=bugsnag.listen,
                port=bugsnag.port,
                endpoint=bugsnag.endpoint,
                queue_size=bugsnag.queue.qsize(),
                queue_max_size=bugsnag.queue.maxsize
            )
        )

    def do_POST(self):
        """
        Accept a payload for forwarding
        """
        bugsnag = self.server.bugsnag
        body = self.rfile.read(int(self.headers['Content-Length']))
        headers = {}
        for key, value in self.headers.items():
            if key.lower() in BugsnagAgent.FORWARDED_HEADERS:
                headers[key] = value

        bugsnag.enqueue(body=body, headers=headers)

        response = "OK {ip}:{port} -> {endpoint} " \
            "({queue_size}/{queue_max_size})\n".format(
                ip=bugsnag.listen,
                port=bugsnag.port,
                endpoint=bugsnag.endpoint,
                queue_size=bugsnag.queue.qsize(),
                queue_max_size=bugsnag.queue.maxsize
            )

        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', len(response))
            self.end_headers()
            self.wfile.write(response)
        except:
            logger.info('Client disconnected before waiting for response')
            print_exception(*sys.exc_info())
            logger.info('Continuing...')

if __name__ == '__main__':
    BugsnagAgent().start()


def main():
    BugsnagAgent().start()
