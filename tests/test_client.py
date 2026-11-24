import unittest
import sys
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import importlib.util

# Add the parent directory to sys.path to import the client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load client directly using importlib to avoid importing homeassistant from __init__.py
client_spec = importlib.util.spec_from_file_location("client", os.path.join(os.path.dirname(__file__), "..", "custom_components", "urlplayer_media_player", "client.py"))
client_module = importlib.util.module_from_spec(client_spec)
client_spec.loader.exec_module(client_module)

UrlPlayerClient = client_module.UrlPlayerClient
UrlPlayerAuthError = client_module.UrlPlayerAuthError
UrlPlayerConnectionError = client_module.UrlPlayerConnectionError

class TestUrlPlayerClient(unittest.TestCase):
    
    def setUp(self):
        # Start a test server on a random port
        self.server = HTTPServer(('localhost', 0), TestRequestHandler)
        self.port = self.server.server_address[1]
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Give the server a moment to start
        time.sleep(0.1)
        
        self.client = UrlPlayerClient('localhost', self.port, 'test_token')
    
    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
    
    def test_health_no_auth(self):
        """Test that health endpoint works without authentication"""
        result = self.client.health()
        self.assertTrue(result)
    
    def test_status_with_auth(self):
        """Test status endpoint with valid token"""
        result = self.client.status()
        expected = {
            'status': 'playing',
            'volume': 0.5,
            'current_station': 'test_station',
            'current_track': 'test_track'
        }
        self.assertEqual(result, expected)
    
    def test_stations_with_auth(self):
        """Test stations endpoint with valid token"""
        result = self.client.stations()
        expected = [
            {'id': '1', 'name': 'Station 1'},
            {'id': '2', 'name': 'Station 2'}
        ]
        self.assertEqual(result, expected)
    
    def test_artwork_with_auth(self):
        """Test artwork endpoint with valid token"""
        # Reset the flag before testing
        TestRequestHandler.return_404_artwork = False
        result = self.client.artwork()
        self.assertEqual(result, (b'test_artwork_data', ''))
    
    def test_invalid_token_raises_auth_error(self):
        """Test that invalid token raises UrlPlayerAuthError"""
        client = UrlPlayerClient('localhost', self.port, 'invalid_token')
        with self.assertRaises(UrlPlayerAuthError):
            client.status()
    
    def test_toggle_sends_correct_request(self):
        """Test toggle sends correct HTTP request"""
        self.client.toggle()
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/toggle')
    
    def test_stop_sends_correct_request(self):
        """Test stop sends correct HTTP request"""
        self.client.stop()
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/stop')
    
    def test_next_track_sends_correct_request(self):
        """Test next_track sends correct HTTP request"""
        self.client.next_track()
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/next')
    
    def test_previous_track_sends_correct_request(self):
        """Test previous_track sends correct HTTP request"""
        self.client.previous_track()
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/previous')
    
    def test_play_url_sends_correct_request(self):
        """Test play with URL sends correct HTTP request"""
        self.client.play(url='http://example.com/stream.mp3')
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/play')
        payload = TestRequestHandler.last_request['payload']
        self.assertEqual(payload.get('url'), 'http://example.com/stream.mp3')
    
    def test_play_media_id_sends_correct_request(self):
        """Test play with media_id sends correct HTTP request"""
        self.client.play(media_id='drive:12345')
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/play')
        payload = TestRequestHandler.last_request['payload']
        self.assertEqual(payload.get('media_id'), 'drive:12345')
    
    def test_play_source_sends_correct_request(self):
        """Test play with source sends correct HTTP request"""
        self.client.play(source='test_station')
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/play')
        payload = TestRequestHandler.last_request['payload']
        self.assertEqual(payload.get('source'), 'test_station')
    
    def test_play_resume_sends_correct_request(self):
        """Test play without parameters sends correct HTTP request"""
        self.client.play()
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/play')
        payload = TestRequestHandler.last_request['payload']
        self.assertEqual(payload, {})
    
    def test_set_volume_sends_correct_request(self):
        """Test set_volume sends correct HTTP request"""
        self.client.set_volume(0.65)
        self.assertTrue(TestRequestHandler.last_request['method'] == 'POST')
        self.assertTrue(TestRequestHandler.last_request['path'] == '/api/v1/volume')
        payload = TestRequestHandler.last_request['payload']
        self.assertEqual(payload.get('level'), 0.65)
    
    def test_artwork_returns_none_on_404(self):
        """Test artwork returns None on 404 error"""
        # Set the flag to trigger 404
        TestRequestHandler.return_404_artwork = True
        result = self.client.artwork()
        self.assertIsNone(result)
    
    def test_unreachable_port_raises_connection_error(self):
        """Test that unreachable port raises UrlPlayerConnectionError"""
        client = UrlPlayerClient('localhost', 99999, 'test_token')
        with self.assertRaises(UrlPlayerConnectionError):
            client.health()

class TestRequestHandler(BaseHTTPRequestHandler):
    last_request = None
    return_404_artwork = False
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/v1/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif parsed_path.path == '/api/v1/status':
            if not self.check_auth():
                return
            self.send_response(200)
            self.end_headers()
            response = {
                'status': 'playing',
                'volume': 0.5,
                'current_station': 'test_station',
                'current_track': 'test_track'
            }
            self.wfile.write(json.dumps(response).encode())
        elif parsed_path.path == '/api/v1/stations':
            if not self.check_auth():
                return
            self.send_response(200)
            self.end_headers()
            response = [
                {'id': '1', 'name': 'Station 1'},
                {'id': '2', 'name': 'Station 2'}
            ]
            self.wfile.write(json.dumps(response).encode())
        elif parsed_path.path == '/api/v1/artwork':
            if not self.check_auth():
                return
            # Use the flag to determine if we should return 404
            if TestRequestHandler.return_404_artwork:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'test_artwork_data')
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data.decode('utf-8')) if post_data else {}
        
        TestRequestHandler.last_request = {
            'method': 'POST',
            'path': parsed_path.path,
            'payload': payload
        }
        
        if parsed_path.path == '/api/v1/toggle':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        elif parsed_path.path == '/api/v1/stop':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        elif parsed_path.path == '/api/v1/next':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        elif parsed_path.path == '/api/v1/previous':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        elif parsed_path.path == '/api/v1/play':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        elif parsed_path.path == '/api/v1/volume':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def check_auth(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            self.send_response(401)
            self.end_headers()
            return False
        
        token = auth_header.split(' ')[1]
        if token != 'test_token':
            self.send_response(401)
            self.end_headers()
            return False
            
        return True

if __name__ == '__main__':
    unittest.main()
