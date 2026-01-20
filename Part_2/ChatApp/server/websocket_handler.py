"""
מימוש פרוטוקול WebSocket לפי RFC 6455
כולל: handshake, קידוד/פענוח frames, masking
"""

import hashlib
import base64
import struct

# Magic GUID for WebSocket handshake (RFC 6455)
WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# WebSocket opcodes
OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


def perform_handshake(client_socket, request):
    """
    Perform WebSocket handshake.

    Args:
        client_socket: Client socket
        request: Parsed HTTP request dict

    Returns:
        True if handshake successful, False otherwise
    """
    headers = request.get('headers', {})

    # Get the WebSocket key from client
    websocket_key = headers.get('sec-websocket-key')
    if not websocket_key:
        print("[-] No Sec-WebSocket-Key in request")
        return False

    # Compute accept key: SHA1(key + GUID), then base64 encode
    accept_raw = websocket_key + WEBSOCKET_GUID
    accept_hash = hashlib.sha1(accept_raw.encode()).digest()
    accept_key = base64.b64encode(accept_hash).decode()

    # Build HTTP 101 Switching Protocols response
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key}\r\n"
        "\r\n"
    )

    # Send handshake response
    client_socket.sendall(response.encode())
    print(f"[WS] Handshake complete, accept key: {accept_key[:20]}...")

    return True


def decode_frame(client_socket):
    """
    Decode a WebSocket frame from client.

    Args:
        client_socket: Client socket to read from

    Returns:
        Tuple of (opcode, payload_data) or (None, None) on error
    """
    try:
        # Read first 2 bytes (header)
        header = client_socket.recv(2)
        if len(header) < 2:
            return None, None

        # Parse first byte: FIN + RSV + opcode
        first_byte = header[0]
        fin = (first_byte >> 7) & 1
        opcode = first_byte & 0x0F

        # Parse second byte: MASK + payload length
        second_byte = header[1]
        masked = (second_byte >> 7) & 1
        payload_len = second_byte & 0x7F

        # Handle extended payload length
        if payload_len == 126:
            # Next 2 bytes are length (big-endian)
            ext_len = client_socket.recv(2)
            payload_len = struct.unpack('>H', ext_len)[0]
        elif payload_len == 127:
            # Next 8 bytes are length (big-endian)
            ext_len = client_socket.recv(8)
            payload_len = struct.unpack('>Q', ext_len)[0]

        # Read masking key (4 bytes) if masked
        mask_key = None
        if masked:
            mask_key = client_socket.recv(4)

        # Read payload data
        payload = b''
        remaining = payload_len
        while remaining > 0:
            chunk = client_socket.recv(min(remaining, 4096))
            if not chunk:
                break
            payload += chunk
            remaining -= len(chunk)

        # Unmask payload if masked (client -> server is always masked)
        if masked and mask_key:
            payload = unmask_payload(payload, mask_key)

        return opcode, payload

    except Exception as e:
        print(f"[-] Error decoding frame: {e}")
        return None, None


def unmask_payload(payload, mask_key):
    """
    Unmask WebSocket payload data.

    Args:
        payload: Masked payload bytes
        mask_key: 4-byte masking key

    Returns:
        Unmasked payload bytes
    """
    return bytes([payload[i] ^ mask_key[i % 4] for i in range(len(payload))])


def encode_frame(data, opcode=OPCODE_TEXT, fin=True):
    """
    Encode data into a WebSocket frame for sending to client.
    Server -> Client frames are NOT masked.

    Args:
        data: Payload data (string or bytes)
        opcode: Frame opcode (default: text)
        fin: FIN bit (default: True for single-frame message)

    Returns:
        Encoded frame as bytes
    """
    # Convert string to bytes
    if isinstance(data, str):
        data = data.encode('utf-8')

    # Build frame
    frame = bytearray()

    # First byte: FIN + opcode
    first_byte = (0x80 if fin else 0x00) | opcode
    frame.append(first_byte)

    # Second byte and extended length (no mask for server->client)
    payload_len = len(data)
    if payload_len < 126:
        frame.append(payload_len)
    elif payload_len < 65536:
        frame.append(126)
        frame.extend(struct.pack('>H', payload_len))
    else:
        frame.append(127)
        frame.extend(struct.pack('>Q', payload_len))

    # Add payload
    frame.extend(data)

    return bytes(frame)


def send_message(client_socket, message):
    """
    Send a text message over WebSocket.

    Args:
        client_socket: Client socket
        message: Message string to send
    """
    frame = encode_frame(message, OPCODE_TEXT)
    client_socket.sendall(frame)


def send_close(client_socket, code=1000, reason=""):
    """
    Send a close frame.

    Args:
        client_socket: Client socket
        code: Close status code (default: 1000 Normal Closure)
        reason: Optional close reason string
    """
    payload = struct.pack('>H', code) + reason.encode('utf-8')
    frame = encode_frame(payload, OPCODE_CLOSE)
    try:
        client_socket.sendall(frame)
    except:
        pass  # Connection might already be closed


def handle_websocket_connection(client_socket, request, on_message, on_close):
    """
    Handle a WebSocket connection after handshake.
    Reads frames and calls callbacks.

    Args:
        client_socket: Client socket
        request: Parsed HTTP request
        on_message: Callback(socket, message_str) for text messages
        on_close: Callback(socket) when connection closes
    """
    # Perform handshake
    if not perform_handshake(client_socket, request):
        return

    try:
        while True:
            opcode, payload = decode_frame(client_socket)

            if opcode is None:
                # Connection error
                break

            if opcode == OPCODE_TEXT:
                # Text message
                message = payload.decode('utf-8')
                on_message(client_socket, message)

            elif opcode == OPCODE_CLOSE:
                # Close frame - echo it back
                print("[WS] Close frame received")
                send_close(client_socket)
                break

            elif opcode == OPCODE_PING:
                # Respond to ping with pong
                pong_frame = encode_frame(payload, OPCODE_PONG)
                client_socket.sendall(pong_frame)

            elif opcode == OPCODE_PONG:
                # Pong received - ignore
                pass

    except Exception as e:
        print(f"[-] WebSocket error: {e}")

    finally:
        on_close(client_socket)
