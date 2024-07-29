# helpers/utils.py
import requests

async def fetch_paths(interaction, api_url_paths):
    response = requests.get(f"{api_url_paths}list/")
    if response.status_code == 200:
        paths = response.json()
        if not paths:
            await interaction.response.send_message("No paths available.", ephemeral=True)
            return None
        return paths
    else:
        await interaction.response.send_message("Failed to fetch paths.", ephemeral=True)
        return None
