"""Original offline mechanism demonstration, not upstream code or production validation."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3


class LocalTickets:
    """Simulated receiver: key and side effect commit in the same durable transaction."""

    def __init__(self, path: Path):
        self.path = path
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.execute("CREATE TABLE IF NOT EXISTS tickets (operation TEXT PRIMARY KEY, payload TEXT NOT NULL)")

    def create(self, key: str, payload: str):
        with closing(sqlite3.connect(self.path, timeout=10)) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            previous = conn.execute("SELECT payload FROM tickets WHERE operation=?", (key,)).fetchone()
            if previous and previous[0] != payload:
                raise ValueError("same key with different parameters")
            if not previous:
                conn.execute("INSERT INTO tickets VALUES (?, ?)", (key, payload))
        return key

    def count(self):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute("SELECT count(*) FROM tickets").fetchone()[0]


def run(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    receiver = LocalTickets(directory / "receiver.db")
    ledger = directory / "workflow.db"
    with closing(sqlite3.connect(ledger)) as conn, conn:
        conn.execute("CREATE TABLE IF NOT EXISTS state (operation TEXT PRIMARY KEY, approved INTEGER, completed INTEGER)")
        conn.execute("INSERT OR IGNORE INTO state VALUES ('business-42', 1, 0)")
    # A approved workflow receives success, then crashes BEFORE writing completion.
    receiver.create("business-42", "project=demo;subject=test")
    try:
        raise RuntimeError("simulated crash after receiver commit, before checkpoint")
    except RuntimeError:
        pass
    with closing(sqlite3.connect(ledger)) as conn:
        assert conn.execute("SELECT completed FROM state").fetchone()[0] == 0
    # Fresh receiver object reads durable database; no in-memory dedup marker.
    recovered = LocalTickets(receiver.path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert set(pool.map(lambda _: recovered.create("business-42", "project=demo;subject=test"), range(16))) == {"business-42"}
    assert recovered.count() == 1
    try:
        recovered.create("business-42", "different parameters")
        raise AssertionError("parameter substitution accepted")
    except ValueError:
        pass
    with closing(sqlite3.connect(ledger)) as conn, conn:
        conn.execute("UPDATE state SET completed=1 WHERE operation='business-42'")
    # Negative control: non-idempotent receiver creates twice across the same gap.
    with closing(sqlite3.connect(directory / "nonidempotent.db")) as conn, conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, payload TEXT)")
        conn.execute("INSERT INTO tickets(payload) VALUES ('same operation')")
        conn.execute("INSERT INTO tickets(payload) VALUES ('same operation')")
        assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 2
    return {"durable_unique_tickets": 1, "concurrent_retries": 16, "negative_control_tickets": 2,
            "limits": "Simulated crash window, not abrupt power loss; local SQLite receiver only. Requires stable key, durable atomic uniqueness, retention and payload binding. No distributed/network failure proof."}
