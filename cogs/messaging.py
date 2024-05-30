from libs import character, chat
import sys
import logging
import traceback
import data

import discord
from discord.ext import commands
from discord import app_commands

async def setup(bot : commands.Bot):
    await bot.add_cog(Messaging(bot))

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

# Sends a message using webhooks (if possible) to roleplay as a defined character with custom avatar and name
async def send_message_as_character(channel, message : str, character : character.Character, edit_first = None) -> list:
    sent_content = []
    # Webhooks do not work in dm, so roleplay is not possible. Simply sends the message.
    if isinstance(channel, discord.DMChannel):
        if (len(message) > 1900):
            appending_code = False
            for i in range ((int(len(message)/1900)) + 1):
                message_text = message[i*1900:i*1900+1900]
                if message_text.count("```") % 2 != 0:
                    if appending_code:
                        message_text = "```" + message_text
                        appending_code = False
                    else:
                        message_text =  message_text + "```"
                        appending_code = True
                elif appending_code:
                    message_text = "```" + message_text + "```"
                    
                if (i == 0):
                    if edit_first != None:
                        w = edit_first
                        await edit_first.edit(content = "From " + character.name + ": " + message_text)
                    else:
                        w = await channel.send("From " + character.name + ": " + message_text)
                    sent_content.append(w)
                else:
                    w = await channel.send(message_text)
                    sent_content.append(w)
        else:
            if (message.count("```") % 2 != 0):
                message = message + "```"
            if edit_first != None:
                w = edit_first
                await edit_first.edit(content = "From " + character.name + ": " + message)
            else:
                w = await channel.send("From " + character.name + ": " + message)
            sent_content.append(w)
        
    else: 
        # Tries to find a webhook from the cache, if not found uses a new one.
        webhook = await data.get_webhook(channel, character)
        
        # Split up response if it is longer than 2k chars, then sends the message using the webhook previously retrieved
        if (len(message) > 1900):
            appending_code = False
            for i in range ((int(len(message)/1900)) + 1):
                message_text = message[i*1900:i*1900+1900]
                if message_text.count("```") % 2 != 0:
                    if appending_code:
                        message_text = "```" + message_text
                        appending_code = False
                    else:
                        message_text =  message_text + "```"
                        appending_code = True
                if isinstance(channel, discord.Thread):
                    if (i == 0 and edit_first != None):
                        w = edit_first
                        await edit_first.edit(content = message_text)
                    else:
                        w = await webhook.send(message_text, thread=channel)
                    sent_content.append(w)
                else:
                    if (i == 0 and edit_first != None):
                        w = edit_first
                        await edit_first.edit(content = message_text)
                    else:
                        w = await webhook.send(message_text, wait=True)
                    sent_content.append(w)
        else:
            if (message.count("```") % 2 != 0):
                message = message + "```"
            if isinstance(channel, discord.Thread):
                if (edit_first != None):
                    w = edit_first
                    await edit_first.edit(content = message)
                else:
                    w = await webhook.send(message, thread=channel)
                sent_content.append(w)
            else:
                if (edit_first != None):
                    w = edit_first
                    await edit_first.edit(content = message)
                else:
                    w = await webhook.send(message, wait=True)
                sent_content.append(w)
    return sent_content

def format_analysis (ch : chat.Chat, channelId, character=character) -> str:    
    conv = []
    users = []
    special_users = []
    for chh in data.characters:
        if 'all' in chh.channels:
            if channelId not in chh.channels:
                namekey = "User '" + chh.name + "'"
                if namekey not in special_users:
                    special_users.append(namekey)
        else:  
            if channelId in chh.channels: 
                namekey = "User '" + chh.name + "'"
                if namekey not in special_users:
                    special_users.append(namekey)
    if len(special_users) == 0:
        return ""
    for message in ch.get_messages(350, min_messages=2):
        namekey = "User '" + message.name + "'"
        conv.append(message.name + ": " + message.text)
        if namekey not in users and namekey not in special_users:
            users.append(namekey)
    # real history is everything but the last message, and the last message says "Latest Message : xxx"
    finalmsg = f"""Regular users speak when they want to say something, when they are mentioned, when nobody else will reply, etc.
Regular users: _LIST_
Special users speak when they are spoken to or relevant in the latest message.
Special users: User 'None' (if no user is relevant or mentioned, output this user),  _LIST-SPECIAL_
Note: The speaker in the latest message will not speak again.
Below is the conversation history:
_HISTORY_""".replace("_LIST_", ", ".join(users)).replace("_LIST-SPECIAL_", ", ".join(special_users)).replace("_HISTORY_", "\n".join(conv[:-1]) + "\n\n[Latest Message]: " + conv[-1])
    finalmsg += "\nPlease determine the next speaker (regular or special user) in the conversation."
    c = character.Character(None, "assistant", "", "You are a helpful assistant.")
    ch = chat.Chat(finalmsg, tokenizer=data.tokenizer)
    text = data.analysis_format.build_prompt(c, "user", ch, 4000, data.tokenizer)    
    text += "The next speaker is: User '"
    return text

# Cog that manages all events which require an LLM response
class Messaging(commands.Cog):
    working : bool
    bot : commands.Bot
    
    def __init__(self, bot : commands.Bot):
        self.working = False
        self.bot = bot

    # Ignores errors of a command not being found (this is a user side issue not an issue to be worried about)
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        ignored = (commands.CommandNotFound, )
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return
        logging.error('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        if isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(title="The bot is missing webhook permissions in this server!", color=discord.Color.red())
            await ctx.send(embed=embed)

    @app_commands.command(name = "force_restart", description = "May stop freezing bugs.")
    async def force_restart(self, interaction : discord.Interaction):
        embed = discord.Embed(description="Force restarted...", color=discord.Color.yellow())
        await interaction.response.send_message(embed=embed)
        working = False

    @app_commands.command(name = "clear_memory", description = "Clears chat history for all characters in the given channel.")
    async def clear_memory(self, interaction : discord.Interaction):
        embed = discord.Embed(description="Memory cleared!", color=discord.Color.blue())
        data.get_chat(interaction.channel.id).messages = []
        await interaction.response.send_message(embed=embed)

    # A select menu is basically a dropdown where the user has to pick one of the options
    # A select menu that lets the user choose one of their characters to talk to
    class ReplyCharacter_selectmenu(discord.ui.Select):
        def __init__(self, parent, from_user : str):
            self.from_user = from_user
            self.parent = parent
            options = []
            for i in range (len(data.characters)):
                options.append(discord.SelectOption(label=i, description=data.characters[i].name))

            super().__init__(placeholder='Select a character', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            if self.parent.working == True:
                embed = discord.Embed(description="Currently busy...", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            if len(data.get_chat(interaction.channel.id).messages) == 0:
                embed = discord.Embed(description="Nothing to reply to!", color=discord.Color.yellow())
                await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
                return
            await interaction.response.edit_message(view = None)
            char = data.characters[int(self.values[0])]
            await self.parent.reply(self.from_user, interaction.channel, char)

    # Attaches the above select menu to a view
    class ReplyCharacterView(discord.ui.View):
        def __init__(self, parent, from_user : str):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.ReplyCharacter_selectmenu(parent, from_user))

    @app_commands.command(name = "reply_as", description = "Replies as a given character.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def reply_as(self, interaction : discord.Interaction, id : str = "-1"):
        if self.working == True:
            embed = discord.Embed(description="Currently busy...", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if len(data.get_chat(interaction.channel.id).messages) == 0:
            embed = discord.Embed(description="Nothing to reply to!", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if id == "-1":
            view = self.ReplyCharacterView(self, interaction.user.display_name)
            embed = discord.Embed(description="Select a character:", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True, delete_after=10)
            return
        foundat = await search_for_data(id, data.characters, interaction)
        if foundat == -1:
            return
        self.working = True
        await interaction.response.send_message("✔", ephemeral=True, delete_after=1)
        await self.reply(interaction.user.display_name, interaction.channel, data.characters[foundat])
        
    @app_commands.command(name = "delete_last", description = "Deletes the last sent AI message OR your own message.")
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    async def delete_last(self, interaction : discord.Interaction):
        chat = data.get_chat(interaction.channel.id)
        if len(chat.messages) == 0:
            embed = discord.Embed(description="Nothing to delete!", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if chat.messages[-1].name != interaction.user.display_name and chat.messages[-1].character == None:
            embed = discord.Embed(description="Only your own messages/AI messages can be deleted!", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        for p in chat.messages[-1].parts:
            await p.delete()
        chat.messages.pop()
        await interaction.response.send_message("✔", ephemeral=True, delete_after=1)
        
    @app_commands.command(name = "retry_last", description = "Retries the last AI sent message.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def retry_last(self, interaction : discord.Interaction):
        if self.working == True:
            embed = discord.Embed(description="Currently busy...", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if len(data.get_chat(interaction.channel.id).messages) == 0:
            embed = discord.Embed(description="Nothing to retry!", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        chat = data.get_chat(interaction.channel.id)
        target_character = chat.messages[-1].character
        if target_character == None:
            embed = discord.Embed(description="Only AI messages can be retried!", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        for p in chat.messages[-1].parts:
            await p.delete()
        chat.messages.pop()
        await interaction.response.send_message("✔", ephemeral=True, delete_after=1)
        await self.reply(chat.messages[-1].name, interaction.channel, target_character)

    # Bot receives mentions and responds to them using the current character with the AI
    @commands.Cog.listener()
    async def on_message(self, message : discord.Message):
        if message.content == "":
            return
        if message.clean_content.startswith("-"):
            return
        if message.webhook_id != None:
            return
        if message.author.id == self.bot.user.id:
            return
        data.get_chat(message.channel.id).append(chat.Message(message.author.display_name, message.clean_content, data.tokenizer, [message]))
        if self.working == True:
            return
        if not isinstance(message.channel, discord.DMChannel):
            if not message.guild.get_member(self.bot.user.id).guild_permissions.manage_webhooks:
                logging.error("Missing webhook perms for sending messages in " + message.guild.name)
                embed = discord.Embed(title="The bot is missing webhook permissions in this server!", color=discord.Color.red())
                await message.channel.send(embed=embed)
                return
        await self.read (message.author.display_name, message.clean_content, message.channel)
    
    async def read (self, from_user : str, content : str, channel):
        self.working = True
        try:
            msg = format_analysis(data.get_chat(channel.id), channel.id)
            if msg == "":
                self.working = False
                return
            analysis = await data.analysis_config.queue(chat.Chat(msg, data.tokenizer), data.characters[0], "", data.tokenizer)
        except Exception as e:
            logging.error(e)
            self.working = False
            return
        if analysis.find("'") != -1:
            analysis = analysis[:analysis.find("'")]
        character_names = []
        for character in data.characters:
            if 'all' not in character.channels:
                if channel.id not in character.channels:
                    character_names.append("2a973sd8294chy3iu234h")
                    continue
            elif channel.id in character.channels:
                character_names.append("2a973sd8294chy3iu234h")
                continue
            character_names.append(character.name.lower())
        character = "" 
        for x in range(len(character_names)):
            if analysis.lower() in character_names[x]:
                character = data.characters[x]
                break
        if character == "":
            self.working = False
            return
        if len(data.get_chat(channel.id).messages) == 0:
            self.working = False
            return
        if character.name == data.get_chat(channel.id).messages[-1].name:
            self.working = False
            return
        await self.reply (from_user, channel, character)

    async def reply (self, from_user : str, channel, character : character.Character):
        self.working = True
        msgs = await send_message_as_character(channel, "*thinking*", character)
        try:
            if channel.id in character.reminders:
                data.get_chat(channel.id).inject_reminder(character.reminders[channel.id])
            response = await character.conf.queue(data.get_chat(channel.id), character, from_user, data.tokenizer)
        except Exception as e:
            logging.error(e)
            embed = discord.Embed(title="Error while attempting to reply as " + character.name + ": ", description = str(e), color=discord.Color.red())
            await channel.send(embed=embed)
            self.working = False
            return
        w = await send_message_as_character(channel, response, character, msgs[0])
        data.get_chat(channel.id).append(chat.Message(character.name, response, data.tokenizer, w, character))
        self.working = False
        await self.read(character.name, response, channel)
