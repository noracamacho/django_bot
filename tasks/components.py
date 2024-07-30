# tasks/components.py
import discord
from discord.ui import Button, View, Modal, TextInput
from discord import ButtonStyle, Interaction, TextStyle
import requests
from helpers.utils import fetch_topics, fetch_tasks

API_URL_TASKS = "http://127.0.0.1:8000/api/tasks/"
API_URL_TOPICS = "http://127.0.0.1:8000/api/topics/"

class TaskSelectPathButton(Button):
    def __init__(self, path, callback_id):
        super().__init__(label=path['name'], style=ButtonStyle.primary)
        self.path_id = path['id']
        self.path_name = path['name']
        self.callback_id = callback_id

    async def callback(self, interaction: Interaction):
        if self.callback_id == 'add_task':
            await self.select_topic(interaction, 'add_task')
        elif self.callback_id == 'update_task':
            await self.select_topic(interaction, 'update_task')
        elif self.callback_id == 'delete_task':
            await self.select_topic(interaction, 'delete_task')
        elif self.callback_id == 'list_tasks_by_topic':
            await self.select_topic(interaction, 'list_tasks_by_topic')
        elif self.callback_id == 'list_tasks':
            await self.list_tasks_for_path(interaction)

    async def select_topic(self, interaction: Interaction, action):
        topics = await fetch_topics(interaction, API_URL_TOPICS)
        if topics:
            topics = [topic for topic in topics if topic['path'] == self.path_id]
            if not topics:
                await interaction.response.send_message("No topics available for this path.", ephemeral=True)
                return

            view = View()
            for topic in topics:
                view.add_item(TaskSelectTopicButton(topic, action))
            await interaction.response.send_message(f"Select a topic for {self.path_name}:", view=view, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)
    
    
    async def list_tasks_for_path(self, interaction: Interaction):
        print(f"Listing tasks for path: {self.path_id}")
        topics = await fetch_topics(interaction, API_URL_TOPICS)
        if topics:
            topic_titles = {topic['id']: topic['title'] for topic in topics if topic['path'] == self.path_id}
            all_tasks = []
            for topic_id, topic_title in topic_titles.items():
                print(f"Fetching tasks for topic: {topic_title}")
                tasks = await fetch_tasks(interaction, API_URL_TASKS, topic_id)
                if tasks:
                    for task in tasks:
                        task['topic_title'] = topic_title
                    all_tasks.extend(tasks)
            if not all_tasks:
                print("No tasks available for this path.")
                await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
                return

            all_tasks.sort(key=lambda x: x['title'])
            print("All tasks available for this path: ", all_tasks)
            task_list = "\n".join([f" ▫️ {task['topic_title']} - {task['title']}" for task in all_tasks])
            print(f"Task list for path {self.path_id}: {task_list}")
            await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)

    # async def list_tasks_for_path(self, interaction: Interaction):
    #     print(f"Listing tasks for path: {self.path_id}")
    #     topics = await fetch_topics(interaction, API_URL_TOPICS)
    #     if topics:
    #         all_tasks = []
    #         for topic in topics:
    #             if topic['path'] == self.path_id:
    #                 print(f"Fetching tasks for topic: {topic['title']}")
    #                 tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
    #                 if tasks:
    #                     all_tasks.extend(tasks)
    #         if not all_tasks:
    #             print("No tasks available for this path.")
    #             await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
    #             return

    #         all_tasks.sort(key=lambda x: x['title'])
    #         print("All tasks available for this path: ", all_tasks)
    #         task_list = "\n".join([f" ▫️ {task['topic']} - {task['title']})" for task in all_tasks])
    #         print(f"Task list for path {self.path_id}: {task_list}")
    #         await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
    #     else:
    #         await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)

class TaskSelectTopicButton(Button):
    def __init__(self, topic, action):
        super().__init__(label=topic['title'], style=ButtonStyle.primary)
        self.topic_id = topic['id']
        self.topic_title = topic['title']
        self.action = action

    async def callback(self, interaction: Interaction):
        if self.action == 'add_task':
            modal = TaskModal(self.topic_id, self.topic_title)
            await interaction.response.send_modal(modal)
        elif self.action == 'update_task':
            await self.update_or_delete_task(interaction, 'update_task')
        elif self.action == 'delete_task':
            await self.update_or_delete_task(interaction, 'delete_task')
        elif self.action == 'list_tasks_by_topic':
            await self.list_tasks_by_topic(interaction)

    async def update_or_delete_task(self, interaction: Interaction, action):
        tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
        if tasks:
            view = View()
            for task in tasks:
                if action == 'update_task':
                    view.add_item(UpdateTaskButton(task))
                elif action == 'delete_task':
                    view.add_item(DeleteTaskButton(task))
            await interaction.response.send_message(f"Select a task to {action.split('_')[0]}:", view=view, ephemeral=True)
        else:
            await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)

    async def list_tasks_by_topic(self, interaction: Interaction):
        tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
        if tasks:
            task_list = "\n".join([f" ▫️ {task['title']}" for task in tasks])
            await interaction.response.send_message(f"Tasks for {self.topic_title}:\n{task_list}", ephemeral=True)
        else:
            await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)

class TaskModal(Modal):
    def __init__(self, topic_id, topic_title):
        super().__init__(title=f"Add Task to {topic_title}")
        self.topic_id = topic_id
        self.topic_title = topic_title

        self.title_input = TextInput(label="Title", required=True)
        self.description_input = TextInput(label="Description", style=TextStyle.paragraph, required=False)

        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: Interaction):
        data = {
            "title": self.title_input.value,
            "description": self.description_input.value,
            "topic": self.topic_id
        }
        response = requests.post(f"{API_URL_TASKS}create/", json=data)
        if response.status_code == 201:
            await interaction.response.send_message(f'Task "{data["title"]}" added successfully to {self.topic_title}.', ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to add task. Status code: {response.status_code}", ephemeral=True)

class UpdateTaskButton(Button):
    def __init__(self, task):
        super().__init__(label=f"Update {task['title']}", style=ButtonStyle.primary)
        self.task = task

    async def callback(self, interaction: Interaction):
        modal = UpdateTaskModal(self.task['id'], self.task['title'], self.task['description'])
        await interaction.response.send_modal(modal)

class UpdateTaskModal(Modal):
    def __init__(self, task_id, title, description):
        super().__init__(title="Update Task")
        self.task_id = task_id

        self.title_input = TextInput(label="Title", default=title, required=True)
        self.description_input = TextInput(label="Description", default=description, style=TextStyle.paragraph, required=False)

        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: Interaction):
        data = {
            "title": self.title_input.value,
            "description": self.description_input.value
        }
        response = requests.put(f"{API_URL_TASKS}{self.task_id}/update/", json=data)
        if response.status_code == 200:
            await interaction.response.send_message(f'Task "{data["title"]}" updated successfully.', ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to update task. Status code: {response.status_code}", ephemeral=True)

class DeleteTaskButton(Button):
    def __init__(self, task):
        super().__init__(label=f"Delete {task['title']}", style=ButtonStyle.danger)
        self.task_id = task['id']
        self.task_title = task['title']

    async def callback(self, interaction: Interaction):
        modal = ConfirmDeleteTaskModal(self.task_id, self.task_title)
        await interaction.response.send_modal(modal)

class ConfirmDeleteTaskModal(Modal):
    def __init__(self, task_id, task_title):
        super().__init__(title="Confirm Deletion")
        self.task_id = task_id
        self.task_title = task_title

        self.confirmation = TextInput(
            label=f"Type '{self.task_title}' to confirm",
            placeholder=self.task_title,
            required=True
        )
        self.add_item(self.confirmation)

    async def on_submit(self, interaction: Interaction):
        if self.confirmation.value != self.task_title:
            await interaction.response.send_message("Deletion cancelled.", ephemeral=True)
            return

        response = requests.delete(f"{API_URL_TASKS}{self.task_id}/delete/")
        if response.status_code == 204:
            await interaction.response.send_message(f'Task "{self.task_title}" deleted successfully.', ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to delete task. Status code: {response.status_code}", ephemeral=True)



class WeekPaginator(View):
    def __init__(self, pages):
        super().__init__()
        self.pages = pages
        self.current_page = 0
        self.previous_button = Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="previous_page")
        self.next_button = Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next_page")
        self.update_buttons()
        self.add_item(self.previous_button)
        self.add_item(self.next_button)

    @property
    def page_content(self):
        return self.pages[self.current_page]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "previous_page":
            if self.current_page > 0:
                self.current_page -= 1
                self.update_buttons()
                await interaction.response.edit_message(content=self.page_content, view=self)
            return False
        elif interaction.data["custom_id"] == "next_page":
            if self.current_page < len(self.pages) - 1:
                self.current_page += 1
                self.update_buttons()
                await interaction.response.edit_message(content=self.page_content, view=self)
            return False
        return True

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1




# # tasks/components.py
# import discord
# from discord.ui import Button, View, Modal, TextInput
# from discord import ButtonStyle, Interaction, TextStyle
# import requests
# from helpers.utils import fetch_topics, fetch_tasks

# API_URL_TASKS = "http://127.0.0.1:8000/api/tasks/"
# API_URL_TOPICS = "http://127.0.0.1:8000/api/topics/"

# class TaskSelectPathButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathButton callback triggered for path_id: {self.path_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'list_tasks_by_topic':
#             response = requests.get(f"{API_URL_TOPICS}list/")
#             print(f"Fetched topics response status: {response.status_code}")
#             if response.status_code == 200:
#                 topics = response.json()
#                 topics = [topic for topic in topics if topic['path'] == self.path_id]
#                 if not topics:
#                     print("No topics available for this path.")
#                     await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                     return
#                 view = View()
#                 for topic in topics:
#                     print(f"Adding topic button for: {topic['title']}")
#                     view.add_item(TaskSelectTopicButton(topic, self.callback_id))
#                 await interaction.response.send_message(f"Select a topic for {self.path_name}:", view=view, ephemeral=True)
#             elif response.status_code == 404:
#                 print("No topics found.")
#                 await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                 return
#             else:
#                 print("Failed to fetch topics inside TaskSelectPathButton")
#                 await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)
#         else:
#             await self.list_tasks_for_path(interaction)

#     async def list_tasks_for_path(self, interaction: Interaction):
#         print(f"Listing tasks for path: {self.path_id}")
#         topics = await fetch_topics(interaction, API_URL_TOPICS)
#         if topics:
#             all_tasks = []
#             for topic in topics:
#                 if topic['path'] == self.path_id:
#                     print(f"Fetching tasks for topic: {topic['title']}")
#                     tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
#                     if tasks:
#                         all_tasks.extend(tasks)
#             if not all_tasks:
#                 print("No tasks available for this path.")
#                 await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
#                 return
            
#             all_tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']} (Topic: {task['topic']})" for task in all_tasks])
#             print(f"Task list for path 2 {self.path_id}: {task_list}")
#             await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)


# class TaskSelectPathForListingButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathForListingButton callback triggered for path_id: {self.path_id}")
#         topics = await fetch_topics(interaction, API_URL_TOPICS)
#         if topics:
#             all_tasks = []
#             for topic in topics:
#                 if topic['path'] == self.path_id:
#                     print(f"Fetching tasks for topic: {topic['title']}")
#                     tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
#                     if tasks:
#                         all_tasks.extend(tasks)
#             if not all_tasks:
#                 print("No tasks available for this path.")
#                 await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
#                 return
            
#             all_tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']} (Topic: {task['topic']})" for task in all_tasks])
#             print(f"Task list for path {self.path_id}: {task_list}")
#             await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             print("Failed to fetch topics inside TaskSelectPathForListingButton")
#             await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)

# class TaskSelectTopicButton(Button):
#     def __init__(self, topic, callback_id):
#         super().__init__(label=topic['title'], style=ButtonStyle.primary)
#         self.topic_id = topic['id']
#         self.topic_title = topic['title']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectTopicButton callback triggered for topic_id: {self.topic_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'add_task':
#             print("Creating TaskModal for adding task")
#             modal = TaskModal(self.topic_id, self.topic_title)
#             await interaction.response.send_modal(modal)
#         elif self.callback_id == 'list_tasks_by_topic':
#             print(f"Fetching tasks for topic: {self.topic_title}")
#             tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
#             if tasks:
#                 task_list = "\n".join([f"▫️ {task['title']}" for task in tasks])
#                 print(f"Task list for topic {self.topic_id}: {task_list}")
#                 await interaction.response.send_message(f"Tasks for {self.topic_title}:\n{task_list}", ephemeral=True)
#             else:
#                 print("No tasks available for this topic.")
#                 await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)
#         elif self.callback_id in ['update_task', 'delete_task', 'list_tasks']:
#             print(f"Fetching tasks for topic: {self.topic_title}")
#             tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
#             if tasks:
#                 view = View()
#                 for task in tasks:
#                     if self.callback_id == 'update_task':
#                         view.add_item(UpdateTaskButton(task))
#                     elif self.callback_id == 'delete_task':
#                         view.add_item(DeleteTaskButton(task))
#                 await interaction.response.send_message(f"Select a task to {self.callback_id.split('_')[0]}:", view=view, ephemeral=True)
#             else:
#                 print("No tasks available for this topic.")
#                 await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)



# # class TaskSelectTopicButton(Button):
# #     def __init__(self, topic, callback_id):
# #         super().__init__(label=topic['title'], style=ButtonStyle.primary)
# #         self.topic_id = topic['id']
# #         self.topic_title = topic['title']
# #         self.callback_id = callback_id

# #     async def callback(self, interaction: Interaction):
# #         print(f"TaskSelectTopicButton callback triggered for topic_id: {self.topic_id}, callback_id: {self.callback_id}")
# #         if self.callback_id == 'add_task':
# #             print("Creating TaskModal for adding task")
# #             modal = TaskModal(self.topic_id, self.topic_title)
# #             await interaction.response.send_modal(modal)
# #         elif self.callback_id in ['update_task', 'delete_task', 'list_tasks']:
# #             print(f"Fetching tasks for topic: {self.topic_title}")
# #             tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
# #             if tasks:
# #                 if self.callback_id == 'list_tasks':
# #                     task_list = "\n".join([f"▫️ {task['title']}" for task in tasks])
# #                     print(f"Task list for topic {self.topic_id}: {task_list}")
# #                     await interaction.response.send_message(f"Tasks for {self.topic_title}:\n{task_list}", ephemeral=True)
# #                 else:
# #                     view = View()
# #                     for task in tasks:
# #                         if self.callback_id == 'update_task':
# #                             view.add_item(UpdateTaskButton(task))
# #                         elif self.callback_id == 'delete_task':
# #                             view.add_item(DeleteTaskButton(task))
# #                     await interaction.response.send_message(f"Select a task to {self.callback_id.split('_')[0]}:", view=view, ephemeral=True)
# #             else:
# #                 print("No tasks available for this topic.")
# #                 await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)


# class TaskModal(Modal):
#     def __init__(self, topic_id, topic_title):
#         super().__init__(title=f"Add Task to {topic_title}")
#         self.topic_id = topic_id

#         self.title_input = TextInput(label="Title", required=True)
#         self.description_input = TextInput(label="Description", style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         print(f"Submitting TaskModal for topic_id: {self.topic_id}")
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value,
#             "topic": self.topic_id
#         }
#         response = requests.post(f"{API_URL_TASKS}create/", json=data)
#         print(f"API URL: {API_URL_TASKS}create/")
#         print(f"Payload: {data}")
#         print(f"Response Status Code: {response.status_code}")
#         print(f"Response Content: {response.content}")
#         if response.status_code == 201:
#             await interaction.response.send_message(f'Task "{data["title"]}" added successfully to {self.topic_title}.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to add task. Status code: {response.status_code}", ephemeral=True)


# class UpdateTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Update {task['title']}", style=ButtonStyle.primary)
#         self.task = task

#     async def callback(self, interaction: Interaction):
#         modal = UpdateTaskModal(self.task['id'], self.task['title'], self.task['description'])
#         await interaction.response.send_modal(modal)


# class UpdateTaskModal(Modal):
#     def __init__(self, task_id, title, description):
#         super().__init__(title="Update Task")
#         self.task_id = task_id

#         self.title_input = TextInput(label="Title", default=title, required=True)
#         self.description_input = TextInput(label="Description", default=description, style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value
#         }
#         response = requests.put(f"{API_URL_TASKS}{self.task_id}/update/", json=data)
#         if response.status_code == 200:
#             await interaction.response.send_message(f'Task "{data["title"]}" updated successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to update task. Status code: {response.status_code}", ephemeral=True)


# class DeleteTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Delete {task['title']}", style=ButtonStyle.danger)
#         self.task_id = task['id']
#         self.task_title = task['title']

#     async def callback(self, interaction: Interaction):
#         modal = ConfirmDeleteTaskModal(self.task_id, self.task_title)
#         await interaction.response.send_modal(modal)


# class ConfirmDeleteTaskModal(Modal):
#     def __init__(self, task_id, task_title):
#         super().__init__(title="Confirm Deletion")
#         self.task_id = task_id
#         self.task_title = task_title

#         self.confirmation = TextInput(
#             label=f"Type '{self.task_title}' to confirm",
#             placeholder=self.task_title,
#             required=True
#         )
#         self.add_item(self.confirmation)

#     async def on_submit(self, interaction: Interaction):
#         if self.confirmation.value != self.task_title:
#             await interaction.response.send_message("Deletion cancelled.", ephemeral=True)
#             return

#         response = requests.delete(f"{API_URL_TASKS}{self.task_id}/delete/")
#         if response.status_code == 204:
#             await interaction.response.send_message(f'Task "{self.task_title}" deleted successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to delete task. Status code: {response.status_code}", ephemeral=True)



# # tasks/components.py
# import discord
# from discord.ui import Button, View, Modal, TextInput
# from discord import ButtonStyle, Interaction, TextStyle
# import requests
# from helpers.utils import fetch_topics, fetch_tasks

# API_URL_TASKS = "http://127.0.0.1:8000/api/tasks/"
# API_URL_TOPICS = "http://127.0.0.1:8000/api/topics/"

# class TaskSelectPathButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathButton callback triggered for path_id: {self.path_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'list_tasks_by_topic':
#             response = requests.get(f"{API_URL_TOPICS}list/")
#             if response.status_code == 200:
#                 topics = response.json()
#                 topics = [topic for topic in topics if topic['path'] == self.path_id]
#                 if not topics:
#                     await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                     return
#                 view = View()
#                 for topic in topics:
#                     view.add_item(TaskSelectTopicButton(topic, self.callback_id))
#                 await interaction.response.send_message(f"Select a topic for {self.path_name}:", view=view, ephemeral=True)
#             else:
#                 print("Failed to fetch topics inside TaskSelectPathButton")
#                 await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)
#         else:
#             await self.list_tasks_for_path(interaction)

#     async def list_tasks_for_path(self, interaction: Interaction):
#         print("Listing tasks for path")
#         topics = await fetch_topics(interaction, API_URL_TOPICS)
#         if topics:
#             all_tasks = []
#             for topic in topics:
#                 if topic['path'] == self.path_id:
#                     tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
#                     if tasks:
#                         all_tasks.extend(tasks)
#             if not all_tasks:
#                 await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
#                 return
            
#             all_tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']} (Topic: {task['topic']})" for task in all_tasks])
#             await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)


# class TaskSelectPathForListingButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathForListingButton callback triggered for path_id: {self.path_id}")
#         topics = await fetch_topics(interaction, API_URL_TOPICS)
#         if topics:
#             all_tasks = []
#             for topic in topics:
#                 if topic['path'] == self.path_id:
#                     tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
#                     if tasks:
#                         all_tasks.extend(tasks)
#             if not all_tasks:
#                 await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
#                 return
            
#             all_tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']} (Topic: {task['topic']})" for task in all_tasks])
#             await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)


# class TaskSelectTopicButton(Button):
#     def __init__(self, topic, callback_id):
#         super().__init__(label=topic['title'], style=ButtonStyle.primary)
#         self.topic_id = topic['id']
#         self.topic_title = topic['title']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectTopicButton callback triggered for topic_id: {self.topic_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'add_task':
#             modal = TaskModal(self.topic_id, self.topic_title)
#             await interaction.response.send_modal(modal)
#         elif self.callback_id in ['update_task', 'delete_task', 'list_tasks']:
#             print('update_task', 'delete_task', 'list_tasks')
#             tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
#             if tasks:
#                 if self.callback_id == 'list_tasks':
#                     task_list = "\n".join([f"▫️ {task['title']}" for task in tasks])
#                     await interaction.response.send_message(f"Tasks for {self.topic_title}:\n{task_list}", ephemeral=True)
#                 else:
#                     view = View()
#                     for task in tasks:
#                         if self.callback_id == 'update_task':
#                             view.add_item(UpdateTaskButton(task))
#                         elif self.callback_id == 'delete_task':
#                             view.add_item(DeleteTaskButton(task))
#                     await interaction.response.send_message(f"Select a task to {self.callback_id.split('_')[0]}:", view=view, ephemeral=True)
#             else:
#                 await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)


# class TaskModal(Modal):
#     def __init__(self, topic_id, topic_title):
#         super().__init__(title=f"Add Task to {topic_title}")
#         self.topic_id = topic_id

#         self.title_input = TextInput(label="Title", required=True)
#         self.description_input = TextInput(label="Description", style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         print(f"Submitting TaskModal for topic_id: {self.topic_id}")
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value,
#             "topic": self.topic_id
#         }
#         response = requests.post(f"{API_URL_TASKS}create/", json=data)
#         print(f"API URL: {API_URL_TASKS}create/")
#         print(f"Payload: {data}")
#         print(f"Response Status Code: {response.status_code}")
#         print(f"Response Content: {response.content}")
#         if response.status_code == 201:
#             await interaction.response.send_message(f'Task "{data["title"]}" added successfully to {self.topic_title}.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to add task. Status code: {response.status_code}", ephemeral=True)


# class UpdateTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Update {task['title']}", style=ButtonStyle.primary)
#         self.task = task

#     async def callback(self, interaction: Interaction):
#         modal = UpdateTaskModal(self.task['id'], self.task['title'], self.task['description'])
#         await interaction.response.send_modal(modal)


# class UpdateTaskModal(Modal):
#     def __init__(self, task_id, title, description):
#         super().__init__(title="Update Task")
#         self.task_id = task_id

#         self.title_input = TextInput(label="Title", default=title, required=True)
#         self.description_input = TextInput(label="Description", default=description, style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value
#         }
#         response = requests.put(f"{API_URL_TASKS}{self.task_id}/update/", json=data)
#         if response.status_code == 200:
#             await interaction.response.send_message(f'Task "{data["title"]}" updated successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to update task. Status code: {response.status_code}", ephemeral=True)


# class DeleteTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Delete {task['title']}", style=ButtonStyle.danger)
#         self.task_id = task['id']
#         self.task_title = task['title']

#     async def callback(self, interaction: Interaction):
#         modal = ConfirmDeleteTaskModal(self.task_id, self.task_title)
#         await interaction.response.send_modal(modal)


# class ConfirmDeleteTaskModal(Modal):
#     def __init__(self, task_id, task_title):
#         super().__init__(title="Confirm Deletion")
#         self.task_id = task_id
#         self.task_title = task_title

#         self.confirmation = TextInput(
#             label=f"Type '{self.task_title}' to confirm",
#             placeholder=self.task_title,
#             required=True
#         )
#         self.add_item(self.confirmation)

#     async def on_submit(self, interaction: Interaction):
#         if self.confirmation.value != self.task_title:
#             await interaction.response.send_message("Deletion cancelled.", ephemeral=True)
#             return

#         response = requests.delete(f"{API_URL_TASKS}{self.task_id}/delete/")
#         if response.status_code == 204:
#             await interaction.response.send_message(f'Task "{self.task_title}" deleted successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to delete task. Status code: {response.status_code}", ephemeral=True)





# tasks/components.py
# import discord
# from discord.ui import Button, View, Modal, TextInput
# from discord import ButtonStyle, Interaction, TextStyle
# import requests
# from helpers.utils import fetch_topics, fetch_tasks

# API_URL_TASKS = "http://127.0.0.1:8000/api/tasks/"
# API_URL_TOPICS = "http://127.0.0.1:8000/api/topics/"

# class TaskSelectPathButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathButton callback triggered for path_id: {self.path_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'list_tasks_by_topic':
#             response = requests.get(f"{API_URL_TOPICS}list/")
#             if response.status_code == 200:
#                 topics = response.json()
#                 topics = [topic for topic in topics if topic['path'] == self.path_id]
#                 if not topics:
#                     await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                     return
#                 view = View()
#                 for topic in topics:
#                     view.add_item(TaskSelectTopicButton(topic, self.callback_id))
#                 await interaction.response.send_message(f"Select a topic for {self.path_name}:", view=view, ephemeral=True)
#             elif response.status_code == 404:
#                 await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                 return
#             else:
#                 print("Failed to fetch topics inside TaskSelectPathButton")
#                 await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)
#         else:
#             await self.list_tasks_for_path(interaction)

#     async def list_tasks_for_path(self, interaction: Interaction):
#         print("Listing tasks for path")
#         topics = await fetch_topics(interaction, API_URL_TOPICS)
#         if topics:
#             all_tasks = []
#             for topic in topics:
#                 if topic['path'] == self.path_id:
#                     tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
#                     if tasks:
#                         all_tasks.extend(tasks)
#             if not all_tasks:
#                 await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
#                 return
            
#             all_tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']} (Topic: {task['topic']})" for task in all_tasks])
#             await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)


# class TaskSelectPathForListingButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathForListingButton callback triggered for path_id: {self.path_id}")
#         topics = await fetch_topics(interaction, API_URL_TOPICS)
#         if topics:
#             all_tasks = []
#             for topic in topics:
#                 if topic['path'] == self.path_id:
#                     tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
#                     if tasks:
#                         all_tasks.extend(tasks)
#             if not all_tasks:
#                 await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
#                 return
            
#             all_tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']} (Topic: {task['topic']})" for task in all_tasks])
#             await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)


# class TaskSelectTopicButton(Button):
#     def __init__(self, topic, callback_id):
#         super().__init__(label=topic['title'], style=ButtonStyle.primary)
#         self.topic_id = topic['id']
#         self.topic_title = topic['title']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectTopicButton callback triggered for topic_id: {self.topic_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'add_task':
#             modal = TaskModal(self.topic_id, self.topic_title)
#             await interaction.response.send_modal(modal)
#         elif self.callback_id in ['update_task', 'delete_task', 'list_tasks']:
#             tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
#             if tasks:
#                 if self.callback_id == 'list_tasks':
#                     task_list = "\n".join([f"▫️ {task['title']}" for task in tasks])
#                     await interaction.response.send_message(f"Tasks for {self.topic_title}:\n{task_list}", ephemeral=True)
#                 else:
#                     view = View()
#                     for task in tasks:
#                         if self.callback_id == 'update_task':
#                             view.add_item(UpdateTaskButton(task))
#                         elif self.callback_id == 'delete_task':
#                             view.add_item(DeleteTaskButton(task))
#                     await interaction.response.send_message(f"Select a task to {self.callback_id.split('_')[0]}:", view=view, ephemeral=True)
#             else:
#                 await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)


# class TaskModal(Modal):
#     def __init__(self, topic_id, topic_title):
#         super().__init__(title=f"Add Task to {topic_title}")
#         self.topic_id = topic_id

#         self.title_input = TextInput(label="Title", required=True)
#         self.description_input = TextInput(label="Description", style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         print(f"Submitting TaskModal for topic_id: {self.topic_id}")
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value,
#             "topic": self.topic_id
#         }
#         response = requests.post(f"{API_URL_TASKS}create/", json=data)
#         print(f"API URL: {API_URL_TASKS}create/")
#         print(f"Payload: {data}")
#         print(f"Response Status Code: {response.status_code}")
#         print(f"Response Content: {response.content}")
#         if response.status_code == 201:
#             await interaction.response.send_message(f'Task "{data["title"]}" added successfully to {self.topic_title}.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to add task. Status code: {response.status_code}", ephemeral=True)


# class UpdateTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Update {task['title']}", style=ButtonStyle.primary)
#         self.task = task

#     async def callback(self, interaction: Interaction):
#         modal = UpdateTaskModal(self.task['id'], self.task['title'], self.task['description'])
#         await interaction.response.send_modal(modal)


# class UpdateTaskModal(Modal):
#     def __init__(self, task_id, title, description):
#         super().__init__(title="Update Task")
#         self.task_id = task_id

#         self.title_input = TextInput(label="Title", default=title, required=True)
#         self.description_input = TextInput(label="Description", default=description, style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value
#         }
#         response = requests.put(f"{API_URL_TASKS}{self.task_id}/update/", json=data)
#         if response.status_code == 200:
#             await interaction.response.send_message(f'Task "{data["title"]}" updated successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to update task. Status code: {response.status_code}", ephemeral=True)


# class DeleteTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Delete {task['title']}", style=ButtonStyle.danger)
#         self.task_id = task['id']
#         self.task_title = task['title']

#     async def callback(self, interaction: Interaction):
#         modal = ConfirmDeleteTaskModal(self.task_id, self.task_title)
#         await interaction.response.send_modal(modal)


# class ConfirmDeleteTaskModal(Modal):
#     def __init__(self, task_id, task_title):
#         super().__init__(title="Confirm Deletion")
#         self.task_id = task_id
#         self.task_title = task_title

#         self.confirmation = TextInput(
#             label=f"Type '{self.task_title}' to confirm",
#             placeholder=self.task_title,
#             required=True
#         )
#         self.add_item(self.confirmation)

#     async def on_submit(self, interaction: Interaction):
#         if self.confirmation.value != self.task_title:
#             await interaction.response.send_message("Deletion cancelled.", ephemeral=True)
#             return

#         response = requests.delete(f"{API_URL_TASKS}{self.task_id}/delete/")
#         if response.status_code == 204:
#             await interaction.response.send_message(f'Task "{self.task_title}" deleted successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to delete task. Status code: {response.status_code}", ephemeral=True)



# import discord
# from discord.ui import Button, View, Modal, TextInput
# from discord import ButtonStyle, Interaction, TextStyle
# import requests
# from helpers.utils import fetch_topics, fetch_tasks

# API_URL_TASKS = "http://127.0.0.1:8000/api/tasks/"
# API_URL_TOPICS = "http://127.0.0.1:8000/api/topics/"

# class TaskSelectPathButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathButton callback triggered for path_id: {self.path_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'list_tasks_by_path':
#             await self.list_tasks_for_path(interaction)
#         else:
#             response = requests.get(f"{API_URL_TOPICS}list/")
#             if response.status_code == 200:
#                 topics = response.json()
#                 topics = [topic for topic in topics if topic['path'] == self.path_id]
#                 if not topics:
#                     await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                     return
#                 view = View()
#                 for topic in topics:
#                     view.add_item(TaskSelectTopicButton(topic, self.callback_id))
#                 await interaction.response.send_message(f"Select a topic for {self.path_name}:", view=view, ephemeral=True)
#             elif response.status_code == 404:
#                 await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                 return
#             else:
#                 print("Failed to fetch topics inside TaskSelectPathButton")
#                 await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)

#     async def list_tasks_for_path(self, interaction: Interaction):
#         print("Listing tasks for path")
#         tasks = await fetch_tasks(interaction, API_URL_TASKS, self.path_id)
#         if tasks:
#             tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']}" for task in tasks])
#             await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             await interaction.response.send_message("No tasks available for this path.", ephemeral=True)


# class TaskSelectPathForListingButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathForListingButton callback triggered for path_id: {self.path_id}")
#         topics = await fetch_topics(interaction, API_URL_TOPICS)
#         if topics:
#             all_tasks = []
#             for topic in topics:
#                 if topic['path'] == self.path_id:
#                     tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
#                     if tasks:
#                         all_tasks.extend(tasks)
#             if not all_tasks:
#                 await interaction.response.send_message("No tasks available for this path.", ephemeral=True)
#                 return
            
#             all_tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']} (Topic: {task['topic']})" for task in all_tasks])
#             await interaction.response.send_message(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)


# class TaskSelectTopicButton(Button):
#     def __init__(self, topic, callback_id):
#         super().__init__(label=topic['title'], style=ButtonStyle.primary)
#         self.topic_id = topic['id']
#         self.topic_title = topic['title']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectTopicButton callback triggered for topic_id: {self.topic_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'add_task':
#             modal = TaskModal(self.topic_id, self.topic_title)
#             await interaction.response.send_modal(modal)
#         elif self.callback_id in ['update_task', 'delete_task', 'list_tasks']:
#             tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
#             if tasks:
#                 if self.callback_id == 'list_tasks':
#                     task_list = "\n".join([f"▫️ {task['title']}" for task in tasks])
#                     await interaction.response.send_message(f"Tasks for {self.topic_title}:\n{task_list}", ephemeral=True)
#                 else:
#                     view = View()
#                     for task in tasks:
#                         if self.callback_id == 'update_task':
#                             view.add_item(UpdateTaskButton(task))
#                         elif self.callback_id == 'delete_task':
#                             view.add_item(DeleteTaskButton(task))
#                     await interaction.response.send_message(f"Select a task to {self.callback_id.split('_')[0]}:", view=view, ephemeral=True)
#             else:
#                 await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)


# class TaskModal(Modal):
#     def __init__(self, topic_id, topic_title):
#         super().__init__(title=f"Add Task to {topic_title}")
#         self.topic_id = topic_id

#         self.title_input = TextInput(label="Title", required=True)
#         self.description_input = TextInput(label="Description", style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         print(f"Submitting TaskModal for topic_id: {self.topic_id}")
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value,
#             "topic": self.topic_id
#         }
#         response = requests.post(f"{API_URL_TASKS}create/", json=data)
#         print(f"API URL: {API_URL_TASKS}create/")
#         print(f"Payload: {data}")
#         print(f"Response Status Code: {response.status_code}")
#         print(f"Response Content: {response.content}")
#         if response.status_code == 201:
#             await interaction.response.send_message(f'Task "{data["title"]}" added successfully to {self.topic_title}.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to add task. Status code: {response.status_code}", ephemeral=True)


# class UpdateTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Update {task['title']}", style=ButtonStyle.primary)
#         self.task = task

#     async def callback(self, interaction: Interaction):
#         modal = UpdateTaskModal(self.task['id'], self.task['title'], self.task['description'])
#         await interaction.response.send_modal(modal)


# class UpdateTaskModal(Modal):
#     def __init__(self, task_id, title, description):
#         super().__init__(title="Update Task")
#         self.task_id = task_id

#         self.title_input = TextInput(label="Title", default=title, required=True)
#         self.description_input = TextInput(label="Description", default=description, style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value
#         }
#         response = requests.put(f"{API_URL_TASKS}{self.task_id}/update/", json=data)
#         if response.status_code == 200:
#             await interaction.response.send_message(f'Task "{data["title"]}" updated successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to update task. Status code: {response.status_code}", ephemeral=True)


# class DeleteTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Delete {task['title']}", style=ButtonStyle.danger)
#         self.task_id = task['id']
#         self.task_title = task['title']

#     async def callback(self, interaction: Interaction):
#         modal = ConfirmDeleteTaskModal(self.task_id, self.task_title)
#         await interaction.response.send_modal(modal)


# class ConfirmDeleteTaskModal(Modal):
#     def __init__(self, task_id, task_title):
#         super().__init__(title="Confirm Deletion")
#         self.task_id = task_id
#         self.task_title = task_title

#         self.confirmation = TextInput(
#             label=f"Type '{self.task_title}' to confirm",
#             placeholder=self.task_title,
#             required=True
#         )
#         self.add_item(self.confirmation)

#     async def on_submit(self, interaction: Interaction):
#         if self.confirmation.value != self.task_title:
#             await interaction.response.send_message("Deletion cancelled.", ephemeral=True)
#             return

#         response = requests.delete(f"{API_URL_TASKS}{self.task_id}/delete/")
#         if response.status_code == 204:
#             await interaction.response.send_message(f'Task "{self.task_title}" deleted successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to delete task. Status code: {response.status_code}", ephemeral=True)


# import discord
# from discord.ui import Button, View, Modal, TextInput
# from discord import ButtonStyle, Interaction, TextStyle
# import requests
# import json
# from helpers.utils import fetch_topics, fetch_tasks

# API_URL_TASKS = "http://127.0.0.1:8000/api/tasks/"
# API_URL_TOPICS = "http://127.0.0.1:8000/api/topics/"

# class TaskSelectPathButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathButton callback triggered for path_id: {self.path_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'list_tasks_by_path':
#             await self.list_tasks_for_path(interaction)
#         else:
#             response = requests.get(f"{API_URL_TOPICS}list/")
#             if response.status_code == 200:
#                 topics = response.json()
#                 topics = [topic for topic in topics if topic['path'] == self.path_id]
#                 if not topics:
#                     await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                     return
#                 view = View()
#                 for topic in topics:
#                     view.add_item(TaskSelectTopicButton(topic, self.callback_id))
#                 await interaction.response.send_message(f"Select a topic for {self.path_name}:", view=view, ephemeral=True)
#             elif response.status_code == 404:
#                 await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#                 return
#             else:
#                 print("Failed to fetch topics inside TaskSelectPathButton")
#                 await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)

#     async def list_tasks_for_path(self, interaction: Interaction):
#         topics = await fetch_topics(interaction, API_URL_TOPICS)
#         if topics:
#             topics = [topic for topic in topics if topic['path'] == self.path_id]
#             all_tasks = []
#             for topic in topics:
#                 tasks = await fetch_tasks(interaction, API_URL_TASKS, topic['id'])
#                 if tasks:
#                     all_tasks.extend(tasks)
#             if not all_tasks:
#                 await interaction.followup.send("No tasks available for this path.", ephemeral=True)
#                 return
            
#             all_tasks.sort(key=lambda x: x['title'])
#             task_list = "\n".join([f" ▫️ {task['title']} (Topic: {task['topic']})" for task in all_tasks])
#             await interaction.followup.send(f"Tasks for {self.path_name}:\n{task_list}", ephemeral=True)
#         else:
#             await interaction.followup.send("Failed to fetch topics.", ephemeral=True)

# class TaskSelectTopicButton(Button):
#     def __init__(self, topic, callback_id):
#         super().__init__(label=topic['title'], style=ButtonStyle.primary)
#         self.topic_id = topic['id']
#         self.topic_title = topic['title']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectTopicButton callback triggered for topic_id: {self.topic_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'add_task':
#             modal = TaskModal(self.topic_id, self.topic_title)
#             await interaction.response.send_modal(modal)
#         elif self.callback_id in ['update_task', 'delete_task', 'list_tasks']:
#             tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
#             if tasks:
#                 if self.callback_id == 'list_tasks':
#                     task_list = "\n".join([f"▫️ {task['title']}" for task in tasks])
#                     await interaction.response.send_message(f"Tasks for {self.topic_title}:\n{task_list}", ephemeral=True)
#                 else:
#                     view = View()
#                     for task in tasks:
#                         if self.callback_id == 'update_task':
#                             view.add_item(UpdateTaskButton(task))
#                         elif self.callback_id == 'delete_task':
#                             view.add_item(DeleteTaskButton(task))
#                     await interaction.response.send_message(f"Select a task to {self.callback_id.split('_')[0]}:", view=view, ephemeral=True)
#             else:
#                 await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)

# async def fetch_tasks(interaction, api_url_tasks, topic_id):
#     response = requests.get(f"{api_url_tasks}list/")
#     if response.status_code == 200:
#         try:
#             tasks = response.json()
#         except json.JSONDecodeError:
#             await interaction.response.send_message("Failed to parse tasks.", ephemeral=True)
#             return None
#         tasks = [task for task in tasks if task['topic'] == topic_id]
#         if not tasks:
#             await interaction.response.send_message("No tasks available.", ephemeral=True)
#             return None
#         return tasks
#     else:
#         await interaction.response.send_message("Failed to fetch tasks.", ephemeral=True)
#         return None

# class TaskModal(Modal):
#     def __init__(self, topic_id, topic_title):
#         super().__init__(title=f"Add Task to {topic_title}")
#         self.topic_id = topic_id
#         self.topic_title = topic_title

#         self.title_input = TextInput(label="Title", required=True)
#         self.description_input = TextInput(label="Description", style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         print(f"Submitting TaskModal for topic_id: {self.topic_id}")
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value,
#             "topic": self.topic_id
#         }
#         response = requests.post(f"{API_URL_TASKS}create/", json=data)
#         print(f"API URL: {API_URL_TASKS}create/")
#         print(f"Payload: {data}")
#         print(f"Response Status Code: {response.status_code}")
#         print(f"Response Content: {response.content}")
#         if response.status_code == 201:
#             await interaction.response.send_message(f'Task "{data["title"]}" added successfully to {self.topic_title}.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to add task. Status code: {response.status_code}", ephemeral=True)

# class UpdateTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Update {task['title']}", style=ButtonStyle.primary)
#         self.task = task

#     async def callback(self, interaction: Interaction):
#         modal = UpdateTaskModal(self.task['id'], self.task['title'], self.task['description'])
#         await interaction.response.send_modal(modal)

# class UpdateTaskModal(Modal):
#     def __init__(self, task_id, title, description):
#         super().__init__(title="Update Task")
#         self.task_id = task_id

#         self.title_input = TextInput(label="Title", default=title, required=True)
#         self.description_input = TextInput(label="Description", default=description, style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value
#         }
#         response = requests.put(f"{API_URL_TASKS}{self.task_id}/update/", json=data)
#         if response.status_code == 200:
#             await interaction.response.send_message(f'Task "{data["title"]}" updated successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to update task. Status code: {response.status_code}", ephemeral=True)

# class DeleteTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Delete {task['title']}", style=ButtonStyle.danger)
#         self.task_id = task['id']
#         self.task_title = task['title']

#     async def callback(self, interaction: Interaction):
#         modal = ConfirmDeleteTaskModal(self.task_id, self.task_title)
#         await interaction.response.send_modal(modal)

# class ConfirmDeleteTaskModal(Modal):
#     def __init__(self, task_id, task_title):
#         super().__init__(title="Confirm Deletion")
#         self.task_id = task_id
#         self.task_title = task_title

#         self.confirmation = TextInput(
#             label=f"Type '{self.task_title}' to confirm",
#             placeholder=self.task_title,
#             required=True
#         )
#         self.add_item(self.confirmation)

#     async def on_submit(self, interaction: Interaction):
#         if self.confirmation.value != self.task_title:
#             await interaction.response.send_message("Deletion cancelled.", ephemeral=True)
#             return

#         response = requests.delete(f"{API_URL_TASKS}{self.task_id}/delete/")
#         if response.status_code == 204:
#             await interaction.response.send_message(f'Task "{self.task_title}" deleted successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to delete task. Status code: {response.status_code}", ephemeral=True)

# class TaskSelectPathButton(Button):
#     def __init__(self, path, callback_id):
#         super().__init__(label=path['name'], style=ButtonStyle.primary)
#         self.path_id = path['id']
#         self.path_name = path['name']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectPathButton callback triggered for path_id: {self.path_id}, callback_id: {self.callback_id}")
#         response = requests.get(f"{API_URL_TOPICS}list/")
#         if response.status_code == 200:
#             topics = response.json()
#             topics = [topic for topic in topics if topic['path'] == self.path_id]
#             view = View()
#             for topic in topics:
#                 view.add_item(TaskSelectTopicButton(topic, self.callback_id))
#             await interaction.response.send_message(f"Select a topic for {self.path_name}:", view=view, ephemeral=True)
#         elif response.status_code == 404:
#             await interaction.response.send_message("No topics available for this path.", ephemeral=True)
#             return
#         else:
#             print("Failed to fetch topics inside TaskSelectPathButton")
#             await interaction.response.send_message("Failed to fetch topics.", ephemeral=True)

# class TaskSelectTopicButton(Button):
#     def __init__(self, topic, callback_id):
#         super().__init__(label=topic['title'], style=ButtonStyle.primary)
#         self.topic_id = topic['id']
#         self.topic_title = topic['title']
#         self.callback_id = callback_id

#     async def callback(self, interaction: Interaction):
#         print(f"TaskSelectTopicButton callback triggered for topic_id: {self.topic_id}, callback_id: {self.callback_id}")
#         if self.callback_id == 'add_task':
#             modal = TaskModal(self.topic_id, self.topic_title)
#             await interaction.response.send_modal(modal)
#         elif self.callback_id in ['update_task', 'delete_task', 'list_tasks']:
#             tasks = await fetch_tasks(interaction, API_URL_TASKS, self.topic_id)
#             if tasks:
#                 if self.callback_id == 'list_tasks':
#                     task_list = "\n".join([f"▫️ {task['title']}" for task in tasks])
#                     await interaction.response.send_message(f"Tasks for {self.topic_title}:\n{task_list}", ephemeral=True)
#                 else:
#                     view = View()
#                     for task in tasks:
#                         if self.callback_id == 'update_task':
#                             view.add_item(UpdateTaskButton(task))
#                         elif self.callback_id == 'delete_task':
#                             view.add_item(DeleteTaskButton(task))
#                     await interaction.response.send_message(f"Select a task to {self.callback_id.split('_')[0]}:", view=view, ephemeral=True)
#             else:
#                 await interaction.response.send_message("No tasks available for this topic.", ephemeral=True)

# async def fetch_tasks(interaction, api_url_tasks, topic_id):
#     response = requests.get(f"{api_url_tasks}list/")
#     if response.status_code == 200:
#         try:
#             tasks = response.json()
#         except json.JSONDecodeError:
#             await interaction.response.send_message("Failed to parse tasks.", ephemeral=True)
#             return None
#         tasks = [task for task in tasks if task['topic'] == topic_id]
#         if not tasks:
#             await interaction.response.send_message("No tasks available.", ephemeral=True)
#             return None
#         return tasks
#     else:
#         await interaction.response.send_message("Failed to fetch tasks.", ephemeral=True)
#         return None

# class TaskModal(Modal):
#     def __init__(self, topic_id, topic_title):
#         super().__init__(title=f"Add Task to {topic_title}")
#         self.topic_id = topic_id
#         self.topic_title = topic_title  # Ensure topic_title is properly initialized

#         self.title_input = TextInput(label="Title", required=True)
#         self.description_input = TextInput(label="Description", style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         print(f"Submitting TaskModal for topic_id: {self.topic_id}")
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value,
#             "topic": self.topic_id
#         }
#         response = requests.post(f"{API_URL_TASKS}create/", json=data)
#         print(f"API URL: {API_URL_TASKS}create/")
#         print(f"Payload: {data}")
#         print(f"Response Status Code: {response.status_code}")
#         print(f"Response Content: {response.content}")
#         if response.status_code == 201:
#             await interaction.response.send_message(f'Task "{data["title"]}" added successfully to {self.topic_title}.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to add task. Status code: {response.status_code}", ephemeral=True)

# class UpdateTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Update {task['title']}", style=ButtonStyle.primary)
#         self.task = task

#     async def callback(self, interaction: Interaction):
#         modal = UpdateTaskModal(self.task['id'], self.task['title'], self.task['description'])
#         await interaction.response.send_modal(modal)

# class UpdateTaskModal(Modal):
#     def __init__(self, task_id, title, description):
#         super().__init__(title="Update Task")
#         self.task_id = task_id

#         self.title_input = TextInput(label="Title", default=title, required=True)
#         self.description_input = TextInput(label="Description", default=description, style=TextStyle.paragraph, required=False)

#         self.add_item(self.title_input)
#         self.add_item(self.description_input)

#     async def on_submit(self, interaction: Interaction):
#         data = {
#             "title": self.title_input.value,
#             "description": self.description_input.value
#         }
#         response = requests.put(f"{API_URL_TASKS}{self.task_id}/update/", json=data)
#         if response.status_code == 200:
#             await interaction.response.send_message(f'Task "{data["title"]}" updated successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to update task. Status code: {response.status_code}", ephemeral=True)

# class DeleteTaskButton(Button):
#     def __init__(self, task):
#         super().__init__(label=f"Delete {task['title']}", style=ButtonStyle.danger)
#         self.task_id = task['id']
#         self.task_title = task['title']

#     async def callback(self, interaction: Interaction):
#         modal = ConfirmDeleteTaskModal(self.task_id, self.task_title)
#         await interaction.response.send_modal(modal)

# class ConfirmDeleteTaskModal(Modal):
#     def __init__(self, task_id, task_title):
#         super().__init__(title="Confirm Deletion")
#         self.task_id = task_id
#         self.task_title = task_title

#         self.confirmation = TextInput(
#             label=f"Type '{self.task_title}' to confirm",
#             placeholder=self.task_title,
#             required=True
#         )
#         self.add_item(self.confirmation)

#     async def on_submit(self, interaction: Interaction):
#         if self.confirmation.value != self.task_title:
#             await interaction.response.send_message("Deletion cancelled.", ephemeral=True)
#             return

#         response = requests.delete(f"{API_URL_TASKS}{self.task_id}/delete/")
#         if response.status_code == 204:
#             await interaction.response.send_message(f'Task "{self.task_title}" deleted successfully.', ephemeral=True)
#         else:
#             await interaction.response.send_message(f"Failed to delete task. Status code: {response.status_code}", ephemeral=True)
