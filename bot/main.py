import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from bot import recipes
from db.pool import create_pool

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trolley")


class Trolley(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.db: object = None

    async def setup_hook(self) -> None:
        self.db = await create_pool()
        self.tree.add_command(recipes.recipe_group)
        await self.tree.sync()


client = Trolley()


@client.event
async def on_ready() -> None:
    log.info("Logged in as %s (%s)", client.user, client.user.id)


@client.event
async def on_message(message: discord.Message) -> None:
    await recipes.handle_url_capture(message)


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
    await recipes.handle_reaction(client, payload)


@client.tree.command(description="Check that Trolley is alive")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("pong")


def main() -> None:
    token = os.environ["DISCORD_BOT_TOKEN"]
    client.run(token)


if __name__ == "__main__":
    main()
