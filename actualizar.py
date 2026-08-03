#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Club Sin Fronteras — actualizador diario.
Mueve 1-2 historias reales del reservorio (backlog.json) al feed (noticias.json),
recorta el feed a un maximo y publica en GitHub Pages con git push.
Se ejecuta solo, 1x al dia, via Tarea Programada de Windows.
"""
import json
import random
import subprocess
import datetime
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
FEED = BASE / "noticias.json"
BACKLOG = BASE / "backlog.json"
MAX_FEED = 12          # cuantas tarjetas conserva el feed
LOG = BASE / "actualizar.log"


def log(msg):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def git(*args):
    return subprocess.run(["git", "-C", str(BASE), *args],
                          check=True, capture_output=True, text=True)


def main():
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))

    if not backlog:
        log("Reservorio VACIO. Pide a Claude: 'rellena el backlog del Club'. Nada que publicar.")
        return

    n = random.choice([1, 2])
    n = min(n, len(backlog))
    picked = backlog[:n]
    backlog = backlog[n:]

    for item in picked:
        item.setdefault("badge", "new")
        item.setdefault("tag", "Nuevo")

    feed = picked + feed
    feed = feed[:MAX_FEED]

    FEED.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    BACKLOG.write_text(json.dumps(backlog, ensure_ascii=False, indent=2), encoding="utf-8")

    titulos = " | ".join(p.get("titulo", "?") for p in picked)
    try:
        git("add", "noticias.json", "backlog.json")
        git("commit", "-m", f"Actualizacion diaria {datetime.date.today().isoformat()} (+{n})")
        git("push")
        log(f"Publicadas {n} historia(s): {titulos}. Quedan {len(backlog)} en el reservorio.")
    except subprocess.CalledProcessError as e:
        log(f"ERROR git: {e.stderr.strip() if e.stderr else e}")
        sys.exit(1)

    if len(backlog) <= 3:
        log(f"AVISO: reservorio bajo ({len(backlog)}). Pide a Claude que lo rellene pronto.")


if __name__ == "__main__":
    main()
