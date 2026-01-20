"""
ניהול thread-safe של לקוחות מחוברים
כולל: הוספה, הסרה, ושידור הודעות לכולם
"""

import threading
from websocket_handler import send_message

# Thread-safe client storage
clients_lock = threading.Lock()
connected_clients = {}  # {socket: {"username": str}}


def add_client(client_socket, username):
    """
    Add a new client to the connected clients list.

    Args:
        client_socket: Client socket object
        username: Client's username
    """
    with clients_lock:
        connected_clients[client_socket] = {"username": username}
        count = len(connected_clients)

    print(f"[+] Client added: {username} (Total: {count})")


def remove_client(client_socket):
    """
    Remove a client from the connected clients list.

    Args:
        client_socket: Client socket to remove

    Returns:
        Username of removed client, or None if not found
    """
    username = None
    with clients_lock:
        if client_socket in connected_clients:
            username = connected_clients[client_socket]["username"]
            del connected_clients[client_socket]
            count = len(connected_clients)
            print(f"[-] Client removed: {username} (Total: {count})")

    return username


def get_username(client_socket):
    """
    Get the username for a client socket.

    Args:
        client_socket: Client socket

    Returns:
        Username string, or None if not found
    """
    with clients_lock:
        client_info = connected_clients.get(client_socket)
        return client_info["username"] if client_info else None


def get_all_usernames():
    """
    Get list of all connected usernames.

    Returns:
        List of username strings
    """
    with clients_lock:
        return [info["username"] for info in connected_clients.values()]


def get_client_count():
    """
    Get the number of connected clients.

    Returns:
        Integer count of connected clients
    """
    with clients_lock:
        return len(connected_clients)


def broadcast(message, exclude_socket=None):
    """
    Send a message to all connected clients.

    Args:
        message: Message string to send
        exclude_socket: Optional socket to exclude from broadcast
    """
    with clients_lock:
        # Create list of sockets to avoid modifying dict during iteration
        sockets = list(connected_clients.keys())

    failed_sockets = []

    for sock in sockets:
        if sock == exclude_socket:
            continue

        try:
            send_message(sock, message)
        except Exception as e:
            print(f"[-] Failed to send to client: {e}")
            failed_sockets.append(sock)

    # Clean up failed connections
    for sock in failed_sockets:
        remove_client(sock)
        try:
            sock.close()
        except:
            pass


def broadcast_system_message(message):
    """
    Broadcast a system message to all clients.
    Uses format: "SYSTEM|message|timestamp"

    Args:
        message: System message text
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted = f"SYSTEM|{message}|{timestamp}"
    broadcast(formatted)


def broadcast_user_list():
    """
    Broadcast the current user list to all clients.
    Uses format: "USERLIST|count|user1,user2,user3"
    """
    usernames = get_all_usernames()
    count = len(usernames)
    user_list = ",".join(usernames) if usernames else ""
    formatted = f"USERLIST|{count}|{user_list}"
    broadcast(formatted)
