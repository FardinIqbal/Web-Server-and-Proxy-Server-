# HTTP Server & Proxy

HTTP web server and caching proxy built from scratch with raw sockets. No external libraries, no frameworks, no HTTP parsers — just Python's standard `socket` module and hand-rolled HTTP/1.1 parsing.

- 2 servers: origin web server + forwarding caching proxy
- 0 external dependencies (standard library only: `socket`, `os`, `mimetypes`)
- ~250 LOC across both programs
- Feb - Mar 2025 | CSE 310, Stony Brook University

---

## What it is

Two cooperating Python programs that implement the HTTP/1.1 request/response cycle at the socket layer:

1. **`webserver.py`** — origin server. Listens on `127.0.0.1:6789`, parses incoming `GET` requests, resolves paths against the working directory, detects MIME types, and streams file bytes back with a valid HTTP response. Returns `404 Not Found` for missing files.

2. **`proxyserver.py`** — forwarding HTTP proxy with on-disk cache. Listens on `127.0.0.1:8888`, accepts absolute-URI `GET` requests from a configured client, extracts hostname and path, opens a new TCP socket to the origin on port 80, forwards the request, caches the response to `cache/`, and returns it. Subsequent requests for the same URL are served from cache without touching the network.

Everything lives below the `http.server` / `urllib` abstractions. Request lines are tokenized by hand. Response headers are concatenated strings. Sockets are opened, bound, listened, accepted, and closed explicitly.

---

## Key features

### Raw socket programming
- `socket.AF_INET` + `socket.SOCK_STREAM` (TCP/IPv4)
- `SO_REUSEADDR` to avoid `Address already in use` on restart
- Explicit `bind` / `listen(5)` / `accept` loop
- `recv` with fixed buffer (1024 B for server, 4096 B for proxy)
- `sendall` for complete response delivery
- `settimeout(10)` on upstream connections to prevent hangs

### HTTP/1.1 parsing (hand-rolled)
- Split request on `\r\n`, tokenize request line into method + URI + version
- Validate method is `GET` before processing
- Strip `http://` scheme, split host from path on first `/`
- Reject HTTPS and relative URIs (proxy)
- Construct response headers as formatted strings with `Content-Type`, `Content-Length`, `Connection: close`

### MIME type detection
- `mimetypes.guess_type` maps extensions to types (HTML, text, PNG, JPEG)
- Falls back to `application/octet-stream` for unknown types
- Binary-safe file reads (`rb`) for images and binary assets

### Proxy cache
- Cache key derived from URL with `/` replaced by `_` (e.g. `gaia.cs.umass.edu_wireshark-labs_HTTP-wireshark-file2.html`)
- `cache/` directory created on startup if missing
- Cache HIT: read from disk, send directly to client, skip upstream fetch
- Cache MISS: fetch from origin, persist raw bytes, forward to client
- Cache bypass via `Cache-Control: no-cache` header or browser hard refresh

### Upstream forwarding
- Opens fresh TCP connection per request (HTTP/1.0, `Connection: close`)
- Rewrites request: `GET <path> HTTP/1.0\r\nHost: <hostname>\r\n...`
- Sets `Accept-Encoding: identity` to prevent compressed responses the proxy cannot decode
- Custom `User-Agent: CSE310-Proxy`

---

## Build & run

Requires Python 3. No dependencies to install.

### Start the web server

```sh
python3 webserver.py
# Listening on http://127.0.0.1:6789/
```

Fetch a file:

```sh
curl -i http://127.0.0.1:6789/HelloWorld.html
curl -i http://127.0.0.1:6789/png.png -o out.png
```

Missing file returns `404 Not Found` with an HTML body.

### Start the proxy server

```sh
python3 proxyserver.py
# Proxy server listening on http://127.0.0.1:8888
```

### Route traffic through the proxy

**curl:**

```sh
curl -x http://127.0.0.1:8888 http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file2.html
curl -x http://127.0.0.1:8888 http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file3.html
```

**Browser:** configure HTTP proxy = `127.0.0.1`, port = `8888`, disable HTTPS proxying.

First request hits the origin and populates `cache/`. Subsequent requests for the same URL are served from cache (check logs for `Cache HIT`).

### Force a fresh fetch

```sh
curl -x http://127.0.0.1:8888 -H 'Cache-Control: no-cache' http://example.com
```

Or delete `cache/` and restart the proxy.

---

## Architecture

```
Client (curl / browser)
   |
   |  HTTP/1.1 GET
   v
+--------------------+         +----------------------+
|  webserver.py      |         |  proxyserver.py      |
|  127.0.0.1:6789    |         |  127.0.0.1:8888      |
|                    |         |                      |
|  recv -> parse ->  |         |  recv -> parse ->    |
|  resolve file ->   |         |  cache lookup ->     |
|  mimetype ->       |         |    HIT: serve cached |
|  200 OK + bytes    |         |    MISS: forward ->  |
|   (or 404)         |         |      connect :80 ->  |
|                    |         |      recv -> cache  -|----> origin
+--------------------+         +----------------------+       (port 80)
```

### Request lifecycle (web server)

1. `accept()` returns new client socket
2. `recv(1024)` pulls request bytes
3. Decode UTF-8, split on `\r\n`, tokenize first line
4. Validate `GET`, extract filename, strip leading `/`
5. `os.path.exists` + `os.path.isfile` check
6. Read file in binary mode, detect MIME, build response header
7. `sendall(header + body)`
8. Close socket

### Request lifecycle (proxy)

1. `accept()` returns new client socket
2. `recv(4096)` pulls absolute-URI request
3. Validate method, reject HTTPS and relative URIs
4. Split URL into hostname + path, build cache key
5. **Cache HIT:** read bytes from `cache/<key>`, send to client, done
6. **Cache MISS:** open socket to `(hostname, 80)`, forward rewritten request, `recv(4096)`, write bytes to `cache/<key>`, send to client
7. Close both sockets

### Concurrency model

Single-threaded, one request at a time. The accept loop is synchronous — no threading, no `select`, no async. Sufficient for the assignment's scope (local testing, sequential client requests).

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3 |
| Networking | `socket` (standard library) |
| File I/O | `os` (standard library) |
| MIME detection | `mimetypes` (standard library) |
| External dependencies | None |
| HTTP parser | Hand-rolled string splitting |
| Cache storage | Flat files in `cache/` directory |

No Flask, no `http.server`, no `urllib`, no `requests`, no `aiohttp`.

---

## Files

- `webserver.py` — Part A: origin HTTP server (176 lines)
- `proxyserver.py` — Part B: caching HTTP proxy (218 lines)
- `HelloWorld.html` — test fixture for the web server
- `png.png`, `jpeg.jpg` — binary fixtures for MIME/content-length testing
- `clients_screenshots.pdf` — test case evidence

---

## Academic context

Built for **CSE 310: Computer Networks** at Stony Brook University (Spring 2025). The assignment required implementing the HTTP request/response cycle without any HTTP abstraction libraries — the point was to demonstrate understanding of:

- TCP socket lifecycle (`socket` -> `bind` -> `listen` -> `accept` -> `recv`/`send` -> `close`)
- HTTP/1.1 wire format (request line, headers, CRLF delimiters, status codes, `Content-Length`)
- Proxy semantics (absolute URI in request line, `Host` header rewriting, upstream connection handling)
- Web cache design (key derivation, hit/miss logic, persistence)

Validated against browser traffic (Chrome, Firefox) and `curl` with `-x` proxy flag. Upstream targets included `gaia.cs.umass.edu/wireshark-labs/` — the same HTTP-only pages used in Kurose & Ross Wireshark labs.

---

## License

MIT. See course materials for assignment specification.

Prepared by Fardin Iqbal.
