import logging
import discord
from libs import character, config, format, model, params, validator
from discord.ext import commands
from discord import ui, app_commands
import data 

async def setup(bot : commands.Bot):
    await bot.add_cog(Configuration_Editing(bot))

def isFloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

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

def find_used_config(item) -> int:
    for x in range(len(data.configs)):
        if data.configs[x].model == item or data.configs[x].format == item or data.configs[x].params == item or item in data.configs[x].validators:
            return x
    return -1

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

class Configuration_Editing(commands.Cog):
    bot : commands.Bot

    def __init__(self, bot : commands.Bot):
        self.bot = bot

    async def is_admin(self, interaction : discord.Interaction) -> bool:
        return interaction.user in data.admins or await self.bot.is_owner(interaction.user)
    
    # A modal is basically a form the user fills out and then submits
    # A modal that edits a config
    class EditConfigModal(ui.Modal, title = "Config Editing"):
        def __init__(self, c : config.Config):
            super().__init__()

            self.c = c

            self.add_item(discord.ui.TextInput(
                label = "Name:", 
                default = c.name,
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Model:", 
                default = c.model.name, 
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Format:",
                default = c.format.name,
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Parameters Preset:",
                default = c.params.name,
                required = True
            ))

            validators_text = []
            for v in c.validators:
                validators_text.append(v.name)

            self.add_item(discord.ui.TextInput(
                label = "Validators:",
                default = "/".join(validators_text),
                required = False
            ))
            
        
        # Called when the user submits the modal
        async def on_submit(self, interaction : discord.Interaction):
            # Check for proper naming
            if isInt(self.children[0].value):
                embed = discord.Embed(description="You are not allowed to use a numerical ID as a name.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            if has_repeat(self.children[0].value, data.configs, self.c):
                embed = discord.Embed(description="Please do not reuse names.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            
            # Find linked model
            foundat = await search_for_data(self.children[1].value, data.models, interaction, custom_error = "Model ")
            if foundat == -1:
                return
            model_found = data.models[foundat]

            # Find linked format
            foundat = await search_for_data(self.children[2].value, data.formats, interaction, custom_error = "Format ")
            if foundat == -1:
                return
            format_found = data.formats[foundat]
            
            # Find linked params
            foundat = await search_for_data(self.children[3].value, data.paramss, interaction, custom_error = "Params ")
            if foundat == -1:
                return
            params_found = data.paramss[foundat]

            # Find linked validators
            if len(self.children[4].value) == 0:
                all_validators = []
            else:
                all_validators = self.children[4].value.split("/")

            all_validators_found = []
            for v in all_validators:
                foundat = await search_for_data(v, data.validators, interaction, custom_error = "Validator ")
                if foundat == -1:
                    return
                all_validators_found.append(data.validators[foundat])

            # Finally, edit the config
            self.c.name = self.children[0].value
            self.c.model = model_found
            self.c.format = format_found
            self.c.params = params_found
            self.c.validators = all_validators_found
            embed = discord.Embed(description="Successfully edited " + self.c.name + "!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin edit a config
    class EditConfig_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.configs)):
                options.append(discord.SelectOption(label=i, description=data.configs[i].name))

            super().__init__(placeholder='Select a config to edit', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            config = data.configs[int(self.values[0])]
            await interaction.response.send_modal(self.parent.EditConfigModal(config))
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class EditConfigView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.EditConfig_selectmenu(parent))

    @app_commands.command(name = "edit_config", description = "Edit a configuration.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def edit_config(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.EditConfigView(self)
            embed = discord.Embed(description="Select a config to edit:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            foundat = await search_for_data(id, data.configs, interaction)
            if foundat == -1:
                return
            config_found = data.configs[foundat]
            await interaction.response.send_modal(self.EditConfigModal(config_found))

    @app_commands.command(name = "create_config", description = "Create a configuration.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def create_config(self, interaction : discord.Interaction):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return

        config_new = config.Config("New-Config", data.models[0], data.formats[0], data.paramss[0], [])
        data.configs.append(config_new)
        embed = discord.Embed(description="Successfully created a new configuration! Edit it with '/edit_config.'", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin delete a config
    class DeleteConfig_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.configs)):
                options.append(discord.SelectOption(label=i, description=data.configs[i].name))

            super().__init__(placeholder='Select a config to delete', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            config_found = data.configs[foundat]
            for x in range(len(data.characters)):
                if data.characters[x].conf == config_found:
                    embed = discord.Embed(title="Config is used in character '" + data.characters[x].name + "'.", color=discord.Color.yellow())
                    await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                    return
            removed = data.configs.pop(ifoundat)
            embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class DeleteConfigView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.DeleteConfig_selectmenu(parent))

    @app_commands.command(name = "delete_config", description = "Delete a configuration.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def delete_config(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if len(data.configs) < 2:
            embed = discord.Embed(title="Please do not delete all configurations.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.DeleteConfigView(self)
            embed = discord.Embed(description="Select a config to delete:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.configs, interaction)
        if foundat == -1:
            return
        config_found = data.configs[foundat]
        for x in range(len(data.characters)):
            if data.characters[x].conf == config_found:
                embed = discord.Embed(title="Config is used in character '" + data.characters[x].name + "'.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
        removed = data.configs.pop(foundat)
        embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name = "create_model", description = "Create a model.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def create_model(self, interaction : discord.Interaction, api_name : str, context_length : int):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return

        if isInt(api_name):
            embed = discord.Embed(description="You are not allowed to use a numerical ID as a name.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed)
            return
        if len(api_name) < 2:
            embed = discord.Embed(title="Please enter a valid name.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if context_length < 2:
            embed = discord.Embed(title="Please enter a valid context length.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if has_repeat(api_name, data.models):
            embed = discord.Embed(description="Please do not reuse names.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return

        model_new = model.Model(api_name, context_length)
        data.models.append(model_new)
        embed = discord.Embed(description="Successfully added '" + model_new.name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin delete a model
    class DeleteModel_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.models)):
                options.append(discord.SelectOption(label=i, description=data.models[i].name))

            super().__init__(placeholder='Select a model to delete', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            model_found = data.models[foundat]
        
            # Check if model is used in any configs
            used_location = find_used_config(model_found)
            if used_location != -1:
                embed = discord.Embed(title="Model is used in config '" + data.configs[used_location].name + "'.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            removed = data.models.pop(foundat)
            embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class DeleteModelView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.DeleteModel_selectmenu(parent))

    @app_commands.command(name = "delete_model", description = "Delete a model.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def delete_model(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if len(data.models) < 2:
            embed = discord.Embed(title="Please do not delete all models.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.DeleteModelView(self)
            embed = discord.Embed(description="Select a model to delete:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.models, interaction)
        if foundat == -1:
            return
        model_found = data.models[foundat]
        # Check if model is used in any configs
        used_location = find_used_config(model_found)
        if used_location != -1:
            embed = discord.Embed(title="Model is used in config '" + data.configs[used_location].name + "'.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        removed = data.models.pop(foundat)
        embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name = "create_validator", description = "Create a validator.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def create_validator(self, interaction : discord.Interaction, name : str):
        if isInt(name):
            embed = discord.Embed(description="You are not allowed to use a numerical ID as a name.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed)
            return
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if has_repeat(name, data.validators):
            embed = discord.Embed(description="Please do not reuse names.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return

        validators = validator.Validator(name)
        data.validators.append(validators)
        embed = discord.Embed(description="Successfully added '" + validators.name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin delete a validator
    class DeleteValidator_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.validators)):
                options.append(discord.SelectOption(label=i, description=data.validators[i].name))

            super().__init__(placeholder='Select a validator to delete', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            validator_found = data.validators[foundat]
            # Check if model is used in any configs
            used_location = find_used_config(validator_found)
            if used_location != -1:
                embed = discord.Embed(title="Validator is used in config '" + data.configs[used_location].name + "'.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            removed = data.validators.pop(foundat)
            embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class DeleteValidatorView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.DeleteValidator_selectmenu(parent))

    @app_commands.command(name = "delete_validator", description = "Delete a validator.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def delete_validator(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if len(data.validators) < 2:
            embed = discord.Embed(title="Please do not delete all validators.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.DeleteValidatorView(self)
            embed = discord.Embed(title="Select a validator to delete:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.validators, interaction)
        if foundat == -1:
            return
        validator_found = data.validators[foundat]
        # Check if model is used in any configs
        used_location = find_used_config(validator_found)
        if used_location != -1:
            embed = discord.Embed(title="Validator is used in config '" + data.configs[used_location].name + "'.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        removed = data.validators.pop(foundat)
        embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A modal is basically a form the user fills out and then submits
    # A modal that edits a sampling preset
    class EditParamsModal(ui.Modal, title = "Params Editing"):
        def __init__(self, p : params.Params):
            super().__init__()

            self.p = p

            self.add_item(discord.ui.TextInput(
                label = "Name:", 
                default = p.name,
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Temperature:", 
                default = str(p.temperature), 
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Min-P:",
                default = str(p.min_p),
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Repetition Penality:",
                default = str(p.repetition_penalty),
                required = True
            ))

            self.add_item(discord.ui.TextInput(
                label = "Max New Tokens:",
                default = str(p.max_new_tokens),
                required = True
            ))
        
        # Called when the user submits the modal
        async def on_submit(self, interaction : discord.Interaction):
            # Check for proper naming
            if isInt(self.children[0].value):
                embed = discord.Embed(description="You are not allowed to use a numerical ID as a name.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            if has_repeat(self.children[0].value, data.paramss, self.p):
                embed = discord.Embed(description="Please do not reuse names.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            if not isFloat(self.children[1].value) or not isFloat(self.children[2].value) or not isFloat(self.children[3].value) or not isInt(self.children[4].value):
                embed = discord.Embed(description="Please enter valid values.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return

            # Finally, edit the params
            self.p.name = self.children[0].value
            self.p.temperature = float(self.children[1].value)
            self.p.min_p = float(self.children[2].value)
            self.p.repetition_penalty = float(self.children[3].value)
            self.p.max_new_tokens = int(self.children[4].value)
            embed = discord.Embed(description="Successfully edited " + self.p.name + "!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin edit a sampling preset
    class EditParams_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.paramss)):
                options.append(discord.SelectOption(label=i, description=data.paramss[i].name))

            super().__init__(placeholder='Select a sampling preset to edit', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            params = data.paramss[int(self.values[0])]
            await interaction.response.send_modal(self.parent.EditParamsModal(params))
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class EditParamsView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.EditParams_selectmenu(parent))

    @app_commands.command(name = "edit_params", description = "Edit a sampling preset.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def edit_params(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.EditParamsView(self)
            embed = discord.Embed(description="Select a sampling preset to edit:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            foundat = await search_for_data(id, data.paramss, interaction)
            if foundat == -1:
                return
            params_found = data.paramss[foundat]
            await interaction.response.send_modal(self.EditParamsModal(params_found))

    @app_commands.command(name = "create_params", description = "Create a sampling preset.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def create_params(self, interaction : discord.Interaction):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return

        params_new = params.Params("New-Params")
        data.paramss.append(params_new)
        embed = discord.Embed(description="Successfully created a new sampling configuration! Edit it with '/edit_params.'", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin delete a sampling preset
    class DeleteParams_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.paramss)):
                options.append(discord.SelectOption(label=i, description=data.paramss[i].name))

            super().__init__(placeholder='Select a sampling preset to delete', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            params_found = data.paramss[foundat]
        
            # Check if model is used in any configs
            used_location = find_used_config(params_found)
            if used_location != -1:
                embed = discord.Embed(title="Sampling preset is used in config '" + data.configs[used_location].name + "'.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            removed = data.paramss.pop(foundat)
            embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class DeleteParamsView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.DeleteParams_selectmenu(parent))

    @app_commands.command(name = "delete_params", description = "Delete a sampling preset.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def delete_params(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if len(data.paramss) < 2:
            embed = discord.Embed(title="Please do not delete all sampling presets.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.DeleteParamsView(self)
            embed = discord.Embed(description="Select a sampling preset to delete:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.paramss, interaction)
        if foundat == -1:
            return
        params_found = data.paramss[foundat]
        # Check if model is used in any configs
        used_location = find_used_config(params_found)
        if used_location != -1:
            embed = discord.Embed(title="Sampling preset is used in config '" + data.configs[used_location].name + "'.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        removed = data.paramss.pop(foundat)
        embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A modal is basically a form the user fills out and then submits
    # A modal that edits a prompt format
    class EditFormatModal(ui.Modal, title = "Prompt Format Editing"):
        def __init__(self, f : format.Format):
            if len(f.name) > 20:
                self.title = "Editing Prompt Format '" + f.name[0:17] + "...'"
            else:
                self.title = "Editing Prompt Format '" + f.name + "'"
                
            super().__init__()

            self.f = f

            text = f.template
            if text.startswith(" "):
                text = "\\s" + text[1:]
            if text.endswith(" "):
                text = text[:-1] + "\\s"
            if text.startswith("\n"):
                text = "\\n" + text[1:]
            if text.endswith("\n"):
                text = text[:-1] + "\\n"

            self.add_item(discord.ui.TextInput(
                label = "Template:", 
                default = text, 
                style = discord.TextStyle.paragraph,
                required = True
            ))

            text = f.other_field_history
            if text.startswith(" "):
                text = "\\s" + text[1:]
            if text.endswith(" "):
                text = text[:-1] + "\\s"
            if text.startswith("\n"):
                text = "\\n" + text[1:]
            if text.endswith("\n"):
                text = text[:-1] + "\\n"

            self.add_item(discord.ui.TextInput(
                label = "Other Field History:",
                default = text,
                style = discord.TextStyle.paragraph,
                required = True
            ))

            text = f.ai_field_history
            if text.startswith(" "):
                text = "\s" + text[1:]
            if text.endswith(" "):
                text = text[:-1] + "\s"
            if text.startswith("\n"):
                text = "\\n" + text[1:]
            if text.endswith("\n"):
                text = text[:-1] + "\\n"

            self.add_item(discord.ui.TextInput(
                label = "AI Field History:",
                default = text,
                style = discord.TextStyle.paragraph,
                required = True
            ))

            text = f.history_joiner
            text = text.replace(" ", "\\s").replace("\n", "\\n")

            self.add_item(discord.ui.TextInput(
                label = "History Joiner:",
                default = text,
                style = discord.TextStyle.paragraph,
                required = True
            ))

            text = '\n'.join(f.stop_criteria).replace(" ", "\\s")

            self.add_item(discord.ui.TextInput(
                label = "Stop Criteria:",
                default = text,
                style = discord.TextStyle.paragraph,
                required = True
            ))

        # Called when the user submits the modal
        async def on_submit(self, interaction : discord.Interaction):
            # Finally, edit the params
            self.f.template = self.children[0].value.replace("\\s", " ").replace("\s", " ").replace("\\n", "\n")
            self.f.other_field_history = self.children[1].value.replace("\\s", " ").replace("\s", " ").replace("\\n", "\n")
            self.f.ai_field_history = self.children[2].value.replace("\\s", " ").replace("\s", " ").replace("\\n", "\n")
            self.f.history_joiner = self.children[3].value.replace("\\s", " ").replace("\s", " ").replace("\\n", "\n")
            self.f.stop_criteria = self.children[4].value.replace("\\s", " ").replace("\s", " ").split("\n")
            embed = discord.Embed(title="Successfully edited " + self.f.name + "!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin edit a prompt format
    class EditFormat_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.formats)):
                options.append(discord.SelectOption(label=i, description=data.formats[i].name))

            super().__init__(placeholder='Select a prompt format to edit', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            format = data.formats[int(self.values[0])]
            await interaction.response.send_modal(self.parent.EditFormatModal(format))
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class EditFormatView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.EditFormat_selectmenu(parent))

    @app_commands.command(name = "edit_format", description = "Edit a prompt format.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def edit_format(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.EditFormatView(self)
            embed = discord.Embed(description="Select a prompt format to edit:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            foundat = await search_for_data(id, data.formats, interaction)
            if foundat == -1:
                return
            format_found = data.formats[foundat]
            await interaction.response.send_modal(self.EditFormatModal(format_found))

    @app_commands.command(name = "create_format", description = "Create a prompt format.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def create_params(self, interaction : discord.Interaction):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        j = {}
        j["template"] = data.formats[0].template
        j["other_field_history"] = data.formats[0].other_field_history
        j["ai_field_history"] = data.formats[0].ai_field_history
        j["history_joiner"] = data.formats[0].history_joiner
        j["stop_criteria"] = data.formats[0].stop_criteria.copy()
        format_new = format.Format("New-Format", j)
        data.formats.append(format_new)
        embed = discord.Embed(description="Successfully created a new prompt format! Edit it with '/edit_format.'", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin delete a prompt format
    class DeleteFormat_selectmenu(discord.ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = []
            for i in range (len(data.formats)):
                options.append(discord.SelectOption(label=i, description=data.formats[i].name))

            super().__init__(placeholder='Select a prompt format to delete', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            format_found = data.formats[foundat]
        
            # Check if model is used in any configs
            used_location = find_used_config(format_found)
            if used_location != -1:
                embed = discord.Embed(title="Prompt format is used in config '" + data.configs[used_location].name + "'.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            removed = data.formats.pop(foundat)
            embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class DeleteFormatView(discord.ui.View):
        def __init__(self, parent):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.DeleteFormat_selectmenu(parent))

    @app_commands.command(name = "delete_format", description = "Delete a prompt format.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def delete_format(self, interaction : discord.Interaction, id : str = "-1"):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if len(data.formats) < 2:
            embed = discord.Embed(title="Please do not delete all sampling presets.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.DeleteFormatView(self)
            embed = discord.Embed(description="Select a prompt format to delete:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        foundat = await search_for_data(id, data.formats, interaction)
        if foundat == -1:
            return
        format_found = data.formats[foundat]
    
        # Check if model is used in any configs
        used_location = find_used_config(format_found)
        if used_location != -1:
            embed = discord.Embed(title="Prompt format is used in config '" + data.configs[used_location].name + "'.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        removed = data.formats.pop(foundat)
        embed = discord.Embed(description="Successfully deleted '" + removed.name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.edit_original_response(view = None)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets an admin rename a prompt format
    class RenameFormat_selectmenu(discord.ui.Select):
        def __init__(self, parent, new_name):
            self.parent = parent
            self.new_name = new_name
            options = []
            for i in range (len(data.formats)):
                options.append(discord.SelectOption(label=i, description=data.formats[i].name))

            super().__init__(placeholder='Select a prompt format to rename', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            foundat = int(self.values[0])
            format_found = data.formats[foundat]

            if has_repeat(self.new_name, data.formats, format_found):
                embed = discord.Embed(description="Please do not reuse names.", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return

            old_name = format_found.name
            format_found.name = self.new_name

            embed = discord.Embed(description="Successfully renamed '" + old_name + "' to '" + self.new_name + "'!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(view = None)

    # Attaches the above select menu to a view
    class RenameFormatView(discord.ui.View):
        def __init__(self, parent, new_name):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.RenameFormat_selectmenu(parent, new_name))

    @app_commands.command(name = "rename_format", description = "Rename a prompt format.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def rename_format(self, interaction : discord.Interaction, new_name : str, id : str = "-1"):
        if isInt(new_name):
            embed = discord.Embed(description="You are not allowed to use a numerical ID as a name.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.RenameFormatView(self, new_name)
            embed = discord.Embed(description="Select a prompt format to rename:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return

        foundat = await search_for_data(id, data.formats, interaction)
        if foundat == -1:
            return
        format_found = data.formats[foundat]

        if has_repeat(new_name, data.formats, format_found):
            embed = discord.Embed(description="Please do not reuse names.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return

        old_name = format_found.name
        format_found.name = new_name

        embed = discord.Embed(description="Successfully renamed '" + old_name + "' to '" + new_name + "'!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.edit_original_response(view = None)
        
