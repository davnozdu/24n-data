#!/usr/bin/env python3
"""Склеить ВСЕ статьи архива в один файл формата articles.json.

ЗАЧЕМ. `articles.json` — это окно последних новостей (300 штук). Хостингу
такого хватает: заливка инкрементальная, старые страницы лежат на сервере и
никуда не деваются. А деплой на Cloudflare — ПОЛНЫЙ СНИМОК: чего нет в
выкладке, того нет на сайте. Собранный из одного окна снимок стирал 2311
статей, которые есть в суточных срезах.

Поэтому для снимка статьи берутся из `archive/*.json` плюс текущее окно. При
совпадении слага побеждает более поздняя версия — в окне лежит самое свежее
состояние материала.

Не покрывает 1381 статью, выложенную до начала архивирования: данных от них не
осталось, только готовые страницы. Они живут в R2 и отдаются воркером — см.
cloudflare/fetch_legacy.py и cloudflare/worker.js.

Запуск: full_articles.py <archive/> <articles.json> <out.json>
"""
import json
import sys
from glob import glob
from os.path import basename, join


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: full_articles.py <archive_dir> <articles.json> <out.json>",
              file=sys.stderr)
        return 2
    archive_dir, window_path, out_path = sys.argv[1:4]

    by_slug: dict[str, dict] = {}

    def take(articles, where: str) -> int:
        n = 0
        for a in articles:
            slug = (a.get("slug") or "").strip()
            if not slug:
                continue
            by_slug[slug] = a
            n += 1
        return n

    for path in sorted(glob(join(archive_dir, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                take(json.load(fh).get("articles") or [], basename(path))
        except (OSError, ValueError) as exc:   # битый срез не должен ронять сборку
            print(f"  срез пропущен ({basename(path)}): {exc}", file=sys.stderr)

    with open(window_path, encoding="utf-8") as fh:
        window = json.load(fh)
    take(window.get("articles") or [], "articles.json")   # окно перекрывает срезы

    articles = sorted(by_slug.values(),
                      key=lambda a: a.get("published_at") or "", reverse=True)
    out = {
        "updated_at": window.get("updated_at", ""),
        "count": len(articles),
        "generated_by": "full_articles.py (срезы архива + окно)",
        "articles": articles,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print(f"полный набор: {len(articles)} статей → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
