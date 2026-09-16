import asyncio
import json
import logging
import re
from dataclasses import dataclass

import asyncpg
import discord
from discord import app_commands

from scraper.extractor import ExtractionError, ExtractedRecipe, extract_sync

log = logging.getLogger("trolley.recipes")

URL_RE = re.compile(r"https?://\S+")
CAPTURE_CHANNEL_NAME = "recipes"
SAVE_EMOJI = "✅"
DISCARD_EMOJI = "❌"


@dataclass
class PendingRecipe:
    url: str
    added_by: int
    data: ExtractedRecipe


pending: dict[int, PendingRecipe] = {}


def is_capture_channel(message: discord.Message) -> bool:
    if isinstance(message.channel, discord.DMChannel):
        return True
    return getattr(message.channel, "name", None) == CAPTURE_CHANNEL_NAME


def build_confirm_embed(url: str, data: ExtractedRecipe) -> discord.Embed:
    embed = discord.Embed(title=data["title"], url=url)
    if data["image_url"]:
        embed.set_image(url=data["image_url"])
    if data["servings"]:
        embed.add_field(name="Servings", value=data["servings"])
    if data["prep_min"]:
        embed.add_field(name="Prep", value=f"{data['prep_min']} min")
    if data["cook_min"]:
        embed.add_field(name="Cook", value=f"{data['cook_min']} min")
    embed.add_field(name="Ingredients", value=str(len(data["ingredients"])))
    embed.set_footer(text=f"{SAVE_EMOJI} save  ·  {DISCARD_EMOJI} discard")
    return embed


async def handle_url_capture(message: discord.Message) -> None:
    if message.author.bot or not is_capture_channel(message):
        return
    match = URL_RE.search(message.content)
    if not match:
        return
    url = match.group(0)

    await message.add_reaction("⏳")
    try:
        data = await asyncio.to_thread(extract_sync, url)
    except ExtractionError as exc:
        await message.clear_reaction("⏳")
        await message.reply(
            f"Couldn't get a recipe from that link ({exc}). "
            "Sites without structured recipe data need the LLM fallback, "
            "which isn't built yet."
        )
        return
    except Exception:
        log.exception("extraction failed for %s", url)
        await message.clear_reaction("⏳")
        await message.reply("Something went wrong fetching that link.")
        return

    await message.clear_reaction("⏳")
    confirm = await message.reply(embed=build_confirm_embed(url, data))
    await confirm.add_reaction(SAVE_EMOJI)
    await confirm.add_reaction(DISCARD_EMOJI)
    pending[confirm.id] = PendingRecipe(url=url, added_by=message.author.id, data=data)


async def save_recipe(db: asyncpg.Pool, url: str, added_by: int, data: ExtractedRecipe) -> None:
    async with db.acquire() as conn, conn.transaction():
        recipe_id = await conn.fetchval(
            """
            INSERT INTO recipes
                (source_url, title, image_url, servings, prep_min, cook_min, instructions, added_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            url,
            data["title"],
            data["image_url"],
            data["servings"],
            data["prep_min"],
            data["cook_min"],
            json.dumps(data["instructions"]),
            added_by,
        )
        if data["ingredients"]:
            await conn.executemany(
                "INSERT INTO ingredients (recipe_id, position, raw_text) VALUES ($1, $2, $3)",
                [(recipe_id, i, text) for i, text in enumerate(data["ingredients"])],
            )


async def handle_reaction(client: discord.Client, payload: discord.RawReactionActionEvent) -> None:
    if payload.user_id == client.user.id:
        return
    item = pending.get(payload.message_id)
    if item is None or payload.user_id != item.added_by:
        return
    emoji = str(payload.emoji)
    if emoji not in (SAVE_EMOJI, DISCARD_EMOJI):
        return

    channel = client.get_channel(payload.channel_id) or await client.fetch_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    del pending[payload.message_id]

    if emoji == DISCARD_EMOJI:
        await msg.edit(content="Discarded.", embed=None)
        await msg.clear_reactions()
        return

    try:
        await save_recipe(client.db, item.url, item.added_by, item.data)
    except asyncpg.UniqueViolationError:
        await msg.edit(content=f"Already in your library: **{item.data['title']}**", embed=None)
        await msg.clear_reactions()
        return

    await msg.edit(content=f"Saved **{item.data['title']}**.")
    await msg.clear_reactions()


recipe_group = app_commands.Group(name="recipe", description="Manage your recipe library")


async def title_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    rows = await interaction.client.db.fetch(
        "SELECT title FROM recipes WHERE title ILIKE $1 ORDER BY title LIMIT 25",
        f"%{current}%",
    )
    return [app_commands.Choice(name=r["title"], value=r["title"]) for r in rows]


@recipe_group.command(name="list", description="List your saved recipes")
async def recipe_list(interaction: discord.Interaction) -> None:
    rows = await interaction.client.db.fetch(
        "SELECT title FROM recipes ORDER BY created_at DESC LIMIT 25"
    )
    if not rows:
        await interaction.response.send_message("No recipes saved yet — paste a link to add one.")
        return
    embed = discord.Embed(
        title="Recipes",
        description="\n".join(f"- {r['title']}" for r in rows),
    )
    await interaction.response.send_message(embed=embed)


@recipe_group.command(name="show", description="Show a saved recipe")
@app_commands.autocomplete(title=title_autocomplete)
async def recipe_show(interaction: discord.Interaction, title: str) -> None:
    row = await interaction.client.db.fetchrow("SELECT * FROM recipes WHERE title = $1", title)
    if row is None:
        await interaction.response.send_message(f"No recipe called **{title}**.", ephemeral=True)
        return

    ingredient_rows = await interaction.client.db.fetch(
        "SELECT raw_text FROM ingredients WHERE recipe_id = $1 ORDER BY position", row["id"]
    )

    embed = discord.Embed(title=row["title"], url=row["source_url"])
    if row["image_url"]:
        embed.set_image(url=row["image_url"])
    ingredients_text = "\n".join(f"- {r['raw_text']}" for r in ingredient_rows) or "—"
    embed.add_field(name="Ingredients", value=ingredients_text[:1024], inline=False)
    instructions = json.loads(row["instructions"]) if isinstance(row["instructions"], str) else row["instructions"]
    steps_text = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(instructions)) or "—"
    embed.add_field(name="Instructions", value=steps_text[:1024], inline=False)
    await interaction.response.send_message(embed=embed)


@recipe_group.command(name="delete", description="Delete a saved recipe")
@app_commands.autocomplete(title=title_autocomplete)
async def recipe_delete(interaction: discord.Interaction, title: str) -> None:
    result = await interaction.client.db.execute("DELETE FROM recipes WHERE title = $1", title)
    if result == "DELETE 0":
        await interaction.response.send_message(f"No recipe called **{title}**.", ephemeral=True)
        return
    await interaction.response.send_message(f"Deleted **{title}**.")
