import socket
import pytest
from scripts import serve


def test_occupied_port_refuses_without_touching_process(monkeypatch):
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", 0))
        holder.listen(1)
        port = holder.getsockname()[1]
        with pytest.raises(RuntimeError, match="no other process"):
            serve.check_port(port)
        # The unrelated listener remains alive and owns its socket.
        assert holder.getsockname()[1] == port
        with socket.socket() as client:
            client.connect(("127.0.0.1", port))
        connection, _ = holder.accept()
        connection.close()


def test_port_failure_does_not_start_server(monkeypatch):
    def occupied():
        raise RuntimeError("occupied")
    def unexpected(*args, **kwargs):
        raise AssertionError("server must not start")
    monkeypatch.setattr(serve, "check_port", occupied)
    monkeypatch.setattr(serve.uvicorn, "run", unexpected)
    with pytest.raises(RuntimeError, match="occupied"):
        serve.main()
