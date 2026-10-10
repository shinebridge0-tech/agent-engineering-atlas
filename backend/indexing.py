import json
import sqlite3
from contextlib import closing
from pathlib import Path
from .content import ROOT, CONTENT, load_all

DB = ROOT / ".local" / "index.db"

def rebuild(root: Path = CONTENT, db: Path = DB):
    cards = load_all(root)  # validate before touching last usable index
    db.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS cards (id TEXT PRIMARY KEY, payload TEXT NOT NULL, search TEXT NOT NULL)")
        with conn:
            conn.execute("DELETE FROM cards")
            for card in cards:
                text = " ".join([card.title, card.problem, card.approach, *card.tags, *card.aliases]).lower()
                conn.execute("INSERT INTO cards VALUES (?, ?, ?)", (card.id + ":" + card.locale, card.model_dump_json(), text))
        try:
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS capability_probe USING fts5(text)")
            fts = True
        except sqlite3.OperationalError:
            fts = False
    return {"count": len(cards), "fts5_available": fts, "search_mode": "parameterized substring + bilingual aliases; FTS not used for ranking"}

def read_cards(db: Path = DB):
    if not db.exists():
        rebuild(db=db)
    with closing(sqlite3.connect(db)) as conn:
        return [json.loads(row[0]) for row in conn.execute("SELECT payload FROM cards ORDER BY id")]
