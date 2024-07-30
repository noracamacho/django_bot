# discord_bot.py

import discord
from discord import app_commands
from discord.ui import View
import os
from dotenv import load_dotenv
import requests
from paths.components import PathButton, PathModal, DeletePathButton
from topics.components import SelectPathButton
from tasks.components import TaskSelectPathButton, WeekPaginator 
from helpers.utils import fetch_paths, fetch_topics  # Import the helper function

# Load environment variables from .env file
load_dotenv()

# Retrieve the Discord token from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

API_URL_PATHS = "http://127.0.0.1:8000/api/paths/"
API_URL_TOPICS = "http://127.0.0.1:8000/api/topics/"
API_URL_TASKS = "http://127.0.0.1:8000/api/tasks/"

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


# Path commands
@tree.command(name="addpath", description="Add a new path")
async def addpath(interaction: discord.Interaction):
    modal = PathModal()
    await interaction.response.send_modal(modal)
    
    
@tree.command(name="updatepath", description="Update an existing path")
async def updatepath(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths is None:
        return

    view = View()
    for path in paths:
        view.add_item(PathButton(path))

    await interaction.response.send_message("Select a path to update:", view=view, ephemeral=True)
    

@tree.command(name="deletepath", description="Delete an existing path")
async def deletepath(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths is None:
        return

    view = View()
    for path in paths:
        view.add_item(DeletePathButton(path))

    await interaction.response.send_message("Select a path to delete:", view=view, ephemeral=True)
    

@tree.command(name="listpaths", description="List all paths")
async def listpaths(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths is None:
        return

    try:
        paths_list = "\n".join([f"  ▫️ {path['name']} ({path['duration_weeks']} weeks)" for path in paths])
        await interaction.response.send_message(f"Paths:\n{paths_list}", ephemeral=True)
    except ValueError as e:
        # If there is an error in JSON decoding
        print(f"JSON decoding failed: {e}")
        await interaction.response.send_message("Failed to decode paths data.", ephemeral=True)
        

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


# Topic commands
@tree.command(name="listtopics", description="List all topics in a path")
async def listtopics(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths is None:
        return

    view = View()
    for path in paths:
        view.add_item(SelectPathButton(path, 'list_topics'))

    await interaction.response.send_message("Select a path to list its topics:", view=view, ephemeral=True)
    

@tree.command(name="addtopic", description="Add a new topic")
async def addtopic(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths is None:
        return

    view = View()
    for path in paths:
        view.add_item(SelectPathButton(path, 'add_topic'))

    await interaction.response.send_message("Select a path to add a topic:", view=view, ephemeral=True)
    

@tree.command(name="updatetopic", description="Update an existing topic")
async def updatetopic(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths is None:
        return

    view = View()
    for path in paths:
        view.add_item(SelectPathButton(path, 'update_topic'))

    await interaction.response.send_message("Select a path to update a topic:", view=view, ephemeral=True)
    

@tree.command(name="deletetopic", description="Delete an existing topic")
async def deletetopic(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths is None:
        return

    view = View()
    for path in paths:
        view.add_item(SelectPathButton(path, 'delete_topic'))

    await interaction.response.send_message("Select a path to delete a topic:", view=view, ephemeral=True)
    

# Task Commands
@tree.command(name="addtask", description="Add a new task")
async def addtask(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths:
        view = View()
        for path in paths:
            view.add_item(TaskSelectPathButton(path, 'add_task'))
        await interaction.response.send_message("Select a path to add a task:", view=view, ephemeral=True)


@tree.command(name="updatetask", description="Update an existing task")
async def updatetask(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths:
        view = View()
        for path in paths:
            view.add_item(TaskSelectPathButton(path, 'update_task'))
        await interaction.response.send_message("Select a path to update a task:", view=view, ephemeral=True)


@tree.command(name="deletetask", description="Delete an existing task")
async def deletetask(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths:
        view = View()
        for path in paths:
            view.add_item(TaskSelectPathButton(path, 'delete_task'))
        await interaction.response.send_message("Select a path to delete a task:", view=view, ephemeral=True)


@tree.command(name="listtasks", description="List all tasks in a path")
async def listtasks(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths:
        view = View()
        for path in paths:
            view.add_item(TaskSelectPathButton(path, 'list_tasks'))
        await interaction.response.send_message("Select a path to list its tasks:", view=view, ephemeral=True)


@tree.command(name="listtasksbytopic", description="List tasks by selecting a path and then a topic")
async def listtasksbytopic(interaction: discord.Interaction):
    paths = await fetch_paths(interaction, API_URL_PATHS)
    if paths:
        view = View()
        for path in paths:
            view.add_item(TaskSelectPathButton(path, 'list_tasks_by_topic'))
        await interaction.response.send_message("Select a path to list its tasks by topic:", view=view, ephemeral=True)


client.run(DISCORD_TOKEN)