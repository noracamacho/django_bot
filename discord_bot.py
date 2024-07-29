# discord_bot.py

import discord
from discord import app_commands
import requests
import os
from dotenv import load_dotenv
from paths.components import PathButton, PathModal, DeletePathButton

# Load environment variables from .env file
load_dotenv()

# Retrieve the Discord token from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

API_URL_PATHS = "http://127.0.0.1:8000/api/paths/"

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands have been synced.")

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        print(f'Commands synced: {[cmd.name for cmd in self.tree.get_commands()]}')

client = MyClient()
tree = client.tree


# Path Commands
@tree.command(name="addpath", description="Add a new path")
async def addpath(interaction: discord.Interaction):
    modal = PathModal()
    await interaction.response.send_modal(modal)


@tree.command(name="updatepath", description="Update an existing path")
async def updatepath(interaction: discord.Interaction):
    response = requests.get(f"{API_URL_PATHS}list/")
    if response.status_code == 200:
        paths = response.json()
        # print(f"Received paths: {paths}")
        if not paths:
            await interaction.response.send_message("No paths available to update.", ephemeral=True)
            return

        view = discord.ui.View()
        for path in paths:
            view.add_item(PathButton(path))

        await interaction.response.send_message("Select a path to update:", view=view, ephemeral=True)
    else:
        await interaction.response.send_message("Failed to fetch paths.", ephemeral=True)
        

@tree.command(name="deletepath", description="Delete an existing path")
async def deletepath(interaction: discord.Interaction):
    response = requests.get(f"{API_URL_PATHS}list/")
    if response.status_code == 200:
        paths = response.json()
        # print(f" {paths}")
        if not paths:
            await interaction.response.send_message("No paths available to delete.", ephemeral=True)
            return

        view = discord.ui.View()
        for path in paths:
            view.add_item(DeletePathButton(path))

        await interaction.response.send_message("Select a path to delete:", view=view, ephemeral=True)
    else:
        await interaction.response.send_message("Failed to fetch paths.", ephemeral=True)


@tree.command(name="listpaths", description="List all paths")
async def listpaths(interaction: discord.Interaction):
    response = requests.get(f"{API_URL_PATHS}list/")
    if response.status_code == 200:
        try:
            paths = response.json()
            if not paths:
                await interaction.response.send_message("No paths available.", ephemeral=True)
                return

            paths_list = "\n".join([f"  ▫️ {path['name']} ({path['duration_weeks']} weeks)" for path in paths])
            await interaction.response.send_message(f"Paths:\n{paths_list}", ephemeral=True)
        except ValueError as e:
            # If there is an error in JSON decoding
            print(f"JSON decoding failed: {e}")
            await interaction.response.send_message("Failed to decode paths data.", ephemeral=True)
    else:
        await interaction.response.send_message("Failed to fetch paths.", ephemeral=True)


@tree.command(name="getpath", description="Get details of a specific path")
@app_commands.describe(path_id="The ID of the path to retrieve")
async def getpath(interaction: discord.Interaction, path_id: int):
    response = requests.get(f"{API_URL_PATHS}{path_id}/")
    if response.status_code == 200:
        path = response.json()
        path_details = f"Name: {path['name']}\nDuration (weeks): {path['duration_weeks']}"
        await interaction.response.send_message(f"Path Details:\n{path_details}", ephemeral=True)
    elif response.status_code == 404:
        await interaction.response.send_message("Path not found.", ephemeral=True)
    else:
        await interaction.response.send_message("Failed to fetch path details.", ephemeral=True)



client.run(DISCORD_TOKEN)