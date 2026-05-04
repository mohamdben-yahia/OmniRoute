import json
import socket

PORTS = list(range(62000, 62650))
HITS = []
for port in PORTS:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.15) as sock:
            sock.sendall(b"GET /json/version HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
            data = sock.recv(2048)
            if b"node.js" in data or b"Protocol-Version" in data or b"Browser" in data:
                HITS.append({"port": port, "preview": data.decode("utf-8", errors="replace")[:500]})
    except Exception:
        pass
print(json.dumps(HITS, indent=2))
