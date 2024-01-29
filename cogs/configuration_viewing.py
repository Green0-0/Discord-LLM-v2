import logging
import discord
from libs import character, config, format, model, params, validator
from discord.ext import commands
from discord import app_commands
import data 
import socket
import select
import time
import json
import http.client
import ssl
import sys

async def setup(bot : commands.Bot):
    await bot.add_cog(Configuration_Viewing(bot))

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

def get_neuroengine_list():
        # Get the list
        command = {'command': 'getmodels' }
        json_data = json.dumps(command)
        # Create an HTTP connection
        socket.setdefaulttimeout(180)
        connection = http.client.HTTPSConnection("api.neuroengine.ai", 443)

        # Send a POST request with the JSON message
        headers = {'Content-Type': 'application/json'}
        connection.request('POST', f'/Neuroengine-Large', json_data, headers)

        # Get the response from the server
        response = connection.getresponse()
        response = response.read().decode()

        connection.close()
        return json.loads(response)
        ###

class Configuration_Viewing(commands.Cog):
    bot : commands.Bot

    def __init__(self, bot : commands.Bot):
        self.bot = bot
        
    @app_commands.command(name = "list_configs", description = "List all the set up configurations.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def list_configs(self, interaction : discord.Interaction):
        text = []
        # Creates a numbered list
        for x in range(len(data.configs)):
            text.append(str(x) + "\. " + data.configs[x].name)
        final_text = "\n".join(text)
        embed = discord.Embed(title="Configs", description=final_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets you view a config
    class ViewConfig_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.configs)):
                options.append(discord.SelectOption(label=i, description=data.configs[i].name))

            super().__init__(placeholder='Select a config to view:', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            config_found = data.configs[foundat]
            s = "- Model: " + config_found.model.name
            s += "\n- Format: " + config_found.format.name
            s += "\n- Validators: " + str(len(config_found.validators))
            embed = discord.Embed(title=str(foundat) + "\. " + config_found.name, description=s, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Attaches the above select menu to a view
    class ViewConfigView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.ViewConfig_selectmenu(parent))

    @app_commands.command(name = "view_config", description = "View a configuration.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def view_config(self, interaction : discord.Interaction, id : str = "-1"):
        if id == "-1":
            view = self.ViewConfigView(self)
            embed = discord.Embed(description="Select a config to view:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.configs, interaction)
        if foundat == -1:
            return
        config_found = data.configs[foundat]
        s = "- Model: " + config_found.model.name
        s += "\n- Format: " + config_found.format.name
        s += "\n- Validators: " + str(len(config_found.validators))
        embed = discord.Embed(title=str(foundat) + "\. " + config_found.name, description=s, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    
    @app_commands.command(name = "neuroengine_list", description = "List all the models avaliable on Neuroengine.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def neuroengine_list(self, interaction : discord.Interaction):
        try:
            ls = get_neuroengine_list()
            text = []
            # Creates a numbered list
            for x in range(len(ls)):
                text.append("" + str(x) + "\. " + ls[x]['name'] + " (Queue: " + str(ls[x]['queuelen']) + ")")
        except Exception as e:
            logging.error(e)
            embed = discord.Embed(title="Exception", description=str(e), color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        final_text = "\n".join(text)
        embed = discord.Embed(title="Raw Model List", description=final_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    
    @app_commands.command(name = "list_models", description = "List all the set up models.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def list_models(self, interaction : discord.Interaction):
        text = []
        # Creates a numbered list
        for x in range(len(data.models)):
            text.append("" + str(x) + "\. " + data.models[x].name + " (" + str(data.models[x].context_length) + " ctx)")
        final_text = "\n".join(text)
        embed = discord.Embed(title="Models", description=final_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name = "list_paramss", description = "List all the set up sampling presets.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def list_params(self, interaction : discord.Interaction):
        text = []
        # Creates a numbered list
        for x in range(len(data.paramss)):
            text.append(str(x) + "\. " + data.paramss[x].name)
        final_text = "\n".join(text)
        embed = discord.Embed(title="Sampling Presets", description=final_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets you view a sampling preset
    class ViewParams_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.paramss)):
                options.append(discord.SelectOption(label=i, description=data.paramss[i].name))

            super().__init__(placeholder='Select a sampling preset to view:', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            params_found = data.paramss[foundat]
            s = "- Temperature: " + str(params_found.temperature)
            s += "\n- Min P: " + str(params_found.min_p)
            s += "\n- Top P: " + str(params_found.top_p)
            s += "\n- Top K: " + str(params_found.top_k)
            s += "\n- Repetition Penalty: " + str(params_found.repetition_penalty)
            s += "\n- Max New Tokens: " + str(params_found.max_new_tokens)
            embed = discord.Embed(title=str(foundat) + "\. " + params_found.name, description=s, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Attaches the above select menu to a view
    class ViewParamsView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.ViewParams_selectmenu(parent))

    @app_commands.command(name = "view_params", description = "View a sampling preset.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def view_params(self, interaction : discord.Interaction, id : str = "-1"):
        if id == "-1":
            view = self.ViewParamsView(self)
            embed = discord.Embed(description="Select a config to view:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.paramss, interaction)
        if foundat == -1:
            return
        params_found = data.paramss[foundat]
        s = "- Temperature: " + str(params_found.temperature)
        s += "\n- Min P: " + str(params_found.min_p)
        s += "\n- Top P: " + str(params_found.top_p)
        s += "\n- Top K: " + str(params_found.top_k)
        s += "\n- Repetition Penalty: " + str(params_found.repetition_penalty)
        s += "\n- Max New Tokens: " + str(params_found.max_new_tokens)
        embed = discord.Embed(title=str(foundat) + "\. " + params_found.name, description=s, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name = "list_formats", description = "List all the set up prompt formats.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def list_formats(self, interaction : discord.Interaction):
        text = []
        # Creates a numbered list
        for x in range(len(data.formats)):
            text.append(str(x) + "\. " + data.formats[x].name)
        final_text = "\n".join(text)
        embed = discord.Embed(title="Prompt Formats", description=final_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets you view a prompt format
    class ViewFormat_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.formats)):
                options.append(discord.SelectOption(label=i, description=data.formats[i].name))

            super().__init__(placeholder='Select a prompt format to view:', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            format_found = data.formats[foundat]
            text = format_found.template
            if text.startswith(" "):
                text = "\s" + text[1:]
            if text.endswith(" "):
                text = text[:-1] + "\s"
            if text.startswith("\n"):
                text = "\\n" + text[1:]
            if text.endswith("\n"):
                text = text[:-1] + "\\n"
            s = "Template:\n```" + text + "```"

            text = format_found.other_field_history
            if text.startswith(" "):
                text = "\s" + text[1:]
            if text.endswith(" "):
                text = text[:-1] + "\s"
            if text.startswith("\n"):
                text = "\\n" + text[1:]
            if text.endswith("\n"):
                text = text[:-1] + "\\n"
            s += "Other Field History:\n```" + text + "```\n"

            text = format_found.ai_field_history
            if text.startswith(" "):
                text = "\s" + text[1:]
            if text.endswith(" "):
                text = text[:-1] + "\s"
            if text.startswith("\n"):
                text = "\\n" + text[1:]
            if text.endswith("\n"):
                text = text[:-1] + "\\n"
            s += "AI Field History:\n```" + text + "```\n"

            text = format_found.history_joiner
            text = text.replace(" ", "\\s").replace("\n", "\\n")
            s += "History Joiner:\n```" + text + "```\n"

            text = '\n'.join(format_found.stop_criteria).replace(" ", "\\s")
            s += "Stop Criteria:\n```" + text + "```"
            
            embed = discord.Embed(title=str(foundat) + "\. " + format_found.name, description=s, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Attaches the above select menu to a view
    class ViewFormatView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.ViewFormat_selectmenu(parent))

    @app_commands.command(name = "view_format", description = "View a prompt format.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def view_format(self, interaction : discord.Interaction, id : str = "-1"):
        if id == "-1":
            view = self.ViewFormatView(self)
            embed = discord.Embed(description="Select a prompt format to view:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.formats, interaction)
        if foundat == -1:
            return
        format_found = data.formats[foundat]
        
        text = format_found.template
        if text.startswith(" "):
            text = "\s" + text[1:]
        if text.endswith(" "):
            text = text[:-1] + "\s"
        if text.startswith("\n"):
            text = "\\n" + text[1:]
        if text.endswith("\n"):
            text = text[:-1] + "\\n"
        s = "Template:\n```" + text + "```"

        text = format_found.other_field_history
        if text.startswith(" "):
            text = "\s" + text[1:]
        if text.endswith(" "):
            text = text[:-1] + "\s"
        if text.startswith("\n"):
            text = "\\n" + text[1:]
        if text.endswith("\n"):
            text = text[:-1] + "\\n"
        s += "Other Field History:\n```" + text + "```\n"

        text = format_found.ai_field_history
        if text.startswith(" "):
            text = "\s" + text[1:]
        if text.endswith(" "):
            text = text[:-1] + "\s"
        if text.startswith("\n"):
            text = "\\n" + text[1:]
        if text.endswith("\n"):
            text = text[:-1] + "\\n"
        s += "AI Field History:\n```" + text + "```\n"

        text = format_found.history_joiner
        text = text.replace(" ", "\\s").replace("\n", "\\n")
        s += "History Joiner:\n```" + text + "```\n"

        text = '\n'.join(format_found.stop_criteria).replace(" ", "\\s")
        s += "Stop Criteria:\n```" + text + "```"
        
        embed = discord.Embed(title=str(foundat) + "\. " + format_found.name, description=s, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name = "list_valids", description = "List all the set up validators.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def list_valids(self, interaction : discord.Interaction):
        text = []
        # Creates a numbered list
        for x in range(len(data.validators)):
            c = data.validators[x]
            s = "" + str(x) + "\. ``" + str(c) + "``"
            text.append(s)
        final_text = "\n".join(text)
        embed = discord.Embed(title="Validators", description=final_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)