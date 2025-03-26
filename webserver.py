"""
Basic Web Server (CSE 310 - Spring 2025)

This Python script creates a simple HTTP web server that listens for incoming HTTP requests,
processes them, and responds with the requested file if available. If the file does not exist,
the server returns a "404 Not Found" response.

Features:
- Handles one request at a time (single-threaded).
- Supports HTML, text, and image files (JPEG, PNG).
- Responds with a valid HTTP header and content.
- Returns a 404 error if the file is missing.
- Can be accessed via a web browser or curl command.

Usage:
1. Place this script in a directory with some HTML and image files.
2. Run: `python3 webserver.py`
3. Access via a browser: `http://127.0.0.1:6789/yourfile.html`
"""

import socket  # Import socket module to handle network communication
import os      # Import os module to interact with the file system
import mimetypes  # Import mimetypes to determine file content types (MIME types)

# Server Configuration
HOST = '127.0.0.1'  # The server listens on localhost (only accessible from this machine)
PORT = 6789         # The port number clients must use to connect

###############################################################################
# FUNCTION TO HANDLE CLIENT REQUESTS
###############################################################################

def handle_client(client_socket):
    """
    Handles an HTTP request from a client and sends back an HTTP response.

    Steps:
      1. Receive the request from the client.
      2. Extract the requested filename from the request.
      3. If the file exists, read and return the content with a proper HTTP response.
      4. If the file does not exist, return a 404 Not Found response.

    client_socket: The network connection between the server and the client (browser).
    """
    print("\n[DEBUG] Handling new client request...")

    try:
        # Receive the HTTP request from the client (up to 1024 bytes)
        request = client_socket.recv(1024)
        print(f"[DEBUG] Raw request received (bytes): {request}")

        # Decode the request to a human-readable format (UTF-8)
        try:
            request_text = request.decode('utf-8')  # Convert bytes to string
            print(f"[DEBUG] Decoded request text:\n{request_text}")
        except UnicodeDecodeError:
            print("[ERROR] Received non-UTF-8 request. Closing connection.")
            client_socket.close()  # Close connection if request is unreadable
            return

        # Split the request into individual lines
        request_lines = request_text.split("\r\n")

        # Check if the request contains data
        if len(request_lines) == 0:
            print("[ERROR] Received empty request. Ignoring.")
            return  # Ignore empty request

        # Extract the first line (request line) and split it into components
        first_line = request_lines[0].split()  # Example: ["GET", "/index.html", "HTTP/1.1"]

        # Ensure the request line has at least two parts and is a GET request
        if len(first_line) < 2 or first_line[0] != "GET":
            print(f"[ERROR] Invalid request format: {first_line}")
            return  # Ignore invalid requests

        print(f"[DEBUG] Parsed HTTP method: {first_line[0]}")
        print(f"[DEBUG] Requested file: {first_line[1]}")

        # Extract the filename from the request (remove the leading "/")
        filename = first_line[1].lstrip("/")

        # If the client requests "/", assume there is no default index file and return 404
        if filename == "":
            print("[DEBUG] Root '/' requested. No default file specified, returning 404.")
            filename = "nonexistentfile"  # Assign a filename that does not exist

        # Check if the requested file exists
        if os.path.exists(filename) and os.path.isfile(filename):
            print(f"[DEBUG] File found: {filename}")

            # Determine the file's MIME type using the mimetypes module
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or "application/octet-stream"  # Default MIME type
            print(f"[DEBUG] Detected MIME type: {content_type}")

            # Open the file in binary mode and read its content
            with open(filename, "rb") as file:
                file_data = file.read()

            print(f"[DEBUG] File size: {len(file_data)} bytes")

            # Construct the HTTP response header for a successful request (200 OK)
            response_header = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(file_data)}\r\n"
                "Connection: close\r\n\r\n"
            ).encode()

            print("[DEBUG] Sending 200 OK response with file content.")
            client_socket.sendall(response_header + file_data)  # Send the response

        else:
            print(f"[ERROR] File not found: {filename}. Sending 404 response.")

            # Construct and send the 404 Not Found response
            error_response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n"
                "Connection: close\r\n\r\n"
                "<html><body><h1>404 Not Found</h1></body></html>"
            ).encode()

            client_socket.sendall(error_response)  # Send error response to client

    except Exception as e:
        print(f"[ERROR] Exception while handling request: {e}")

    finally:
        print("[DEBUG] Closing client connection.\n")
        client_socket.close()  # Close the client connection

###############################################################################
# FUNCTION TO START THE WEB SERVER
###############################################################################

def start_server():
    """
    Initializes and starts the web server.

    - Creates a TCP socket.
    - Binds it to the specified HOST and PORT.
    - Listens for incoming connections.
    - Accepts client connections and passes them to the handle_client() function.
    """
    print("[DEBUG] Starting web server...")

    # Create a TCP socket using IPv4 (AF_INET) and TCP (SOCK_STREAM)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow the server to reuse the same address to avoid "Address already in use" error
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to the specified HOST and PORT
    server_socket.bind((HOST, PORT))

    # Start listening for incoming connections (maximum of 5 queued connections)
    server_socket.listen(5)
    print(f"[DEBUG] Server running on http://{HOST}:{PORT}/")
    print("[DEBUG] Waiting for client connections...\n")

    # Infinite loop to continuously accept and handle client requests
    while True:
        # Accept a new client connection
        client_socket, client_address = server_socket.accept()
        print(f"[DEBUG] Connection established with {client_address}")
        handle_client(client_socket)  # Process the client request

###############################################################################
# MAIN EXECUTION: START THE SERVER
###############################################################################

if __name__ == "__main__":
    start_server()  # Run the server
