## Simple Web Server & HTTP Proxy Server

## Table of Contents

1. [Introduction](#introduction)
2. [Files Included](#files-included)
3. [Part A: Web Server](#part-a-web-server)
    - [How It Works](#how-it-works)
    - [How to Run](#how-to-run)
    - [Testing the Web Server](#testing-the-web-server)
4. [Part B: Proxy Server](#part-b-proxy-server)
    - [How It Works](#how-it-works-1)
    - [How to Run](#how-to-run-1)
    - [Testing the Proxy Server](#testing-the-proxy-server)
    - [Clearing Cache](#clearing-cache)
5. [Libraries Used](#libraries-used)

---

## Introduction

This project consists of implementing:

1. A simple **web server** that serves files over HTTP (Part A).
2. A **proxy server** that forwards HTTP requests and caches responses (Part B).

Both programs use **Python socket programming** without external web frameworks (e.g., Flask is not used).

---

## Files Included

- `webserver.py`  → Web server implementation (Part A)
- `proxyserver.py` → Proxy server implementation (Part B)
- `clients_screenshots.pdf` → Screenshots of successful test cases
- `README.md` → This documentation
- Example test files:
    - `HelloWorld.html` → Test file for the web server
    - Sample image files (`.png`, `.jpeg`) for additional testing

---

## Part A: Web Server

### How It Works

- The web server listens on **localhost (127.0.0.1) at port 6789**.
- It accepts incoming HTTP GET requests and serves **HTML, text, and image files** from the same directory.
- If a requested file is **found**, it responds with a **200 OK** status and the file content.
- If the file is **not found**, it returns a **404 Not Found** error with a simple HTML response.

### How to Run

1. Place `webserver.py` in a directory containing `HelloWorld.html` and other test files.
2. Run the server:
   ```sh
   python3 webserver.py
   ```
3. The server will start and listen on **http://127.0.0.1:6789**.

### Testing the Web Server

- Open a web browser and go to:
  ```
  http://127.0.0.1:6789/HelloWorld.html
  ```
  The page should load successfully if the file exists.
- If the file is missing, you will see a **404 Not Found** error.
- You can also use `curl`:
  ```sh
  curl -i http://127.0.0.1:6789/HelloWorld.html
  ```
  This should return an HTTP response with **200 OK** and the file content.

---

## Part B: Proxy Server

### How It Works

- The proxy server listens on **localhost (127.0.0.1) at port 8888**.
- It **intercepts and forwards HTTP GET requests** to the destination server.
- Responses from servers are **cached** in a local `cache/` directory.
- If a requested page is already cached, the proxy **serves it from cache** instead of requesting it again.

### How to Run

1. Run the proxy server:
   ```sh
   python3 proxyserver.py
   ```
2. Configure your web browser to **use a proxy**:
    - **Proxy Address:** `127.0.0.1`
    - **Proxy Port:** `8888`
    - **Ensure HTTPS proxying is disabled** (this proxy only supports HTTP).
3. Open a browser and visit:
   ```
   http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file2.html
   http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file3.html
   http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file4.html
   http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file5.html
   ```
   The proxy will fetch and cache the page.

### Testing the Proxy Server

- **Basic Test**  
  Run curl for any of the supported URLs or just visit these sites again:
  ```sh
  curl -x http://127.0.0.1:8888 http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file2.html
  curl -x http://127.0.0.1:8888 http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file3.html
  curl -x http://127.0.0.1:8888 http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file4.html
  curl -x http://127.0.0.1:8888 http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file5.html
  ```
  Each command should return the requested webpage. If it is not going through your proxy, you may need to hard refresh
  your browser to refresh your browsers cache. This is explained right below.

- **Checking Cache**
    - Test caching by running the curl commands multiple times
    - Verify that subsequent requests are faster (indicating cache usage)
    - Each URL will have its own cache entry:
        - `gaia.cs.umass.edu_wireshark-labs_HTTP-wireshark-file1`
        - `gaia.cs.umass.edu_wireshark-labs_HTTP-wireshark-file2`
        - `gaia.cs.umass.edu_wireshark-labs_HTTP-wireshark-file3`
        - `gaia.cs.umass.edu_wireshark-labs_HTTP-wireshark-file4`

  After the first request, the proxy should serve subsequent requests from the local cache directory.

### Clearing Cache

If you want to force the proxy to **fetch a fresh copy**, use:

- **Google Chrome:** `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- **Firefox:** `Ctrl + F5` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- **Edge:** `Ctrl + Shift + R`
- **Safari:** `Cmd + Option + R`
- **Using curl:**
  ```sh
  curl -x http://127.0.0.1:8888 -H 'Cache-Control: no-cache' http://example.com
  ```
  This will **bypass the browser's cache**.

## Libraries Used

**Only standard Python libraries**, and the following were used:

- `socket` → To create TCP connections for both the web server and proxy server.
- `os` → To handle file operations for caching and file serving.
- `mimetypes` → To determine the correct MIME type for HTTP responses.

No external libraries (like Flask) were used.

## Final Notes

- **Troubleshooting Proxy Cache:** If you encounter cache-related issues, delete the `cache/` directory and restart the
  proxy server.
- **Browser Caching Bypass:** To ensure your proxy server is actually processing requests, use a hard refresh:
    - **Google Chrome:** `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
    - **Firefox:** `Ctrl + F5` (Windows/Linux) or `Cmd + Shift + R` (Mac)
    - **Microsoft Edge:** `Ctrl + Shift + R`
    - **Safari:** `Cmd + Option + R`

  A hard refresh forces the browser to bypass its local cache and request the page directly through your proxy server.

**Prepared by: [Fardin Iqbal]**
