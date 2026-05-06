# Architectural Decision Records

Each entry documents a non-obvious engineering choice, its alternatives, and why I picked what I picked.

---

## ADR 1: Single-threaded sequential request handling

**Status:** accepted

**Context:**
Each `accept()` returns one client socket. The server must handle that client's request before moving to the next. Two options:

1. **Sequential** (this design): finish handling client N before calling `accept()` for client N+1.
2. **Threaded**: spawn a thread per connection, handle them concurrently.
3. **Async**: use `asyncio` or `selectors` to multiplex in one thread.

**Decision:**
Sequential.

**Consequences:**

- Pro: simplest possible code. No thread synchronization, no event loop, no callbacks.
- Pro: easy to reason about. One request in flight at a time.
- Con: one slow client blocks all others. A client that opens a connection and never sends bytes hangs the server.
- Con: cannot scale beyond one CPU.

For an educational exercise focused on HTTP, sequential is the right scope. Adding threading would obscure the protocol behind synchronization concerns. A production server would use a thread pool or `asyncio`.

---

## ADR 2: HTTP/1.0 instead of HTTP/1.1

**Status:** accepted

**Context:**
HTTP/1.1 is the universally-supported version. HTTP/1.0 is older and simpler. Two options:

1. **HTTP/1.0** (this design): stateless connections, no chunked encoding, simpler parsing.
2. **HTTP/1.1**: persistent connections (`Connection: keep-alive`), chunked transfer encoding, pipelining, host-header requirement.

**Decision:**
HTTP/1.0.

**Consequences:**

- Pro: every connection serves exactly one request. No state to track between requests on a single socket.
- Pro: no chunked encoding parsing. Response body length is known via `Content-Length` or determined by EOF.
- Pro: simpler request parsing. No need to handle pipelined requests.
- Con: cannot leverage connection reuse. Each request requires a fresh TCP handshake.
- Con: real clients send HTTP/1.1 by default. The server returns 200 to those, but a strict 1.1 client might expect 1.1 responses.

For a study project, the simplifications are worth it. The HTTP/1.0 vs 1.1 difference is a separate, well-documented exercise.

---

## ADR 3: Cache key as URL with slashes replaced

**Status:** accepted

**Context:**
The proxy needs to generate a filename from a URL. Two options:

1. **Replace special characters with underscores** (this design): `url.replace('/', '_')`.
2. **Hash the URL** (e.g., MD5): `hashlib.md5(url.encode()).hexdigest()`.

**Decision:**
Slash replacement.

**Consequences:**

- Pro: human-readable filenames. `cache/example.com_page` is obvious.
- Pro: simpler code (no hashing).
- Con: long URLs exceed filesystem limits (255 bytes for `ext4`).
- Con: query strings, fragments, and other special characters can collide or cause filesystem errors.
- Con: case-insensitive filesystems (macOS HFS+, Windows NTFS) collapse `/Foo` and `/foo` to the same cache file.

For the test cases in this assignment, slash replacement works. For production, use hashing. The hash collision probability is negligible (1 in 2^128 for MD5), filenames are fixed length, and special characters are not a problem.

---

## ADR 4: MIME type detection via `mimetypes.guess_type()`

**Status:** accepted

**Context:**
The web server needs to set `Content-Type` headers based on the file being served. Two options:

1. **Extension-based** (this design): use Python's `mimetypes.guess_type(filename)`, which maps file extensions to MIME types.
2. **Magic number detection**: read the first few bytes of the file and identify the format from its signature (e.g., `0xFFD8FF` for JPEG).

**Decision:**
Extension-based via `mimetypes`.

**Consequences:**

- Pro: stdlib only. No external dependency on `python-magic` or libmagic.
- Pro: fast. No file read for type detection.
- Pro: covers the common case. `.html`, `.jpg`, `.png`, `.css`, `.js` all resolve correctly.
- Con: filename without extension defaults to `application/octet-stream`.
- Con: maliciously-renamed file (`.html` containing PHP) would be served with the wrong content type. Production servers might use both extension and magic-number checks.

For an educational exercise, extension-based is fine.

---

## ADR 5: HTTPS not supported in proxy

**Status:** accepted

**Context:**
Real HTTP proxies handle HTTPS via the `CONNECT` method, which tells the proxy to open a TCP tunnel to the remote without inspecting the encrypted bytes. Two options:

1. **Reject HTTPS** (this design): if the URL starts with `https://`, drop the connection.
2. **Implement CONNECT**: open a tunnel, relay bytes blindly.

**Decision:**
Reject.

**Consequences:**

- Pro: cache works. The proxy can read response bytes for caching.
- Pro: simpler code. No bidirectional pipe between client and remote.
- Con: cannot proxy any modern site. The web is HTTPS by default.
- Con: not a useful general-purpose proxy.

For the assignment scope (caching demo), HTTP-only is sufficient. A `CONNECT`-supporting proxy would be a separate exercise: the proxy cannot see the encrypted body, so caching is impossible, and the proxy effectively becomes a TCP tunnel.

---

## ADR 6: No cache invalidation

**Status:** accepted

**Context:**
The cache stores responses forever once cached. Real HTTP defines `Cache-Control` (`max-age`, `must-revalidate`, `no-cache`), `ETag`, and `If-Modified-Since` headers for cache invalidation. Two options:

1. **No invalidation** (this design): once cached, always served from cache.
2. **Honor `Cache-Control`**: parse the response headers, set TTLs, expire entries.

**Decision:**
No invalidation.

**Consequences:**

- Pro: simple. Cache hit is a file read; cache write is a file write. No metadata, no expiry.
- Pro: deterministic. The same URL returns the same bytes every time.
- Con: the cache is wrong as soon as the upstream changes. No way to refresh.
- Con: cache grows unboundedly. No eviction policy.

For the assignment (demonstrate caching), no invalidation is fine. For production, every layer of the cache invalidation problem is well-understood (`Cache-Control`, `ETag`, conditional requests, eviction policies like LRU or LFU); each adds significant complexity.

---

## ADR 7: Stdlib only, no external dependencies

**Status:** accepted

**Context:**
Python has excellent HTTP libraries: `http.server`, `httpx`, `requests`, `aiohttp`. Two options:

1. **Stdlib only** (this design): `socket`, `os`, `mimetypes`. No imports beyond what ships with Python.
2. **Use a library**: leverage `requests` for the proxy's outbound calls and `http.server` for the web server.

**Decision:**
Stdlib only.

**Consequences:**

- Pro: zero install steps. Clone and run.
- Pro: educational. Forces every protocol detail to be explicit.
- Pro: every HTTP byte is visible in the source code.
- Con: more code to write. `requests.get()` would be one line; the manual proxy version is ten.
- Con: less robust against edge cases (HTTP/1.1 features, unusual content encodings, redirects).

For a project whose entire point is to see HTTP from the bottom up, stdlib only is the right call. Using `requests` would defeat the purpose.
