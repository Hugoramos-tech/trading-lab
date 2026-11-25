"""Registro de experimentos.

POR QUE EXISTE ESTE MODULO
--------------------------
El Deflated Sharpe Ratio necesita saber N: cuantas configuraciones has probado.
Si no lo registras, no puedes calcularlo, y sin el no sabes si tu mejor
resultado es habilidad o azar.

Y hay una razon mas importante: registrar la hipotesis ANTES de ver el
resultado impide el autoengano de reinterpretar un hallazgo casual como si
fuera lo que buscabas desde el principio.

Flujo de uso:
    jr = Journal()
    exp_id = jr.declare("Las small caps tardan en reaccionar a resultados",
                        {"lookback": 20, "umbral": 0.05})
    ...  # ahora se ejecuta el backtest
    jr.record(exp_id, result.stats)
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    declared_at TEXT    NOT NULL,
    hypothesis  TEXT    NOT NULL,
    params      TEXT    NOT NULL,
    recorded_at TEXT,
    results     TEXT,
    notes       TEXT
);
"""


class Journal:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.JOURNAL_DB
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def declare(self, hypothesis: str, params: dict) -> int:
        """Declara un experimento ANTES de ejecutarlo. Devuelve su id."""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO experiments (declared_at, hypothesis, params) "
                "VALUES (?, ?, ?)",
                (now, hypothesis, json.dumps(params, sort_keys=True)),
            )
            return int(cur.lastrowid)

    def record(self, experiment_id: int, results: dict, notes: str = "") -> None:
        """Guarda el resultado de un experimento ya declarado."""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            c.execute(
                "UPDATE experiments SET recorded_at=?, results=?, notes=? "
                "WHERE id=?",
                (now, json.dumps(results), notes, experiment_id),
            )

    def n_trials(self) -> int:
        """Total de experimentos declarados. Este es el N del DSR."""
        with self._conn() as c:
            return int(c.execute("SELECT COUNT(*) FROM experiments").fetchone()[0])

    def history(self) -> list[dict]:
        with self._conn() as c:
            c.row_factory = sqlite3.Row
            rows = c.execute(
                "SELECT * FROM experiments ORDER BY id"
            ).fetchall()
        return [dict(r) for r in rows]
