import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trolley")


class Trolley(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()


client = Trolley()


@client.event
async def on_ready() -> None:
    log.info("Logged in as %s (%s)", client.user, client.user.id)


@client.tree.command(description="Check that Trolley is alive")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("pong")


def main() -> None:
    token = os.environ["DISCORD_BOT_TOKEN"]
    client.run(token)


if __name__ == "__main__":
    main()
