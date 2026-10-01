# Maintenance scripts

Run them from the repository root as modules, so they can import the main
code (`bot`, `datos`) and find `clientes/` and `pruebas/`:

```bash
python -m scripts.crear_tablas
```

| Script | Usage | What it does |
|---|---|---|
| `crear_tablas` | `python -m scripts.crear_tablas` | Creates the database tables (idempotent). |
| `cargar_fichas` | `python -m scripts.cargar_fichas` | Loads every `clientes/*.yaml` into the `clientes` table (upsert by slug). |
| `suscribir` | `python -m scripts.suscribir [waba_id]` | Subscribes the Meta app to a WhatsApp Business Account. Falls back to `WABA_ID`. |
| `chat` | `python -m scripts.chat [slug]` | Chats with a client's bot in the terminal, without WhatsApp or tools. |
| `probar` | `python -m scripts.probar [slug]` | Runs every line of `pruebas/<slug>.txt` against the bot, one question at a time. |
| `ver_leads` | `python -m scripts.ver_leads` | Shows the latest 20 leads. |
| `ver_mensajes` | `python -m scripts.ver_mensajes` | Shows the latest 20 messages. |
| `olvidar` | `python -m scripts.olvidar <slug> <phone>` | Deletes a conversation's messages, leads and pause, to test from scratch. |
| `liberar` | `python -m scripts.liberar <slug> <phone_number_id>` | Changes the WhatsApp number assigned to a client. |
| `despausar` | `python -m scripts.despausar` | Lifts every human-handoff pause. |

All of them read `DATABASE_URL` (and the API keys they need) from `.env`.
