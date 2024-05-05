"""
A basic script to connect, authenticate, and receive messages from an Arctop device.
You must have your api key, server IP, and server port to connect (ip + port are on the app's streaming screen)
"""

import json
import logging
import socket
import struct
import time

logging.basicConfig(level=logging.INFO)

DEBUG_MODE = False  # Set this to True to print all incoming messages

# Initialize values for non-debug mode printing
latest_values = {"enjoyment": 0.0, "focus": 0.0, "heart_rate": 0.0}


def send_auth_command(sock, api_key):
    command = {
        "command": "auth",
        "apiKey": api_key
    }
    send_message(sock, command)


def send_message(sock, message):
    message_encoded = json.dumps(message).encode('utf-8')
    message_length = struct.pack('>H', len(message_encoded))
    sock.sendall(message_length + message_encoded)


def receive_message(sock):
    """Receive a message which is preceded by its length in BIG ENDIAN format."""
    # Read message length
    message_length_bytes = sock.recv(2)
    if not message_length_bytes:
        return None
    message_length = struct.unpack('>H', message_length_bytes)[0]

    # Read the message data
    message_data = sock.recv(message_length)
    message = json.loads(message_data.decode('utf-8'))

    if DEBUG_MODE:
        print(f"Received message: {message}")

    return message


def handle_value_change(message):
    global latest_values
    if message.get("key") in ['enjoyment', 'focus', 'heart_rate']:
        latest_values[message.get("key")] = message.get("value")
        if not DEBUG_MODE:
            print_values()

            """
            THIS IS WHERE YOU CAN ADD YOUR OWN LOGIC TO HANDLE THE VALUES
            FOR EXAMPLE, FEED A DEEP LEARNING MODEL, OR UPDATE A DATABASE OR PLAY A SOUND.            
            """


def handle_auth_failed(message):
    logging.error("Authentication failed. Check API key.")


def handle_session_complete(message):
    logging.info("Session complete. Closing connection.")


COMMAND_HANDLERS = {
    "valueChange": handle_value_change,
    "auth-failed": handle_auth_failed,
    "sessionComplete": handle_session_complete,
}


def handle_message(sock):
    while True:
        message = receive_message(sock)
        if message is None:
            logging.info("Connection closed by server.")
            break

        handler = COMMAND_HANDLERS.get(message.get("command"))
        if handler:
            handler(message)


def print_values():
    print(
        f"Enjoyment [{latest_values['enjoyment']:.2f}]  |  Focus [{latest_values['focus']:.2f}]  |  Heart Rate [{latest_values['heart_rate']:.2f}]")


def connect_to_server(server_ip, server_port, api_key):
    attempt_count = 0
    while attempt_count < 3:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((server_ip, server_port))
                logging.info("Connected to server.")
                send_auth_command(sock, api_key)
                handle_message(sock)
                break
        except socket.error as e:
            logging.error(f"Failed to connect to server: {e}")
            attempt_count += 1
            time.sleep(5)


if __name__ == '__main__':
    SERVER_IP = '192.168.68.116'  # Change to your server's IP
    SERVER_PORT = 38641  # Change to your server's port
    API_KEY = 'YOUR_API_KEY'  # Change to your key
    DEBUG_MODE = input("Enter debug mode for all device msgs? (y/n): ").lower() == 'y'
    if not DEBUG_MODE:
        print_values()
    connect_to_server(SERVER_IP, SERVER_PORT, API_KEY)
