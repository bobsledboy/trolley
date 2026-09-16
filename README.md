# Trolley

A self-hosted Discord bot that captures recipes from links and photos, plans
your week from a rotation of favourites, builds a shopping list, and fills
your Woolworths basket for you.

Each deployment is its own thing: your own Discord bot application, your own
database, your own Woolworths account connected via `/retailer connect` once
that's built. Nothing about one installation is shared with another — see
[`docs/design.pdf`](docs/design.pdf) for the full design, and
[`LICENSE`](LICENSE) (MIT) for terms.

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

## Running on Unraid

Every push to `main` builds an image and publishes it to
`ghcr.io/bobsledboy/trolley:latest` (see
[`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml)) —
Unraid only ever pulls that image, it never builds from source. The package
is public, so no registry login is needed.

1. Install the **Compose Manager** plugin from Community Applications.
2. Add a new stack sourced from this repository
   (`https://github.com/bobsledboy/trolley`) — Compose Manager can pull a
   compose file straight from a Git repo. Point it at
   [`docker-compose.unraid.yml`](docker-compose.unraid.yml) specifically
   (it's the deploy-time variant that pulls the published image rather than
   building from source, unlike the root `docker-compose.yml` used for local
   development). If your Compose Manager version can't source from Git,
   copy that one file to `/mnt/user/appdata/trolley/docker-compose.yml` on
   the Unraid share instead.
3. Add a `.env` alongside it with your own `DISCORD_BOT_TOKEN` and
   `DATABASE_URL=postgresql://trolley:trolley@db:5432/trolley`.
4. Hit **Up**. It pulls the image and starts Postgres alongside it, storing
   data under `/mnt/user/appdata/trolley/pgdata`.
5. To pick up a new build later, **Pull** then **Up** again — no rebuild
   happens on the box.
