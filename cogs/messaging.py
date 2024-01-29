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

# Sends a message using webhooks (if possible) to roleplay as a defined character with custom avatar and name
async def send_message_as_character(channel, message : str, character : character.Character, wrapped : bool = False):
    # Webhooks do not work in dm, so roleplay is not possible. Simply sends the message.
    if isinstance(channel, discord.DMChannel):
        if (len(message) > 1900):
            for i in range ((int(len(message)/1900)) + 1):
                if (i == 0):
                    if wrapped: 
                        await channel.send("```" + character.name + ": " + message[i*1900:i*1900+1900] + "```")
                    else: 
                        await channel.send(character.name + ": " + message[i*1900:i*1900+1900])
                else:
                    if wrapped:
                        await channel.send("```" + message[i*1900:i*1900+1900] + "```")
                    else:
                        await channel.send(message[i*1900:i*1900+1900])
        else:
            if wrapped:
                await channel.send("```" + character.name + ": " + message + "```")
            else:
                await channel.send(character.name + ": " + message)
        
    else: 
        # Tries to find a webhook from the cache, if not found uses a new one.
        webhook = await data.get_webhook(channel, character)
        
        # Split up response if it is longer than 2k chars, then sends the message using the webhook previously retrieved
        if (len(message) > 1900):
            for i in range ((int(len(message)/1900)) + 1):
                if wrapped:
                    if isinstance(channel, discord.Thread):
                        await webhook.send("```" + message[i*1900:i*1900+1900] + "```", thread=channel)
                    else:
                        await webhook.send("```" + message[i*1900:i*1900+1900] + "```")
                else:
                    if isinstance(channel, discord.Thread):
                        await webhook.send(message[i*1900:i*1900+1900], thread=channel)
                    else:
                        await webhook.send(message[i*1900:i*1900+1900])
        else:
            if wrapped:
                if isinstance(channel, discord.Thread):
                    await webhook.send("```" + message + "```", thread=channel)
                else:
                    await webhook.send("```" + message + "```")
            else:
                if isinstance(channel, discord.Thread):
                    await webhook.send(message, thread=channel)
                else:
                    await webhook.send(message)

def format_analysis (ch : chat.Chat) -> str:
    chat = []
    users = []
    special_users = []
    for character in data.characters:
        if character.name not in special_users:
            special_users.append("User '" + character.name + "'")
    for message in ch.get_messages(300):
        chat.append("User '" + message.name + "': " + message.text)
        if message.name not in users and message.name not in special_users:
            users.append("User '" + message.name + "'")
    text = "Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request."
    text += "\n\n"
    text += "### Instruction:"
    text += "\n"
    text += "Please determine the next speaker in the conversation. Output their full username."
    text += "\n\n"
    text += "### Input:"
    text += "\n"
    text += """Below is a list of regular users. These users send messages when appropriate, when they are responded to, or simply when they feel like it. Users do not respond to themselves.
User 'John', User 'Sophia', _LIST_
Here are some special users. Special users are particular about sending messages, they only send messages when they are explicitly mentioned by another user. Special users do not respond to themselves.
User 'Nicolas', _LIST-SPECIAL_
Conversation history:
_HISTORY_""".replace("_LIST_", ", ".join(users)).replace("_LIST-SPECIAL_", ", ".join(special_users)).replace("_HISTORY_", "\n".join(chat))
    text += "\n\n"
    text += "### Response:"
    text += "\n"
    text += "Based on my expert analysis, the full name of the next speaker is: User '"
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
        def __init__(self, from_user : str, thing):
            self.from_user = from_user
            self.thing = thing
            options = []
            for i in range (len(data.characters)):
                options.append(discord.SelectOption(label=i, description=data.characters[i].name))

            super().__init__(placeholder='Select a character', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.edit_message(view = None)
            char = data.characters[int(self.values[0])]
            await self.thing.reply(self.from_user, interaction.channel, char)

    # Attaches the above select menu to a view
    class ReplyCharacterView(discord.ui.View):
        def __init__(self, parent, from_user : str, thing):
            super().__init__()

            # Adds the dropdown to our view object.
            self.add_item(parent.ReplyCharacter_selectmenu(from_user, thing))

    @app_commands.command(name = "reply_as", description = "Replies as a given character.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def reply_as(self, interaction : discord.Interaction):
        if self.working == True:
            embed = discord.Embed(description="Currently busy...", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        view = self.ReplyCharacterView(self, interaction.user.display_name, self)
        embed = discord.Embed(description="Select a character:", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True, delete_after=10)

    # Bot receives mentions and responds to them using the current character with the AI
    @commands.Cog.listener()
    async def on_message(self, message : discord.Message):
        if message.content == "":
            return
        if message.content == "*thinking*":
            return
        if message.clean_content.startswith("-"):
            return
        data.get_chat(message.channel.id).append(chat.Message(message.author.display_name, message.clean_content, data.tokenizer))
        if self.working == True:
            return
        if not message.guild.get_member(self.bot.user.id).guild_permissions.manage_webhooks:
            logging.info("Missing webhook perms for sending messages in " + message.guild.name)
            embed = discord.Embed(title="The bot is missing webhook permissions in this server!", color=discord.Color.red())
            await message.channel.send(embed=embed)
            return
        await self.read (message.author.display_name, message.clean_content, message.channel)
    
    async def read (self, from_user : str, content : str, channel):
        if len(data.get_chat(channel.id).messages) == 0:
            return

        self.working = True

        try:
            analysis = await data.analysis_config.queue(chat.Chat(format_analysis(data.get_chat(channel.id)), data.tokenizer), data.characters[0], "", data.tokenizer)
        except Exception as e:
            logging.error(e)
            self.working = False
            return

        if analysis.find("'") != -1:
            analysis = analysis[:analysis.find("'")]
        character_names = []
        for character in data.characters:
            character_names.append(character.name.lower())
        character = "" 
        for x in range(len(character_names)):
            if analysis.lower() in character_names[x]:
                character = data.characters[x]
                break
        if character == "":
            self.working = False
            return
        if character.name == data.get_chat(channel.id).messages[-1].name:
            self.working = False
            return
        await self.reply (from_user, channel, character)

    async def reply (self, from_user : str, channel, character : character.Character):
        self.working = True
        await send_message_as_character(channel, "*thinking*", character)
        try:
            response = await data.configs[3].queue(data.get_chat(channel.id), character, from_user, data.tokenizer)
        except Exception as e:
            logging.error(e)
            embed = discord.Embed(title="Error while attempting to reply as " + character.name + ": ", description = str(e), color=discord.Color.red())
            await channel.send(embed=embed)
            self.working = False
            return
        await send_message_as_character(channel, response, character)
        self.working = False
        await self.read(character.name, response, channel)
