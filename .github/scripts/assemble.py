#!/usr/bin/env python3
"""Собрать generator/data.json = скелет (приватный репо) + статьи (публичный репо).

data.json = дизайн-скелет (site/locale/strings/tags/tagbar) из приватного
repo `davnozdu/24n` (generator/scaffold.json) + массив `articles` из этого
публичного репо (articles.json). Так generate.py не знает о разделении —
получает привычный полный data.json.

Использование:
    assemble.py <scaffold.json> <articles.json> <out data.json>
"""
import json
import sys


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: assemble.py <scaffold.json> <articles.json> <out.json>",
              file=sys.stderr)
        return 2
    scaffold_path, articles_path, out_path = sys.argv[1:4]
    with open(scaffold_path, encoding="utf-8") as fh:
        data = json.load(fh)
    with open(articles_path, encoding="utf-8") as fh:
        arts = json.load(fh)
    # articles.json — либо обёртка {..., "articles": [...]}, либо голый массив.
    if isinstance(arts, dict):
        articles = arts.get("articles", [])
    elif isinstance(arts, list):
        articles = arts
    else:
        articles = []
    data["articles"] = articles
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"data.json собран: {len(articles)} статей → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
