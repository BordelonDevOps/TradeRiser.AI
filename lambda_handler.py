import json
import sys
import os
from io import StringIO

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from new_traderiser_platform import app
except ImportError:
    # Fallback to application.py if new_traderiser_platform is not available
    from application import app

def lambda_handler(event, context):
    """
    AWS Lambda handler for the TradeRiser AI Flask application.
    
    This function adapts the Flask application to work with AWS Lambda
    and API Gateway by converting Lambda events to WSGI format.
    """
    
    # Handle different event types
    if 'httpMethod' not in event:
        # Handle direct invocation or other event types
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'message': 'TradeRiser AI Lambda function is running',
                'status': 'healthy'
            })
        }
    
    # Extract request information from Lambda event
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    query_string_parameters = event.get('queryStringParameters') or {}
    headers = event.get('headers') or {}
    body = event.get('body', '')
    
    # Handle base64 encoded body
    if event.get('isBase64Encoded', False) and body:
        import base64
        body = base64.b64decode(body).decode('utf-8')
    
    # Create WSGI environ dictionary
    environ = {
        'REQUEST_METHOD': http_method,
        'PATH_INFO': path,
        'QUERY_STRING': '&'.join([f'{k}={v}' for k, v in query_string_parameters.items()]),
        'CONTENT_TYPE': headers.get('Content-Type', ''),
        'CONTENT_LENGTH': str(len(body)) if body else '0',
        'SERVER_NAME': headers.get('Host', 'localhost'),
        'SERVER_PORT': '443',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': StringIO(body),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add headers to environ
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # Capture response
    response_data = []
    response_status = []
    response_headers = []
    
    def start_response(status, headers, exc_info=None):
        response_status.append(status)
        response_headers.extend(headers)
    
    # Call Flask application
    try:
        with app.app_context():
            app_response = app(environ, start_response)
            response_data = b''.join(app_response).decode('utf-8')
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
    
    # Parse status code
    status_code = int(response_status[0].split()[0]) if response_status else 200
    
    # Convert headers to dict
    headers_dict = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    for header in response_headers:
        headers_dict[header[0]] = header[1]
    
    return {
        'statusCode': status_code,
        'headers': headers_dict,
        'body': response_data
    }