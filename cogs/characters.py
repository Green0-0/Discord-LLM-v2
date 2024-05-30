from libs import character, chat, config
import sys
import logging
import traceback
import data
import requests
import json

import discord
from discord.ext import commands
from discord import ui, app_commands

async def setup(bot : commands.Bot):
    await bot.add_cog(Characters(bot))

def isInt(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def has_repeat(new_name : str, items : list, item_exclude = None):
    for x in range(len(items)):
        i = items[x]
        if i == item_exclude:
            continue
        if i.name.lower() == new_name.lower():
            return True
    return False


async def search_for_data(id : str, items : list, interaction : discord.Interaction, custom_error : str = "") -> int:
    try:
        id = int(id)
        if id < 0:
            embed = discord.Embed(title=f"Invalid {custom_error}ID", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return -1
        if id >= len(items):
            embed = discord.Embed(title=f"Invalid {custom_error}ID", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return -1
        return id
    except ValueError:
        for x in range(len(items)):
            id = id.lower()
            c = items[x]
            if c.name.lower() == id:
                return x
        embed = discord.Embed(title=f"{custom_error}Name Not Found OR Invalid {custom_error}ID", color=discord.Color.yellow())
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
        return -1

class Characters(commands.Cog):
    working : bool
    bot : commands.Bot
    
    def __init__(self, bot : commands.Bot):
        self.working = False
        self.bot = bot

    async def is_admin(self, interaction : discord.Interaction) -> bool:
        return interaction.user in data.admins or await self.bot.is_owner(interaction.user)

    @app_commands.command(name = "list_characters", description = "List all the characters.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def list_characters(self, interaction : discord.Interaction):
        text = []
        # Creates a numbered list
        for x in range(len(data.characters)):
            text.append("" + str(x) + ". " + data.characters[x].name + " (" + str(data.characters[x].conf.name) + ")")
        final_text = "\n".join(text)
        embed = discord.Embed(title="Characters", description=final_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    
    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets you view a sampling preset
    class ViewCharacter_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.characters)):
                options.append(discord.SelectOption(label=i, description=data.characters[i].name))

            super().__init__(placeholder='Select a character to view:', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            character_found = data.characters[foundat]
            character_channel_list = "Can only be viewed in a server."
            if len(character_found.channels) == 0:
                character_channel_list = "None."
            if not isinstance(interaction.channel, discord.DMChannel) and len(character_found.channels) != 0:
                character_channel_list = ""
                if 'all' in character_found.channels:
                    character_channel_list = "(Note: Given channels are excluded from all) "
                channel_list = interaction.guild.channels
                foundChannels = []
                for x in range(len(character_found.channels)):
                    found = False
                    for y in range(len(channel_list)):
                        if character_found.channels[x] == channel_list[y].id:
                            foundChannels.append(channel_list[y].name)
                            found = True
                            break
                    if not found:
                        foundChannels.append(character_found.channels[x])
                character_channel_list += ", ".join(foundChannels)
            embed = discord.Embed(title=str(foundat) + ". " + character_found.name + " (" + str(character_found.conf.name) + ")", description="```" + character_found.system + "```" + "\nChannels active: " + character_channel_list, color=discord.Color.blue())
            embed.set_thumbnail(url=character_found.icon)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Attaches the above select menu to a view
    class ViewCharacterView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.ViewCharacter_selectmenu(parent))

    @app_commands.command(name = "view_character", description = "View a character.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def view_character(self, interaction : discord.Interaction, id : str = "-1"):
        if id == "-1":
            view = self.ViewCharacterView(self)
            embed = discord.Embed(description="Select a character to view:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.characters, interaction)
        if foundat == -1:
            return
        character_found = data.characters[foundat]
        character_channel_list = "Can only be viewed in a server."
        if not isinstance(interaction.channel, discord.DMChannel) and len(character_found.channels) == 0:
            character_channel_list = "None."
        if not isinstance(interaction.channel, discord.DMChannel) and len(character_found.channels) != 0:
            character_channel_list = ""
            if 'all' in character_found.channels:
                character_channel_list = "(Note: Given channels are excluded from all)"
            channel_list = interaction.guild.channels
            foundChannels = []
            for x in range(len(character_found.channels)):
                found = False
                for y in range(len(channel_list)):
                    if character_found.channels[x] == channel_list[y].id:
                        foundChannels.append(channel_list[y].name)
                        found = True
                        break
                if not found:
                    foundChannels.append(character_found.channels[x])
            character_channel_list += ", ".join(foundChannels)
        embed = discord.Embed(title=str(foundat) + ". " + character_found.name + " (" + str(character_found.conf.name) + ")", description="```" + character_found.system + "```" + "\nChannels active: " + character_channel_list, color=discord.Color.blue())
        embed.set_thumbnail(url=character_found.icon)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A modal is basically a form the user fills out and then submits
    # A modal that edits a character
    class EditCharacterModal(ui.Modal, title = "Character Editing"):
        def __init__(self, c : character.Character = None):
            if c == None:
                self.add = True
                self.title = "New Character"
                c = character.Character(conf = data.configs[0], name = "New Character", icon = "PNG, JPEG, or JPG", system = "New Character Description")
            else:
                self.add = False
                self.title = "Editing " + c.name
            super().__init__()

            self.c = c

            self.add_item(discord.ui.TextInput(
                label = "Config:",
                default = c.conf.name,
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Name:", 
                default = c.name,
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Icon:", 
                default = c.icon, 
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "System/Description:",
                default = c.system,
                style = discord.TextStyle.paragraph,
                required = True
            ))
        
        # Called when the user submits the modal
        async def on_submit(self, interaction : discord.Interaction):
            # Check for proper naming
            if isInt(self.children[1].value):
                embed = discord.Embed(description="You are not allowed to use a numerical ID as a name.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            if has_repeat(self.children[1].value, data.characters, self.c):
                embed = discord.Embed(description="Please do not reuse names.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            # Checks if the icon URL is valid
            try:
                r = requests.head(self.children[2].value)
                image_formats = ("image/png", "image/jpeg", "image/jpg")
                if r.headers["content-type"] not in image_formats:
                    embed = discord.Embed(description="Invalid icon URL", color=discord.Color.yellow())
                    await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                    embed = discord.Embed(title="Failed to create character " + self.children[1].value, description="Character description: " + self.children[3].value, color=discord.Color.yellow())
                    await interaction.channel.send(embed=embed)
                    return
            except:
                embed = discord.Embed(description="Invalid icon URL", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed)
                embed = discord.Embed(title="Failed to create character " + self.children[1].value, description="Character description: " + self.children[3].value, color=discord.Color.yellow())
                await interaction.channel.send(embed=embed)
                return
            # Check if the config exists
            foundat = await search_for_data(self.children[0].value, data.configs, interaction, custom_error = "Config ")
            if foundat == -1:
                return
            config_found = data.configs[foundat]

            # Update the character
            self.c.conf = config_found
            self.c.name = self.children[1].value
            self.c.icon = self.children[2].value
            self.c.system = self.children[3].value
            if self.add:
                data.characters.append(self.c)
                embed = discord.Embed(description="Successfully created " + self.c.name + "!", color=discord.Color.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(description="Successfully edited " + self.c.name + "!", color=discord.Color.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin edit a character
    class EditCharacter_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.characters)):
                options.append(discord.SelectOption(label=i, description=data.characters[i].name))

            super().__init__(placeholder='Select a character to edit', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            character = data.characters[int(self.values[0])]
            await interaction.response.send_modal(self.parent.EditCharacterModal(character))
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class EditCharacterView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.EditCharacter_selectmenu(parent))

    @app_commands.command(name = "edit_character", description = "Edit a character.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def edit_character(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.EditCharacterView(self)
            embed = discord.Embed(description="Select a character to edit:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            foundat = await search_for_data(id, data.characters, interaction)
            if foundat == -1:
                return
            character = data.characters[foundat]
            await interaction.response.send_modal(self.EditCharacterModal(character))

    @app_commands.command(name = "create_character", description = "Create a character.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def create_character(self, interaction : discord.Interaction):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        await interaction.response.send_modal(self.EditCharacterModal(None))

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin delete a character
    class DeleteCharacter_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.characters)):
                options.append(discord.SelectOption(label=i, description=data.characters[i].name))

            super().__init__(placeholder='Select a character to delete', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            removed = data.characters.pop(foundat)
            embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class DeleteCharacterView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.DeleteCharacter_selectmenu(parent))

    @app_commands.command(name = "delete_character", description = "Delete a character.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def delete_character(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if len(data.characters) < 2:
            embed = discord.Embed(title="Please do not delete all characters.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.DeleteCharacterView(self)
            embed = discord.Embed(description="Select a character to delete:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.characters, interaction)
        if foundat == -1:
            return
        removed = data.characters.pop(foundat)
        embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin unlock a character for a particular channel
    class UnlockCharacter_selectmenu(discord.ui.Select):
        def __init__(self, parent, all_channels):
            self.parent = parent
            self.all_channels = all_channels
            options = []
            for i in range (len(data.characters)):
                options.append(discord.SelectOption(label=i, description=data.characters[i].name))

            super().__init__(placeholder='Select a character to unlock in this channel', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            character = data.characters[foundat]
            if self.all_channels:
                if 'all' in character.channels:
                    character.channels.remove('all')
                    embed = discord.Embed(description="" + character.name + " can no longer talk in every channel!", color=discord.Color.blue())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    character.channels.append('all')
                    embed = discord.Embed(description="" + character.name + " can now talk in every channel!", color=discord.Color.blue())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                if interaction.channel.id not in character.channels:
                    character.channels.append(interaction.channel.id)
                    embed = discord.Embed(description="" + character.name + " can now talk in this channel!", color=discord.Color.blue())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    character.channels.remove(interaction.channel.id)
                    embed = discord.Embed(description="" + character.name + " can no longer talk in this channel!", color=discord.Color.blue())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class UnlockCharacterView(discord.ui.View):
        def __init__(self, parent, all_channels):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.UnlockCharacter_selectmenu(parent, all_channels))

    @app_commands.command(name = "toggle_character", description = "Toggles speaking for a character in this channel.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def toggle_character(self, interaction : discord.Interaction, id : str = "-1", all_channels : bool = False):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.UnlockCharacterView(self, all_channels)
            embed = discord.Embed(description="Select a character to enable/disable in this channel:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.characters, interaction)
        if foundat == -1:
            return
        character = data.characters[foundat]
        if all_channels:
            if 'all' in character.channels:
                character.channels.remove('all')
                embed = discord.Embed(description="" + character.name + " can no longer talk in every channel!", color=discord.Color.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                character.channels.append('all')
                embed = discord.Embed(description="" + character.name + " can now talk in every channel!", color=discord.Color.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            if interaction.channel.id not in character.channels:
                character.channels.append(interaction.channel.id)
                embed = discord.Embed(description="" + character.name + " can now talk in this channel!", color=discord.Color.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                character.channels.remove(interaction.channel.id)
                embed = discord.Embed(description="" + character.name + " can no longer talk in this channel!", color=discord.Color.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name = "export_all", description = "Export all characters into a json file.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def export_all(self, interaction : discord.Interaction):
        j = {"characters" : []}
        for c in data.characters:
            thing = {}
            thing["name"] = c.name
            thing["system"] = c.system
            thing["icon"] = c.icon
            thing["channels"] = c.channels
            thing["conf"] = c.conf.name
            j["characters"].append(thing)
        with open("Characters.json", "w") as file:
            json.dump(j, file)
        embed = discord.Embed(description="Successfully exported all characters!", color=discord.Color.blue())
        with open("Characters.json", "rb") as file:
            await interaction.response.send_message(embed=embed, file=discord.File(file, "Characters.json"), ephemeral=True) 
    
    @app_commands.command(name = "import_all", description = "Import all characters from a json file, replace existing ones if found.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def import_all(self, interaction : discord.Interaction, file: discord.Attachment):      
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return          
        try:
            raw = await file.read()
            j = json.loads(raw)
        except:
            embed = discord.Embed(description="Invalid json file!", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        warningmsgs = []
        for char in j["characters"]:
            try:
                name = char["name"]
                system = char["system"]
                icon = char["icon"]
                channels = char["channels"]
                conf = char["conf"]
            except:
                warningmsgs.append(f"[Character {name}]: Invalid json! Skipped.")
                continue
            
            # Check if config exists
            found = False
            for c in data.configs:
                if c.name == conf:
                    found = True
                    conf = c
                    break
            if not found:
                warningmsgs.append(f"[Character {name}]: Config {conf} does not exist! Skipped.")
                continue
            
            # Check if icon is valid
            r = requests.head(icon)
            image_formats = ("image/png", "image/jpeg", "image/jpg")
            if r.headers["content-type"] not in image_formats:
                warningmsgs.append(f"[Character {name}]: Invalid icon! Skipped.")
                continue
            
            # Check if character already exists
            foundat = -1
            for i in range(len(data.characters)):
                if data.characters[i].name == name:
                    foundat = i
                    break
            if foundat != -1:
                warningmsgs.append(f"[Character {name}]: Replaced existing with data in json.")
                data.characters[foundat] = character.Character(c, name, icon, system)
                continue
            else:
                warningmsgs.append(f"[Character {name}]: Added new with data in json.")
                data.characters.append(character.Character(c, name, icon, system))
        embed = discord.Embed(title=f"Finished importing {len(j['characters'])} characters!", description="\n".join(warningmsgs), color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name = "set_reminder", description = "Set the reminder for the characters (seperated by '::').")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def set_reminders(self, interaction : discord.Interaction, ids : str, reminder : str):
        ids = ids.split("::")
        reminder = reminder.replace("\\\\n", "\n").replace("\\\\s", " ").replace("\\\\z", "")
        results = []
        for id in ids:
            foundat = await search_for_data(id, data.characters, interaction)
            if foundat == -1:
                results.append("Character " + id + " not found!")
                continue
            data.characters[foundat].reminders[interaction.channel_id] = reminder
            results.append("Set reminder for " + id + " to '" + reminder + "' in channel " + str(interaction.channel_id))
        embed = discord.Embed(description="Successfully set reminders!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin unlock a character for a particular channel
    class GetReminder_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.characters)):
                options.append(discord.SelectOption(label=i, description=data.characters[i].name))

            super().__init__(placeholder='Select a character to view the reminders of for this channel:', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            character = data.characters[foundat]
            if interaction.channel_id not in character.reminders or character.reminders[interaction.channel_id] == "":
                r = "No reminders set for this character in this channel!"
            else:
                r = character.reminders[interaction.channel_id]
                if r.startswith(" "):
                    r = "\\\\s" + r[1:]
                if r.endswith(" "):
                    r = "\\\\s" + r[:-1]
                if r.startswith("\n"):
                    r = "\\\\n" + r[1:]
                if r.endswith("\n"):
                    r = "\\\\n" + r[:-1]
                r = f"Reminder for {character.name}: ```{r}```"
            embed = discord.Embed(description=r, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class GetReminderView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.GetReminder_selectmenu(parent))

    @app_commands.command(name = "get_reminder", description = "Gets a reminder from the character.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def get_reminder(self, interaction : discord.Interaction, id : str = "-1"):
        if id == "-1":
            view = self.GetReminderView(self)
            embed = discord.Embed(description="Select a character to view the reminders of for this channel:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.characters, interaction)
        if foundat == -1:
            return
        character = data.characters[foundat]
        if interaction.channel_id not in character.reminders or character.reminders[interaction.channel_id] == "":
            r = "No reminders set for this character in this channel!"
        else:
            r = character.reminders[interaction.channel_id]
            if r.startswith(" "):
                r = "\\\\s" + r[1:]
            if r.endswith(" "):
                r = "\\\\s" + r[:-1]
            if r.startswith("\n"):
                r = "\\\\n" + r[1:]
            if r.endswith("\n"):
                r = "\\\\n" + r[:-1]
            r = f"Reminder for {character.name}: ```{r}```"
        embed = discord.Embed(description=r, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
