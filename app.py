"""Hosted HTTP entry point; the OCR implementation stays in server.py."""
import base64
from functools import lru_cache
import hmac
import io
import os
import threading

from flask import Flask, jsonify, request, send_file
from werkzeug.exceptions import HTTPException

from server import MAX_BODY, ROOT, export_xlsx, process_image, pytesseract


@lru_cache(maxsize=1)
def ocr_version():
    return str(pytesseract.get_tesseract_version())


def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(
        MAX_CONTENT_LENGTH=MAX_BODY,
        APP_USERNAME=os.environ.get('APP_USERNAME', 'admin'),
        APP_PASSWORD=os.environ.get('APP_PASSWORD', ''),
    )
    if config:
        app.config.update(config)
    processing = threading.BoundedSemaphore(1)

    @app.before_request
    def authenticate():
        password = app.config['APP_PASSWORD']
        # Render's readiness check needs a public endpoint without uploaded data.
        if not password or request.path == '/api/health':
            return None
        credentials = request.authorization
        valid = credentials is not None and credentials.type == 'basic'
        valid = valid and hmac.compare_digest((credentials.username or '').encode(), app.config['APP_USERNAME'].encode())
        valid = valid and hmac.compare_digest((credentials.password or '').encode(), password.encode())
        if not valid:
            response = jsonify(ok=False, error='Sign in to use the Business Card Digitizer.')
            response.status_code = 401
            response.headers['WWW-Authenticate'] = 'Basic realm="Business Card Digitizer", charset="UTF-8"'
            return response

    @app.after_request
    def response_headers(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            message = error.description
            if error.code == 413:
                message = 'Image upload is too large. Choose a smaller photo (under 22 MB).'
            response = error.get_response()
            response.data = app.json.dumps({'ok': False, 'error': message})
            response.content_type = 'application/json'
            return response
        return error

    @app.errorhandler(ValueError)
    def invalid_input(error):
        return jsonify(ok=False, error=str(error)), 400

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception('Request failed')
        return jsonify(ok=False, error='The OCR server could not complete this request. Please try again.'), 500

    def json_object():
        payload = request.get_json()
        if not isinstance(payload, dict):
            raise ValueError('Expected a JSON object.')
        return payload

    @app.get('/')
    @app.get('/index.html')
    def index():
        return send_file(os.path.join(ROOT, 'index.html'))

    @app.get('/api/health')
    def health():
        try:
            version = ocr_version()
        except Exception:
            return jsonify(ok=False, error='Tesseract OCR is unavailable.'), 503
        return jsonify(ok=True, app='business-card-digitizer-v2',
                       ocr=f'Tesseract {version} + OpenCV', multiCard=True)

    @app.post('/api/process')
    def process():
        payload = json_object()
        source = payload.get('data', '')
        if not isinstance(source, str) or not source:
            raise ValueError('No image data was supplied.')
        raw = base64.b64decode(source.split(',', 1)[-1], validate=True)
        if not raw:
            raise ValueError('No image data was supplied.')
        if not processing.acquire(blocking=False):
            return jsonify(ok=False, error='Another photo is being processed. Please try again shortly.'), 503
        try:
            cards = process_image(raw)
            return jsonify(ok=True, count=len(cards), cards=cards)
        finally:
            processing.release()

    @app.post('/api/export')
    def export():
        rows = json_object().get('rows', [])
        if not rows:
            raise ValueError('No confirmed cards to export.')
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError('Expected a list of cards to export.')
        return send_file(io.BytesIO(export_xlsx(rows)), as_attachment=True,
                         download_name='business-cards.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    return app


app = create_app()
