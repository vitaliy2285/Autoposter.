# telegram_autoposter

Коробочный Telegram-автопостер для security-каналов.

## Структура

```
telegram_autoposter/
├── .env.example
├── requirements.txt
├── README.md
├── config.json (создаётся при первом запуске)
├── logs/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── bot.py
│   ├── admin_handlers.py
│   ├── content_creator.py
│   ├── formatter.py
│   ├── scheduler.py
│   ├── utils.py
│   ├── models.py
│   ├── sources/
│   │   ├── base.py
│   │   └── github_hunter.py
│   └── generators/
│       ├── text_generator.py
│       └── image_generator.py
└── tests/
    ├── test_formatter.py
    └── test_utils.py
```

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.main
```

## Админ-команды

`/start`, `/set_topic`, `/set_times`, `/set_tone`, `/set_mood`, `/set_style`, `/set_image_size`,
`/set_auth_kandinsky`, `/set_openai`, `/set_keywords`, `/set_channel`, `/toggle`, `/post_now`,
`/stats`, `/settings`, `/reset`.

## Примечания

- Сначала читается `.env`, затем `config.json` (JSON перекрывает env).
- При ошибке картинки пост отправляется текстом.
- При ошибке публикации в канал автопостинг отключается автоматически.
