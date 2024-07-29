# paths/components.py
import discord
import requests

API_URL_PATHS = "http://127.0.0.1:8000/api/paths/"

class PathModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Add New Path")

        self.path_name = discord.ui.TextInput(
            label="Path Name",
            placeholder="Enter the name of the path",
            required=True
        )
        self.duration_weeks = discord.ui.TextInput(
            label="Duration (weeks)",
            placeholder="Enter the duration in weeks",
            required=True
        )

        self.add_item(self.path_name)
        self.add_item(self.duration_weeks)

    async def on_submit(self, interaction: discord.Interaction):
        path_name = self.path_name.value
        duration_weeks = self.duration_weeks.value

        if not duration_weeks.isdigit():
            await interaction.response.send_message("Duration must be a number.", ephemeral=True)
            return

        duration_weeks = int(duration_weeks)
        data = {
            "name": path_name,
            "duration_weeks": duration_weeks
        }
        response = requests.post(f"{API_URL_PATHS}create/", json=data)
        if response.status_code == 201:
            await interaction.response.send_message(f'Path "{path_name}" added successfully with duration {duration_weeks} weeks.', ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to add path. Status code: {response.status_code}, Response: {response.text}", ephemeral=True)


class UpdatePathModal(discord.ui.Modal):
    def __init__(self, path_id, path_name, duration_weeks):
        super().__init__(title="Update Path")
        self.path_id = path_id

        self.path_name = discord.ui.TextInput(
            label="Path Name",
            required=True
        )
        self.path_name.default = path_name

        self.duration_weeks = discord.ui.TextInput(
            label="Duration (weeks)",
            required=True
        )
        self.duration_weeks.default = duration_weeks

        self.add_item(self.path_name)
        self.add_item(self.duration_weeks)

    async def on_submit(self, interaction: discord.Interaction):
        path_name = self.path_name.value
        duration_weeks = self.duration_weeks.value

        if not duration_weeks.isdigit():
            await interaction.response.send_message("Duration must be a number.", ephemeral=True)
            return

        duration_weeks = int(duration_weeks)
        data = {
            "name": path_name,
            "duration_weeks": duration_weeks
        }
        response = requests.put(f"{API_URL_PATHS}{self.path_id}/update/", json=data)
        if response.status_code == 200:
            await interaction.response.send_message(f'Path "{path_name}" updated successfully with duration {duration_weeks} weeks.', ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to update path. Status code: {response.status_code}, Response: {response.text}", ephemeral=True)


class ConfirmDeleteModal(discord.ui.Modal):
    def __init__(self, path_id, path_name):
        super().__init__(title="Confirm Deletion")
        self.path_id = path_id
        self.path_name = path_name

        # Add a TextInput field for the user to type the name of the path to confirm deletion
        self.confirmation = discord.ui.TextInput(
            label=f"Type '{path_name}' to confirm",
            placeholder=path_name,
            required=True
        )
        self.add_item(self.confirmation)

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmation.value != self.path_name:
            await interaction.response.send_message("Deletion cancelled. The typed name did not match.", ephemeral=True)
            return

        response = requests.delete(f"{API_URL_PATHS}{self.path_id}/delete/")
        if response.status_code == 204:
            await interaction.response.send_message(f'Path "{self.path_name}" deleted successfully.', ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to delete path. Status code: {response.status_code}, Response: {response.text}", ephemeral=True)


class PathButton(discord.ui.Button):
    def __init__(self, path):
        super().__init__(label=path['name'], style=discord.ButtonStyle.primary)
        self.path_id = path['id']
        self.path_name = path['name']
        self.duration_weeks = path['duration_weeks']

    async def callback(self, interaction: discord.Interaction):
        modal = UpdatePathModal(self.path_id, self.path_name, self.duration_weeks)
        await interaction.response.send_modal(modal)


class DeletePathButton(discord.ui.Button):
    def __init__(self, path):
        super().__init__(label=f"Delete {path['name']}", style=discord.ButtonStyle.danger)
        self.path_id = path['id']
        self.path_name = path['name']

    async def callback(self, interaction: discord.Interaction):
        modal = ConfirmDeleteModal(self.path_id, self.path_name)
        await interaction.response.send_modal(modal)

