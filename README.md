# Trolley

A Discord bot that captures recipes from links and photos, plans your week
from a rotation of favourites, builds a shopping list, and fills your
Woolworths basket for you.

Full design doc: [`docs/design.pdf`](docs/design.pdf).

## Status

Early scaffold — the bot connects and responds to `/ping`. Nothing from the
design doc's feature set is built yet. See the doc's phased build plan for
what's next; Phase 1 (recipe capture from links) is up first.

## Setup

1. Create a Discord application and bot user at the
   [Discord Developer Portal](https://discord.com/developers/applications),
   invite it to your server, and copy its token.
2. `cp .env.example .env` and paste the token into `DISCORD_BOT_TOKEN`.
3. Run it:

   ```bash
   pip install -r requirements.txt
   python -m bot.main
   ```

   or via Docker:

   ```bash
   docker compose up --build
   ```

4. In Discord, run `/ping` — it should reply `pong`.
