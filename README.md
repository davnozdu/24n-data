# 24n-data — публичное хранилище новостей 24n.cz

Этот **публичный** репозиторий хранит базу новостей сайта [24n.cz](https://24n.cz/)
и деплоит сайт на хостинг. Код и дизайн сайта — в приватном репозитории
`davnozdu/24n`.

## Как это работает

```
Робот-автопостер ──push──▶ articles.json  (этот репо)
                                  │  push триггерит GitHub Action
                                  ▼
                    .github/workflows/deploy.yml:
                      1. checkout этого репо (articles.json)
                      2. checkout приватного davnozdu/24n (генератор + scaffold.json)
                      3. assemble.py: data.json = scaffold.json + articles.json
                      4. generate.py → dist/ (включая индекс поиска по заголовкам)
                      5. lftp FTPS → хостинг (только изменённые файлы, архив цел)
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
