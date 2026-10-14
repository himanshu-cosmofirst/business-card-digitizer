import os

bind = f"{os.environ.get('HOST', '0.0.0.0')}:{int(os.environ.get('PORT', '8000'))}"
workers = 1
worker_class = 'gthread'
threads = 2
timeout = 180
graceful_timeout = 30
accesslog = '-'
errorlog = '-'
