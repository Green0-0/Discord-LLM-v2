import logging
import discord
from libs import character, config, format, model, params, validator
from discord.ext import commands
from discord import app_commands
import data 

async def setup(bot : commands.Bot):
    await bot.add_cog(Generics(bot))

class Generics(commands.Cog):
    bot : commands.Bot

    def __init__(self, bot : commands.Bot):
        self.bot = bot

    async def is_admin(self, interaction : discord.Interaction) -> bool:
        return interaction.user in data.admins or await self.bot.is_owner(interaction.user)


    @app_commands.command(name = "help", description = "Displays all available commands.")
    async def help(self, interaction : discord.Interaction):
        embed = discord.Embed(title="Help Page", description=
        f""" This is a bot that allows you to use and talk to an LLM. You can ask it for help or simply have conversations with it. 
        One main trait of this bot is the existence of **characters.** A character is simply a profile given to the bot, which the bot acts out. 
        There are four sample characters besides the defaults for each LLM model: Joe Biden (Joke), Donald Trump, (Joke), Stack (Chain-of-thought coding), Commentator (Uncensored political/controversial discussion)
        **To get a response from the bot, simply mention it (@{self.bot.user.name})!**
        To create, edit, and manage your characters, use the following commands:

        /help - displays this message

        /create_character - creates a character
        /config - edit character properties
        /edit_profile - edit character profile

        /change_character - change character
        /list_characters - list all characters
        /view_current_character - view current character
        /delete_character - delete a character

        /change_model - change AI model used for outputs
        /delete_last_interaction - delete the last interaction
        /retry_last_interaction - retry the last interaction
        /clear_memory - clear character memory
        /change_memory_mode - set whether or not the character should remember things

        /get_character_suggestions - get suggestions for how to improve your character profile!
        /shorten_character_profile - shorten your character profile

        There are also some heavily experimental commands that allow you to create conversation channels with a bot, where multiple users (or even characters you have) can talk to a bot.
        /create_thread - create a thread for talking to one specific character with other users
        /delete_thread - delete a thread you made
        /reply_as_current - reply to a character thread with your currently selected character. You can also send a query here to be added to the convo before the character replies.

        Notes:
        Be warned that if the bot is turned off for some reason all your character data will disappear, if you write any dedicated characters make sure to save them in a text file somewhere.
        If the bot doesn't respond to a command or fails an interaction or doesn't update your character info, report it as a bug, if the bot simply takes a long time to reply to you it probably isn't an issue related to the bot.
        If a character is acting weird try fiddling with the temperature, a range of 0.8-1.8 is recommended but varies per model.
        """, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        if not await self.is_admin(interaction):
            return
        embed = discord.Embed(title="Admin Commands", description=
        """ As an admin, you can use the following commands.
        /reload - Reloads the code the bot runs on, allowing updates without data loss
        /purge_webhooks - Deletes all webhooks 
        /get_logs - Gets the last 1000 characters from the console
        
        For only the owner:
        /add_admin - gives someone permission to use the admin commands
        /remove_admin - takes away permissions to use the admin commands""", color=discord.Color.blue())
        await interaction.channel.send(embed=embed)

    @app_commands.command(name = "ping", description = "Pings the bot.")
    async def ping(self, interaction : discord.Interaction):
        await interaction.response.send_message("Pong! " + "(" + str(self.bot.latency * 1000) + "ms)")

    @app_commands.command(name = "add_admin", description = "Allows someone to use the bot admin commands.")
    async def add_admin(self, interaction : discord.Interaction, user : discord.User):
        if not (await self.bot.is_owner(interaction.user)):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if user not in data.admins:
            data.admins.append(user)
            await interaction.response.send_message("Added " + user.mention)
        else:
            await interaction.response.send_message("User is already an admin.")

    @app_commands.command(name = "remove_admin", description = "Removes the permission to use bot admin commands from someone.")
    async def remove_admin(self, interaction : discord.Interaction, user : discord.User):
        if not (await self.bot.is_owner(interaction.user)):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if user in data.admins:
            data.admins.remove(user)
            await interaction.response.send_message("Removed " + user.mention)
        else:
            await interaction.response.send_message("User is not an admin.")

    @app_commands.command(name = "reload", description = "After updating the source code and saving the files, this will reload the bot without losing data.")
    async def reload(self, interaction : discord.Interaction):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name=f"/help for commands, mention @{self.bot.user.name} to talk!"))
        await interaction.response.send_message("Preparing to reload")
        logging.info("Preparing to reload")
        await interaction.channel.send("Loading extensions")
        logging.info("Loading extensions")
        for extension in data.extensions:
            if not extension in data.skip:
                try:
                    if extension in self.bot.extensions:
                        await self.bot.reload_extension(extension)
                    else: 
                        await self.bot.load_extension(extension)
                except Exception as e:
                    await interaction.channel.send("**Error loading extension:** ```" + str(e) + "```")
                    logging.error("Error loading extension: " + str(e))
        await interaction.channel.send("Finished loading extensions")
        logging.info("Finished loading extensions")
        await interaction.channel.send("Syncing slash commands")
        logging.info("Syncing slash commands")
        try:
            await self.bot.tree.sync()
            pass
        except Exception as e:
            await interaction.channel.send("**Error syncing slash commands:** ```" + str(e) + "```")
            logging.error("Error syncing slash commands: " + str(e))
        await interaction.channel.send("Finished syncing slash commands")
        logging.info("Finished syncing slash commands")
        await interaction.channel.send("Finished reloading")
        logging.info("Finished reloading")
        await interaction.channel.send("Note: If the bot was just turned on, please use /purge_webhooks as there will be leftover webhooks from when the bot got turned off")

    @app_commands.command(name = "purge_webhooks", description = "Purges all webhooks the bot has made. Should fix any issues but will slow the bot down.")
    async def purge_webhooks(self, interaction : discord.Interaction):
        if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        await interaction.response.send_message("Purging webhooks")
        s = ""
        for guild in self.bot.guilds:
            try:
                w = await guild.webhooks()
            except:
                w = None
                s += f"Could not delete webhooks in the guild \"{guild.name}\" due to a lack of permissions!\n"
            if w is not None:
                for webhook in w:
                    if webhook.user == self.bot.user:
                        await webhook.delete()
                data.webhookChannels = {name:val for name, val in data.webhookChannels.items() if name.guild != guild}
        if s != "":
            await interaction.channel.send(s)
        else:
            data.webhookChannels = {}
        logging.info(s)
        await interaction.channel.send("Finished purging webhooks")

    @app_commands.command(name = "get_logs", description = "Gets the last 1000 characters from the console.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def get_logs(self, interaction : discord.Interaction):
       if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
       embed = discord.Embed(title="Last 3500 Characters of log", description=data.log_stream.getvalue()[-3500:], color=discord.Color.blue())
       await interaction.response.send_message(embed=embed)

    


