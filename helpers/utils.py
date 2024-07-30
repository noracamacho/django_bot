# helpers/utils.py
import requests
import logging
import json

logger = logging.getLogger(__name__)

API_URL_PATHS = "http://127.0.0.1:8000/api/paths/"

async def fetch_paths(interaction, api_url_paths):
    response = requests.get(f"{api_url_paths}list/")
    logger.info(f"Received response with status code {response.status_code}")
    if response.status_code == 200:
        try:
            paths = response.json()
        except json.JSONDecodeError:
            logger.error("Failed to parse paths.")
            await interaction.response.send_message("Failed to parse paths.", ephemeral=True)
            return None
        if not paths:
            await interaction.response.send_message("No paths available.", ephemeral=True)
            return None
        return paths
    else:
        logger.error("Failed to fetch paths.")
        await interaction.response.send_message("Failed to fetch paths.", ephemeral=True)
        return None
    
    

async def fetch_topics(interaction, api_url_topics):
    response = requests.get(f"{api_url_topics}list/")
    if response.status_code == 200:
        try:
            topics = response.json()
        except json.JSONDecodeError:
            await interaction.response.send_message("Failed to parse topics.", ephemeral=True)
            return None
        return topics
    elif response.status_code == 404:
        await interaction.response.send_message("No topics available.", ephemeral=True)
        return None
    else:
        await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)
        return None



async def fetch_tasks(interaction, api_url_tasks, topic_id):
    response = requests.get(f"{api_url_tasks}list/")
    if response.status_code == 200:
        try:
            tasks = response.json()
        except json.JSONDecodeError:
            await interaction.response.send_message("Failed to parse tasks.", ephemeral=True)
            return None
        tasks = [task for task in tasks if task['topic'] == topic_id]
        return tasks
    elif response.status_code == 404:
        await interaction.response.send_message("No tasks available.", ephemeral=True)
        return None
    else:
        await interaction.response.send_message("Failed to fetch tasks.", ephemeral=True)
        return None
    

async def fetch_tasks_by_path(interaction, api_url_tasks, path_id):
    response = requests.get(f"{api_url_tasks}list/")
    if response.status_code == 200:
        try:
            tasks = response.json()
        except json.JSONDecodeError:
            await interaction.response.send_message("Failed to parse tasks.", ephemeral=True)
            return None
        tasks = [task for task in tasks if task['path'] == path_id]
        return tasks
    elif response.status_code == 404:
        await interaction.response.send_message("No tasks available.", ephemeral=True)
        return None
    else:
        await interaction.response.send_message("Failed to fetch tasks.", ephemeral=True)
        return None
