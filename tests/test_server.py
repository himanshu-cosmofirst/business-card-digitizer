import base64
import http.client
import io
import json
import threading
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont
from openpyxl import load_workbook

from server import Handler, MAX_BODY, ThreadingHTTPServer


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


class ApiResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request(method, path, body, headers or {})
            response = connection.getresponse()
            self.assertIn('application/json', response.getheader('Content-Type'))
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def test_health_identifies_the_ocr_backend(self):
        status, data = self.request('GET', '/api/health')
        self.assertEqual(status, 200)
        self.assertTrue(data['ok'])
        self.assertEqual(data['app'], 'business-card-digitizer-v2')

    def test_route_and_method_errors_are_json(self):
        for method, path, expected in [
            ('GET', '/api/missing', 404),
            ('POST', '/api/missing', 404),
            ('GET', '/api/process', 405),
            ('POST', '/api/health', 405),
            ('PUT', '/api/process', 501),
        ]:
            with self.subTest(method=method, path=path):
                status, data = self.request(method, path)
                self.assertEqual(status, expected)
                self.assertFalse(data['ok'])
                self.assertTrue(data['error'])

    def test_bad_uploads_return_a_json_client_error(self):
        for body in ['', '<!doctype html>', 'null', '[]', '{}',
                     '{"data":"%%%"}', '{"data":"data:image/jpeg;base64,"}']:
            with self.subTest(body=body):
                status, data = self.request('POST', '/api/process', body)
                self.assertEqual(status, 400)
                self.assertFalse(data['ok'])

    def test_oversize_request_returns_json(self):
        status, data = self.request('POST', '/api/process', headers={
            'Content-Length': str(MAX_BODY + 1),
        })
        self.assertEqual(status, 413)
        self.assertIn('too large', data['error'])

    def test_upload_with_query_string_reaches_processing(self):
        image = b'image-bytes'
        body = json.dumps({'name': 'IMG_1947 1.jpg', 'data':
                           'data:image/jpeg;base64,' + base64.b64encode(image).decode()})
        with patch('server.process_image', return_value=[{'index': 1}]) as process:
            status, data = self.request('POST', '/api/process?upload=1', body)
        self.assertEqual(status, 200)
        self.assertEqual(data['count'], 1)
        process.assert_called_once_with(image)

    def test_real_jpeg_upload_and_excel_export(self):
        image = Image.new('RGB', (1000, 600), 'white')
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=42)
        for index, text in enumerate(['Jane Doe', 'Example Labs', 'Sales Director',
                                      'jane@example.com', 'www.example.com']):
            draw.text((60, 60 + index * 90), text, fill='black', font=font)
        jpeg = io.BytesIO()
        image.save(jpeg, format='JPEG', quality=95)
        body = json.dumps({'name': 'IMG_1947 1.jpg', 'data':
                           'data:image/jpeg;base64,' + base64.b64encode(jpeg.getvalue()).decode()})
        status, data = self.request('POST', '/api/process', body)
        self.assertEqual(status, 200)
        self.assertEqual(data['count'], 1)
        self.assertNotIn('error', data['cards'][0])
        fields = data['cards'][0]['fields']
        self.assertEqual(fields['email'], 'jane@example.com')
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request('POST', '/api/export', json.dumps({
                'rows': [{**fields, 'sourceImage': 'IMG_1947 1.jpg'}],
            }))
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn('spreadsheetml.sheet', response.getheader('Content-Type'))
            workbook = load_workbook(io.BytesIO(response.read()))
            self.assertEqual(workbook.active['F2'].value, 'jane@example.com')
            self.assertEqual(workbook.active['J2'].value, 'IMG_1947 1.jpg')
        finally:
            connection.close()


if __name__ == '__main__':
    unittest.main()
