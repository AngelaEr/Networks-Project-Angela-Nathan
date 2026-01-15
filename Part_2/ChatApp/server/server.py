"""
שרת צ'אט - Chat Server
Group_AN - פרויקט גמר ברשתות תקשורת מחשבים

שרת TCP שמטפל בבקשות HTTP (קבצים סטטיים) וחיבורי WebSocket (צ'אט בזמן אמת)
משתמש בספריות מובנות בלבד: socket, threading, hashlib, base64, struct
"""

import socket
import threading

from http_handler import handle_http, is_websocket_upgrade
from websocket_handler import handle_websocket_connection
from client_manager import (
    add_client,
    remove_client,
    broadcast,
    broadcast_system_message,
    broadcast_user_list,
    get_client_count
)

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 10000


def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "localhost"


def on_message(client_socket, message):
    """
    Handle incoming WebSocket message.
    Message format: "USERNAME|MESSAGE|TIMESTAMP"
    """
    print(f"[MSG] {message}")

    # Parse message parts
    parts = message.split('|')
    if len(parts) < 3:
        return

    username = parts[0]
    msg_text = parts[1]
    timestamp = parts[2]

    # Handle special commands
    if msg_text == 'JOIN':
        # Register client with username
        add_client(client_socket, username)
        # Broadcast join notification
        broadcast_system_message(f"{username} joined the chat")
        # Broadcast updated user list to all clients
        broadcast_user_list()
        return

    if msg_text == 'LEAVE':
        # Handled in on_close
        return

    # Regular message - broadcast to all clients
    broadcast(message)


def on_close(client_socket):
    """Handle WebSocket connection close."""
    username = remove_client(client_socket)
    if username:
        broadcast_system_message(f"{username} left the chat")
        # Broadcast updated user list to all clients
        broadcast_user_list()


def handle_client(client_socket, address):
    """Handle a single client connection."""
    print(f"[+] New connection from {address}")

    try:
        # Read raw data from client
        data = client_socket.recv(4096)
        if not data:
            return

        # Handle HTTP request (static files or WebSocket upgrade detection)
        request = handle_http(client_socket, data)

        # If this is a WebSocket upgrade request, hand off to WebSocket handler
        if request and is_websocket_upgrade(request):
            print(f"[WS] WebSocket upgrade from {address}")
            # Handle WebSocket connection (blocking until closed)
            handle_websocket_connection(
                client_socket,
                request,
                on_message=on_message,
                on_close=on_close
            )
            # Don't close socket here - it's handled in the WebSocket handler
            return

    except Exception as e:
        print(f"[-] Error handling {address}: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass
        print(f"[-] Connection closed: {address}")


def main():
    """Main server loop - accepts connections and spawns handler threads."""
    # Create TCP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow port reuse (helps when restarting server)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to address and port
    server.bind((HOST, PORT))

    # Start listening (backlog of 5 connections)
    server.listen(5)

    local_ip = get_local_ip()
    print(f"[*] Chat Server started on {HOST}:{PORT}")
    print(f"[*] Open: http://{local_ip}:{PORT}")
    print("[*] Press Ctrl+C to stop")
    print("=" * 40)

    try:
        while True:
            # Accept new connection
            client_socket, address = server.accept()

            # Handle in new thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address)
            )
            client_thread.daemon = True  # Thread dies when main thread dies
            client_thread.start()

    except KeyboardInterrupt:
        print("\n[*] Server shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    main()
