from flask_app import app
import serverless_wsgi

def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)