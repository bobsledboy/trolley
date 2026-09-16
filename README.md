# Trolley

A self-hosted Discord bot that captures recipes from links and photos, plans
your week from a rotation of favourites, builds a shopping list, and fills
your Woolworths basket for you.

Each deployment is its own thing: your own Discord bot application, your own
database, your own Woolworths account connected via `/retailer connect` once
that's built. Nothing about one installation is shared with another — see
[`docs/design.pdf`](docs/design.pdf) for the full design, and
[`LICENSE`](LICENSE) (MIT) for terms.

It's a single container — Postgres runs inside it via `supervisord`, so
there's nothing else to stand up alongside it.

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
3. Run it with Docker Compose — same image as production, Postgres bundled
   inside it, nothing else to start:

   ```bash
   docker compose up --build
   ```

4. In Discord, run `/ping` to check it's alive, then paste a recipe link in
   a DM or `#recipes` channel.

## Running on Unraid

Every push to `main` builds this same image and publishes it to
`ghcr.io/bobsledboy/trolley:latest` (see
[`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml)) —
Unraid only ever pulls it, never builds from source. The package is public,
so no registry login is needed. No Compose Manager, no second container for
Postgres — just:

1. Docker tab → **Add Container**. Repository: `ghcr.io/bobsledboy/trolley:latest`.
2. Add a **Variable**: Key `DISCORD_BOT_TOKEN`, Value your real token.
3. Add a **Path**: Container Path `/var/lib/postgresql/data`, Host Path
   `/mnt/user/appdata/trolley/pgdata` — this is where the bundled Postgres
   keeps its data, so it survives container updates and shows up under
   Unraid's normal appdata backups.
4. Apply. First boot takes a few extra seconds while Postgres initializes;
   check the container's log for `Logged in as Trolley#...` to confirm it's
   up.
5. To pick up a new build later: pull the image again and restart the
   container from the Docker tab.
