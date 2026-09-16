# Trolley

A Discord bot that captures recipes from links and photos, plans your week
from a rotation of favourites, builds a shopping list, and fills your
Woolworths basket for you.

Full design doc: [`docs/design.pdf`](docs/design.pdf).

## Status — Phase 1

Recipe capture from links is working:

- Paste a URL in a DM or a channel named `#recipes` and Trolley extracts the
  recipe (`schema.org/Recipe` data via `recipe-scrapers`; sites without that
  data aren't handled yet — that's the tier-2 LLM fallback, coming later).
- React ✅ to save it, ❌ to discard it.
- `/recipe list`, `/recipe show`, `/recipe delete`.

Not built yet: photo capture, meal planning, shopping lists, Woolworths
integration, substitutions. See the design doc's phased build plan.

## Setup

1. Create a Discord application and bot user at the
   [Discord Developer Portal](https://discord.com/developers/applications).
   Under **Bot**, enable the **Message Content Intent** — without it Trolley
   can't read the links you paste. Under **OAuth2 → URL Generator**, check
   the `bot` and `applications.commands` scopes and the **Send Messages**,
   **Read Message History**, **Add Reactions**, **Embed Links** bot
   permissions, then open the generated URL to invite it to your server.
2. `cp .env.example .env` and fill in `DISCORD_BOT_TOKEN`. Trolley watches
   DMs and any channel named `#recipes` for links by default — set
   `RECIPE_CHANNEL_NAME` in `.env` if you'd rather use a different channel
   name.
3. Run it with Docker (bot + Postgres together):

   ```bash
   docker compose up --build
   ```

   Or locally, against a Postgres you run yourself — start one with
   `docker compose up -d db`, point `DATABASE_URL` in `.env` at
   `postgresql://trolley:trolley@localhost:5432/trolley`, then:

   ```bash
   pip install -r requirements.txt
   python -m bot.main
   ```

4. In Discord, run `/ping` to check it's alive, then paste a recipe link in
   a DM or `#recipes` channel.
