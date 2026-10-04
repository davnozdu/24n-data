# 24n-data — публичное хранилище новостей 24n.cz

Этот **публичный** репозиторий хранит базу новостей сайта [24n.cz](https://24n.cz/)
и собирает полный статический сайт на Cloudflare Workers Assets/R2.
FTPS отключён и сохранён как резерв. Код и дизайн сайта — в приватном репозитории
`davnozdu/24n`.

## Как это работает

```
Робот-автопостер ──push──▶ articles.json  (этот репо)
                                  │  push триггерит GitHub Action
                                  ▼
                    .github/workflows/deploy.yml:
                      1. checkout этого репо (окно новостей + archive/)
                      2. checkout приватного davnozdu/24n (генератор + scaffold.json)
                      3. full_articles.py + assemble.py: scaffold + весь архив → data.json
                      4. generate.py → dist/ (включая индекс поиска по заголовкам)
                      5. SEO-аудит → legacy-страницы → R2 (излишек) → Workers Assets
```

Репозиторий публичный → минуты GitHub Actions бесплатны и безлимитны.

## Файлы

- **`articles.json`** — массив новостей (обёртка `{updated_at, count, articles:[…]}`),
  который пишет робот. Единственный часто меняющийся файл.
- `.github/workflows/deploy.yml` — сборка и деплой при каждом push `articles.json`.
- `.github/scripts/assemble.py` — склейка `scaffold.json` (приватный) + `articles.json`.
- `.github/scripts/deploy.mjs` — инкрементальная заливка `dist/` по FTPS (lftp).

## Секреты репозитория (Settings → Secrets and variables → Actions)

| Секрет | Назначение |
|---|---|
| `SITE_REPO_TOKEN` | PAT с правом **contents: read** на приватный `davnozdu/24n` |
| `FTP_HOST`, `FTP_USER`, `FTP_PASSWORD`, `FTP_REMOTE_DIR`, `FTP_PORT` | доступ к хостингу (как в приватном репо) |

Переменные (Variables): `FTP_SECURE` (по умолч. `true`), `DEPLOY_FORCE_FULL`
(`true` — разовая полная перезаливка).

## Проверки сборки

`python3 .github/scripts/test_assemble.py` проверяет исправления дат,
сохранность архива и отказ сборки при повреждённых данных. `lastmod` отражает
реальную дату обновления, если она позже публикации.
В CI запускается также `site/tools/check_site.py site/dist`: canonical,
взаимный hreflang, sitemap, index/noindex, NewsArticle и доступность ассетов.
Адаптивные WebP-фотографии кешируются между сборками; ошибка загрузки фото
оставляет оригинал. Перед публикацией проверяется HEAD обоих репозиториев,
чтобы устаревшая сборка не перезаписала новые новости.
