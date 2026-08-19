#!/usr/bin/env python3
"""Собрать generator/data.json = скелет (приватный репо) + статьи (публичный репо).

data.json = дизайн-скелет (site/locale/strings/tags/tagbar) из приватного
repo `davnozdu/24n` (generator/scaffold.json) + массив `articles` из этого
публичного репо (articles.json). Так generate.py не знает о разделении —
получает привычный полный data.json.

Сюда же собирается ПОЛНЫЙ список адресов для карты сайта (`sitemap_urls`):
окно `articles.json` — это последние 300 новостей, а на хостинге лежит весь
архив, и без остальных адресов карта показывала бы Google малую часть сайта.
Список берётся из суточных срезов `archive/*.json` плюс `sitemap-legacy.json`
(статьи, выложенные до начала архивирования). См. `_sitemap_urls`.

Использование:
    assemble.py <scaffold.json> <articles.json> <out data.json>
"""
import json
import os
import sys
from glob import glob


def _sitemap_urls(repo_root: str, window: list) -> list:
    """Все адреса статей, что лежат на хостинге: [[слаг, дата], …].

    Три источника, от старого к новому — при совпадении слага побеждает более
    поздний, у него дата точнее:
      1. sitemap-legacy.json — выложено до начала архивирования, снято с сервера;
      2. archive/*.json      — суточные срезы;
      3. articles.json       — текущее окно (оно же попадает в `articles`).

    Дата = день публикации, она уходит в <lastmod>. Пустой список (нет ни
    срезов, ни legacy) — не беда: generate.py тогда строит карту по окну,
    как делал раньше.
    """
    urls: dict[str, str] = {}

    legacy_path = os.path.join(repo_root, "sitemap-legacy.json")
    if os.path.isfile(legacy_path):
        with open(legacy_path, encoding="utf-8") as fh:
            legacy = json.load(fh)
        urls.update(legacy.get("urls") or {})

    def take(articles):
        for a in articles:
            slug = (a.get("slug") or "").strip()
            pub = (a.get("published_at") or "")[:10]
            if slug and pub:
                urls[slug] = pub

    for path in sorted(glob(os.path.join(repo_root, "archive", "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                take(json.load(fh).get("articles") or [])
        except (OSError, ValueError) as exc:   # битый срез не должен ронять сборку
            print(f"  срез пропущен ({os.path.basename(path)}): {exc}",
                  file=sys.stderr)

    take(window)
    return [[slug, urls[slug]] for slug in sorted(urls, key=lambda s: (urls[s], s),
                                                  reverse=True)]


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
    # Полный список адресов для карты сайта — рядом с окном статей.
    # Корень репо считаем от articles.json: в CI скрипт зовут из корня, но
    # завязываться на текущий каталог не стоит.
    repo_root = os.path.dirname(os.path.abspath(articles_path)) or "."
    data["sitemap_urls"] = _sitemap_urls(repo_root, articles)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"data.json собран: {len(articles)} статей в окне, "
          f"{len(data['sitemap_urls'])} адресов для карты сайта → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
