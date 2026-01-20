"""
מנתח בקשות HTTP ומגיש קבצים סטטיים (HTML, CSS, JS)
"""

import os

# Path to client files (relative to this file's directory)
CLIENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'client')

# Content types for static files
CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.ico': 'image/x-icon',
}


def parse_request(data):
    """
    Parse raw HTTP request data into components.

    Args:
        data: Raw bytes from socket

    Returns:
        dict with 'method', 'path', 'version', 'headers'
        or None if parsing fails
    """
    try:
        # Decode bytes to string
        text = data.decode('utf-8')

        # Split into lines
        lines = text.split('\r\n')
        if not lines:
            return None

        # Parse request line: "GET /path HTTP/1.1"
        request_line = lines[0].split(' ')
        if len(request_line) != 3:
            return None

        method, path, version = request_line

        # Parse headers into dictionary
        headers = {}
        for line in lines[1:]:
            if not line:  # Empty line marks end of headers
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        return {
            'method': method,
            'path': path,
            'version': version,
            'headers': headers
        }

    except Exception as e:
        print(f"[-] Error parsing request: {e}")
        return None


def build_response(status_code, status_text, content_type, body):
    """
    Build a complete HTTP response.

    Args:
        status_code: HTTP status code (e.g., 200)
        status_text: HTTP status text (e.g., "OK")
        content_type: MIME type for Content-Type header
        body: Response body as bytes

    Returns:
        Complete HTTP response as bytes
    """
    # Build response headers
    headers = f"HTTP/1.1 {status_code} {status_text}\r\n"
    headers += f"Content-Type: {content_type}\r\n"
    headers += f"Content-Length: {len(body)}\r\n"
    headers += "Connection: close\r\n"
    headers += "\r\n"

    # Combine headers and body
    return headers.encode('utf-8') + body


def serve_static_file(path):
    """
    Serve a static file from the client directory.

    Args:
        path: URL path (e.g., "/index.html")

    Returns:
        HTTP response as bytes
    """
    # Default to index.html for root path
    if path == '/':
        path = '/index.html'

    # Security: prevent directory traversal
    if '..' in path:
        return build_404()

    # Build file path
    file_path = os.path.normpath(os.path.join(CLIENT_DIR, path.lstrip('/')))

    # Verify file is within client directory
    if not file_path.startswith(os.path.normpath(CLIENT_DIR)):
        return build_404()

    # Check if file exists
    if not os.path.isfile(file_path):
        return build_404()

    # Determine content type
    _, ext = os.path.splitext(file_path)
    content_type = CONTENT_TYPES.get(ext, 'application/octet-stream')

    # Read and serve file
    try:
        with open(file_path, 'rb') as f:
            body = f.read()
        return build_response(200, 'OK', content_type, body)
    except Exception as e:
        print(f"[-] Error reading file {file_path}: {e}")
        return build_500()


def build_404():
    """Build a 404 Not Found response."""
    body = b"<html><body><h1>404 Not Found</h1></body></html>"
    return build_response(404, 'Not Found', 'text/html; charset=utf-8', body)


def build_500():
    """Build a 500 Internal Server Error response."""
    body = b"<html><body><h1>500 Internal Server Error</h1></body></html>"
    return build_response(500, 'Internal Server Error', 'text/html; charset=utf-8', body)


def is_websocket_upgrade(request):
    """
    Check if this is a WebSocket upgrade request.

    Args:
        request: Parsed request dictionary

    Returns:
        True if this is a WebSocket upgrade request
    """
    if not request:
        return False

    headers = request.get('headers', {})

    # Check for WebSocket upgrade headers
    upgrade = headers.get('upgrade', '').lower()
    connection = headers.get('connection', '').lower()

    return 'websocket' in upgrade and 'upgrade' in connection


def handle_http(client_socket, data):
    """
    Handle an HTTP request and send response.

    Args:
        client_socket: Client socket to send response to
        data: Raw request data

    Returns:
        Parsed request dict (for WebSocket detection)
    """
    # Parse the request
    request = parse_request(data)

    if not request:
        client_socket.sendall(build_404())
        return None

    print(f"[HTTP] {request['method']} {request['path']}")

    # Check if this is a WebSocket upgrade
    if is_websocket_upgrade(request):
        # Don't send HTTP response - let WebSocket handler take over
        return request

    # Serve static file
    response = serve_static_file(request['path'])
    client_socket.sendall(response)

    return request
