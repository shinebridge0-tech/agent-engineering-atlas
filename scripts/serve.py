"""Foreground-only server: Ctrl+C stops this process; no PID/port termination logic."""
import socket
import uvicorn

HOST = "127.0.0.1"
PORT = 18765


def check_port(port=PORT):
    try:
        with socket.socket() as sock:
            sock.bind((HOST, port))
    except OSError:
        raise RuntimeError("Local port unavailable; no other process or system setting was changed") from None


def main():
    check_port()
    print(f"AgentAtlas: http://{HOST}:{PORT}; keep this terminal open; Ctrl+C to stop.", flush=True)
    uvicorn.run("backend.app:app", host=HOST, port=PORT, access_log=False)


if __name__ == "__main__":
    main()
