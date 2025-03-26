"""
Basic HTTP Proxy Server (CSE 310 - Spring 2025)

This Python script implements a simple HTTP proxy server that intercepts HTTP GET requests
from clients (web browsers), forwards them to the target web server, retrieves the response,
and returns it to the client. The proxy also caches responses to improve efficiency.

Features:
- Intercepts and forwards HTTP GET requests.
- Caches responses to reduce redundant network requests.
- Handles only HTTP (not HTTPS) requests.
- Works with web browsers or command-line tools like `curl` with proxy settings.

Limitations:
- Does not support HTTPS (CONNECT requests will be rejected).
- Single-threaded: can handle only one request at a time.
- Only works for HTTP requests on port 80.

Usage:
1. Run: `python3 proxyserver.py`
2. Configure your web browser to use `127.0.0.1:8888` as the proxy.
3. Visit a website using HTTP (e.g., `http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file2.html`).
4. Cached responses will be served if available.
5. To force a fresh request from the server instead of using cached content:
   - **Google Chrome:** Press `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac).
   - **Firefox:** Press `Ctrl + F5` (Windows/Linux) or `Cmd + Shift + R` (Mac).
   - **Edge:** Press `Ctrl + Shift + R`.
   - **Safari:** Press `Cmd + Option + R`.
   - **Using curl:** Run `curl -x http://127.0.0.1:8888 -H 'Cache-Control: no-cache' http://example.com`
"""

import socket  # Networking module
import os      # File system module

###############################################################################
# CONFIGURATION
###############################################################################

HOST = '127.0.0.1'   # Proxy listens on localhost
PORT = 8888          # Proxy port
CACHE_DIR = 'cache'  # Directory for cached responses

# Ensure cache directory exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
    print(f"[DEBUG] Created cache directory '{CACHE_DIR}'.")

###############################################################################
# FUNCTION TO CHECK CACHED RESPONSES
###############################################################################

def get_cached_content(cache_key):
    """
    Checks if the requested web page is stored in the cache.
    Returns the cached data if found; otherwise, returns None.
    """
    cache_path = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(cache_path) and os.path.isfile(cache_path):
        print(f"[DEBUG] Cache HIT for: {cache_key}")
        with open(cache_path, "rb") as cached_file:
            return cached_file.read()
    print(f"[DEBUG] Cache MISS for: {cache_key}")
    return None

###############################################################################
# FUNCTION TO SAVE CONTENT TO CACHE
###############################################################################

def cache_content(cache_key, content):
    """
    Stores the web page data in a file within the cache directory.
    """
    cache_path = os.path.join(CACHE_DIR, cache_key)
    with open(cache_path, "wb") as f:
        f.write(content)
    print(f"[DEBUG] Cached content at: {cache_path}")

###############################################################################
# FUNCTION TO HANDLE CLIENT REQUESTS
###############################################################################

def handle_client(client_socket):
    """
    Processes requests from a web browser:
      1) Reads the HTTP request and extracts the URL.
      2) If the resource is cached, sends it back immediately.
      3) Otherwise, fetches it from the remote server, caches it, and returns it.
    Only supports HTTP GET requests.
    """
    try:
        print("[DEBUG] Waiting to receive client request...")
        request_data = client_socket.recv(4096)

        if not request_data:
            print("[ERROR] Received empty request data.")
            return

        # Decode the received request to a string
        request_text = request_data.decode('utf-8', errors='ignore')
        print(f"[DEBUG] Decoded request:\n{request_text}")

        # Extract the first line (e.g., "GET http://example.com/page.html HTTP/1.1")
        lines = request_text.split('\r\n')
        if len(lines) < 1 or not lines[0]:
            print("[ERROR] Malformed request: No request line found.")
            return

        request_line = lines[0].split()
        if len(request_line) < 2:
            print(f"[ERROR] Invalid request line: {request_line}")
            return

        method = request_line[0].upper()  # e.g., GET
        url = request_line[1]            # e.g., http://example.com/page.html
        print(f"[DEBUG] Parsed request - Method: {method}, URL: {url}")

        # Only supports GET
        if method != 'GET':
            print(f"[ERROR] Only GET is supported. Received method: {method}")
            return

        # Check for HTTPS
        if url.startswith("https://"):
            print("[ERROR] HTTPS requests are not supported by this proxy.")
            return

        # If the URL is relative (like "/index.html"), we can't handle it in this proxy
        if url.startswith('/'):
            print("[ERROR] Relative URL detected, cannot process request.")
            return

        # Strip "http://"
        if url.startswith("http://"):
            url = url[len("http://"):]

        # Split into hostname and path
        parts = url.split('/', 1)
        hostname = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else "/"

        print(f"[DEBUG] Extracted hostname: {hostname}, Path: {path}")

        # Create a unique cache key
        cache_key = url.replace('/', '_')

        # Check if content is cached
        cached_data = get_cached_content(cache_key)
        if cached_data:
            print(f"[DEBUG] Serving cached content for: {url}")
            client_socket.sendall(cached_data)
            return

        # Otherwise, fetch from the web server
        print(f"[DEBUG] No cache found, forwarding request to {hostname}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.settimeout(10)  # 10-second timeout
            server_sock.connect((hostname, 80))

            forward_msg = (
                f"GET {path} HTTP/1.0\r\n"
                f"Host: {hostname}\r\n"
                "User-Agent: CSE310-Proxy\r\n"
                "Accept: */*\r\n"
                "Accept-Encoding: identity\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            server_sock.sendall(forward_msg.encode('utf-8'))
            print("[DEBUG] Request forwarded to remote server.")

            response_data = server_sock.recv(4096)  # Receive response in a single call

        # If the server responded with nothing, treat it as a 404
        if not response_data:
            print(f"[ERROR] Empty response received from {hostname}")
            return

        # Cache the response
        cache_content(cache_key, response_data)

        # Send the server's response back to the client
        print(f"[DEBUG] Received {len(response_data)} bytes from {hostname}, sending to client...")
        client_socket.sendall(response_data)

    except socket.timeout:
        print("[ERROR] Connection timed out while handling request.")
    except Exception as e:
        print(f"[ERROR] Exception while handling request: {e}")
    finally:
        client_socket.close()
        print("[DEBUG] Closed client connection.")

###############################################################################
# FUNCTION TO START THE PROXY SERVER
###############################################################################

def start_proxy_server():
    """
    Starts the proxy server on the specified HOST and PORT.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_sock:
        proxy_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy_sock.bind((HOST, PORT))
        proxy_sock.listen(5)
        print(f"[INFO] Proxy server listening on http://{HOST}:{PORT}")

        while True:
            client_conn, client_addr = proxy_sock.accept()
            print(f"[INFO] Connection established with {client_addr}")
            handle_client(client_conn)

###############################################################################
# MAIN EXECUTION: START THE SERVER
###############################################################################

if __name__ == "__main__":
    start_proxy_server()
