import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from agf.common import AgfError
from agf.webfetch import fetch, register


PAGE = '<h1>來源</h1>\n<script>not_executed()</script>'.encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.requests.append(self.path)
        if self.path == '/robots.txt':
            status, body = self.server.robots_status, self.server.robots_body
        elif self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/page')
            self.end_headers()
            return
        elif self.path == '/cross':
            self.send_response(302)
            self.send_header('Location', f'http://localhost:{self.server.server_port}/page')
            self.end_headers()
            return
        elif self.path == '/loop':
            self.send_response(302)
            self.send_header('Location', '/loop')
            self.end_headers()
            return
        elif self.path.startswith('/hop/'):
            self.send_response(302)
            self.send_header('Location', f'/hop/{int(self.path.rsplit("/", 1)[1]) + 1}')
            self.end_headers()
            return
        elif self.path in {'/big', '/stream'}:
            status, body = 200, b'x' * 1024
        else:
            status, body = 200, PAGE
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        if self.path != '/stream':
            self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except ConnectionError:
            pass


class WebFetchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.webfetch-test-', dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.server.requests = []
        self.server.robots_status = 404
        self.server.robots_body = b''
        self.proxy = patch.dict('os.environ', {'NO_PROXY': '127.0.0.1,localhost', 'no_proxy': '127.0.0.1,localhost'})
        self.proxy.start()
        self.addCleanup(self.proxy.stop)

    def test_plan_has_no_network_or_directory_side_effect(self):
        output = self.root / 'new' / 'page.html'
        with patch('agf.webfetch.build_opener', side_effect=AssertionError('PLAN must not connect')):
            result = fetch(self.origin + '/page', output)
        self.assertEqual(result['status'], 'PLAN')
        self.assertFalse(output.parent.exists())
        self.assertEqual(self.server.requests, [])

    def test_success_saves_exact_bytes_and_source_metadata(self):
        output = self.root / 'page.html'
        result = fetch(self.origin + '/page', output, execute=True)
        self.assertEqual(output.read_bytes(), PAGE)
        self.assertEqual(result['http_status'], 200)
        self.assertEqual(result['url'], self.origin + '/page')
        self.assertEqual(result['content_type'], 'text/html; charset=utf-8')
        self.assertEqual(result['sha256'], hashlib.sha256(PAGE).hexdigest())
        self.assertEqual(result['bytes'], len(PAGE))
        self.assertEqual(self.server.requests, ['/robots.txt', '/page'])

    def test_known_and_streaming_size_limits_leave_no_output(self):
        for endpoint in ('/big', '/stream'):
            output = self.root / endpoint[1:] / 'page.html'
            with self.subTest(endpoint=endpoint), self.assertRaisesRegex(AgfError, 'max-bytes'):
                fetch(self.origin + endpoint, output, execute=True, max_bytes=16)
            self.assertFalse(output.parent.exists())

    def test_existing_output_is_preserved_without_network(self):
        output = self.root / 'page.html'
        output.write_bytes(b'keep')
        with self.assertRaisesRegex(AgfError, 'Existing output'):
            fetch(self.origin + '/page', output, execute=True)
        self.assertEqual(output.read_bytes(), b'keep')
        self.assertEqual(self.server.requests, [])

    def test_redirect_same_origin_and_explicit_other_host(self):
        result = fetch(self.origin + '/redirect', self.root / 'same.html', execute=True)
        self.assertEqual(result['url'], self.origin + '/page')
        with self.assertRaisesRegex(AgfError, 'allow-host'):
            fetch(self.origin + '/cross', self.root / 'blocked.html', execute=True)
        self.assertFalse((self.root / 'blocked.html').exists())
        result = fetch(self.origin + '/cross', self.root / 'allowed.html', execute=True, allow_hosts=['localhost'])
        self.assertEqual(result['url'], f'http://localhost:{self.server.server_port}/page')

    def test_loop_stops_without_output(self):
        with self.assertRaisesRegex(AgfError, 'loop'):
            fetch(self.origin + '/loop', self.root / 'page.html', execute=True)
        self.assertFalse((self.root / 'page.html').exists())
        self.assertEqual(self.server.requests.count('/loop'), 1)

    def test_redirect_chain_has_a_fixed_request_limit(self):
        with self.assertRaisesRegex(AgfError, 'redirect limit'):
            fetch(self.origin + '/hop/0', self.root / 'page.html', execute=True)
        self.assertEqual(self.server.requests, ['/robots.txt', '/hop/0', '/hop/1', '/hop/2', '/hop/3'])
        self.assertFalse((self.root / 'page.html').exists())

    def test_robots_denial_or_uncertainty_stops_before_page(self):
        for status, body in ((200, b'User-agent: *\nDisallow: /page\n'), (403, b''), (503, b''), (200, b'\xff')):
            self.server.robots_status, self.server.robots_body = status, body
            self.server.requests = []
            with self.subTest(status=status), self.assertRaises(AgfError):
                fetch(self.origin + '/page', self.root / 'page.html', execute=True)
            self.assertEqual(self.server.requests, ['/robots.txt'])
            self.assertFalse((self.root / 'page.html').exists())

    def test_reject_userinfo_file_urls_and_invalid_limits(self):
        for url in ('file:///tmp/page.html', 'https://name:secret@example.invalid/', 'http://example.invalid/\npath', 'http://example.invalid:0/'):
            with self.subTest(url=url), self.assertRaises(AgfError):
                fetch(url, self.root / 'page.html')
        for kwargs in ({'timeout': float('nan')}, {'timeout': 0}, {'max_bytes': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(AgfError):
                fetch(self.origin, self.root / 'page.html', **kwargs)

    def test_register_adds_fetch_to_existing_source_subparsers(self):
        parser = argparse.ArgumentParser()
        register(parser.add_subparsers(required=True))
        args = parser.parse_args(['fetch', self.origin, '--output', str(self.root / 'page.html')])
        self.assertEqual(args.func(args)['status'], 'PLAN')
