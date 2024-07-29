
# topics/components.py
import discord
from discord.ui import Button, View, Modal, TextInput
from discord import ButtonStyle, Interaction, TextStyle
import requests

API_URL_TOPICS = "http://127.0.0.1:8000/api/topics/"
API_URL_PATHS = "http://127.0.0.1:8000/api/paths/"


class SelectPathButton(Button):
    def __init__(self, path, callback_id):
        super().__init__(label=path['name'], style=ButtonStyle.primary)
        self.path_id = path['id']
        self.path_name = path['name']
        self.callback_id = callback_id

    async def callback(self, interaction: Interaction):
        if self.callback_id == 'add_topic':
            await self.select_week(interaction, self.path_id, self.path_name, 'add_topic')
        elif self.callback_id == 'update_topic':
            await self.select_week(interaction, self.path_id, self.path_name, 'update_topic')
        elif self.callback_id == 'delete_topic':
            await self.select_week(interaction, self.path_id, self.path_name, 'delete_topic')
        elif self.callback_id == 'list_topics':
            await self.list_topics(interaction, self.path_id)

    async def select_week(self, interaction: Interaction, path_id, path_name, action):
        response = requests.get(f"{API_URL_PATHS}{path_id}/")
        if response.status_code == 200:
            path = response.json()
            weeks = list(range(1, path['duration_weeks'] + 1))
            view = View()
            for week in weeks:
                view.add_item(SelectWeekButton(path_id, path_name, week, action))

            await interaction.response.send_message(f"Select a week for {path_name}:", view=view, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch path details.", ephemeral=True)

    async def list_topics(self, interaction: Interaction, path_id):
        response = requests.get(f"{API_URL_TOPICS}list/")
        if response.status_code == 200:
            topics = response.json()
            topics = [topic for topic in topics if topic['path'] == path_id]
            if not topics:
                await interaction.response.send_message("No topics available for this path.", ephemeral=True)
                return
            
            # Sort topics by week in ascending order
            topics.sort(key=lambda x: x['week'])
            topic_list = "\n".join([f" ▫️ Week {topic['week']} - {topic['title']} " for topic in topics])
            await interaction.response.send_message(f"Topics for {self.path_name}:\n{topic_list}", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)
        #     topic_list = "\n".join([f" ▫️ Week {topic['week']} - {topic['title']} " for topic in topics])
        #     await interaction.response.send_message(f"Topics for {self.path_name}:\n{topic_list}", ephemeral=True)
        # else:
        #     await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)


class SelectWeekButton(Button):
    def __init__(self, path_id, path_name, week, action):
        super().__init__(label=f"Week {week}", style=ButtonStyle.primary)
        self.path_id = path_id
        self.path_name = path_name
        self.week = week
        self.action = action

    async def callback(self, interaction: Interaction):
        if self.action == 'add_topic':
            modal = TopicModal(self.path_id, self.path_name, self.week)
            await interaction.response.send_modal(modal)
        elif self.action in ['update_topic', 'delete_topic']:
            await self.select_topic(interaction, self.path_id, self.week, self.action)

    async def select_topic(self, interaction: Interaction, path_id, week, action):
        response = requests.get(f"{API_URL_TOPICS}list/")
        if response.status_code == 200:
            topics = response.json()
            topics = [topic for topic in topics if topic['path'] == path_id and topic['week'] == week]
            if not topics:
                await interaction.response.send_message("No topics available for this week.", ephemeral=True)
                return

            view = View()
            for topic in topics:
                if action == 'update_topic':
                    view.add_item(UpdateTopicButton(topic))
                elif action == 'delete_topic':
                    view.add_item(DeleteTopicButton(topic))

            await interaction.response.send_message(f"Select a topic to {action.split('_')[0]} in Week {week}:", view=view, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)


class TopicModal(Modal):
    def __init__(self, path_id, path_name, week):
        super().__init__(title=f"Add Topic to {path_name} - Week {week}")
        self.path_id = path_id
        self.week = week
        self.title_input = TextInput(label="Title", required=True)
        self.description_input = TextInput(label="Description", style=TextStyle.paragraph, required=False)
        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: Interaction):
        data = {
            "title": self.title_input.value,
            "week": self.week,
            "description": self.description_input.value,
            "path": self.path_id
        }
        response = requests.post(f"{API_URL_TOPICS}create/", json=data)  # Correct endpoint URL
        if response.status_code == 201:
            await interaction.response.send_message(f'Topic {data["title"]} added successfully.', ephemeral=True)
        else:
            error_message = f"Failed to add topic. Status code: {response.status_code}"
            print(error_message)
            await interaction.response.send_message(error_message, ephemeral=True)


class UpdateTopicButton(Button):
    def __init__(self, topic):
        super().__init__(label=f"Update {topic['title']}", style=ButtonStyle.primary)
        self.topic = topic

    async def callback(self, interaction: Interaction):
        modal = UpdateTopicModal(self.topic['id'], self.topic['title'], self.topic['week'], self.topic['description'])
        await interaction.response.send_modal(modal)


class UpdateTopicModal(Modal):
    def __init__(self, topic_id, title, week, description):
        super().__init__(title="Update Topic")
        self.topic_id = topic_id

        self.title_input = TextInput(label="Title", default=title, required=True)
        self.week_input = TextInput(label="Week", default=str(week), required=True)
        self.description_input = TextInput(label="Description", default=description, style=TextStyle.paragraph, required=False)
        self.add_item(self.title_input)
        self.add_item(self.week_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: Interaction):
        data = {
            "title": self.title_input.value,
            "week": int(self.week_input.value),
            "description": self.description_input.value
        }
        response = requests.put(f"{API_URL_TOPICS}{self.topic_id}/update/", json=data)
        if response.status_code == 200:
            await interaction.response.send_message(f'Topic "{self.title_input.value}" updated successfully.', ephemeral=True)  #change
        else:
            error_message = f"Failed to update topic. Status code: {response.status_code}, Response: {response.text}"  #change
            print(error_message)
            await interaction.response.send_message(error_message, ephemeral=True)
            

class DeleteTopicButton(Button):
    def __init__(self, topic):
        super().__init__(label=f"Delete {topic['title']}", style=ButtonStyle.danger)
        self.topic = topic

    async def callback(self, interaction: Interaction):
        modal = ConfirmDeleteModal(self.topic['id'], self.topic['title'])
        await interaction.response.send_modal(modal)


class ConfirmDeleteModal(Modal):
    def __init__(self, topic_id, topic_title):
        super().__init__(title="Confirm Deletion")
        self.topic_id = topic_id
        self.topic_title = topic_title

        self.confirmation = TextInput(
            label=f"Type '{self.topic_title}' to confirm",
            placeholder=self.topic_title,
            required=True
        )
        self.add_item(self.confirmation)

    async def on_submit(self, interaction: Interaction):
        if self.confirmation.value != self.topic_title:
            await interaction.response.send_message("Deletion cancelled.", ephemeral=True)
            return

        response = requests.delete(f"{API_URL_TOPICS}{self.topic_id}/delete/")
        if response.status_code == 204:
            await interaction.response.send_message(f'Topic "{self.topic_title}" deleted successfully.', ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to delete topic. Status code: {response.status_code}, Response: {response.text}", ephemeral=True)