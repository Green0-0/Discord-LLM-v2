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
        f""" This is a bot that creates character avatars that seamlessly interact with others in channels they are allowed to talk in. 
        One main trait of this bot is the existence of **characters.** 
        A character includes a system prompt and a pfp, each character is allowed to act independently in all channels they are unlocked in.
        To talk to a character, simply say its name, eg. "Hey Trump, how are you?". To force a character to reply use /reply_as
        You can clear memory using /clear_memory.
        You can also view configs/characters/etc using /view_... or /list_...
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
        await interaction.response.send_message("Pong! " + "(" + str(self.bot.latency * 1000) + "ms)", ephemeral=True, delete_after=5)

    @app_commands.command(name = "add_admin", description = "Allows someone to use the bot admin commands.")
    async def add_admin(self, interaction : discord.Interaction, user : discord.User):
        if not (await self.bot.is_owner(interaction.user)):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if user not in data.admins:
            data.admins.append(user)
            embed = discord.Embed(description="Added " + user.mention + " as an admin.", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="User is already an admin.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)

    @app_commands.command(name = "remove_admin", description = "Removes the permission to use bot admin commands from someone.")
    async def remove_admin(self, interaction : discord.Interaction, user : discord.User):
        if not (await self.bot.is_owner(interaction.user)):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
        if user in data.admins:
            data.admins.remove(user)
            embed = discord.Embed(description="Removed admin perms from " + user.mention + ".", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="User is not an admin.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)

    @app_commands.command(name="quick_reload", description = "Reload without syncing slash commands.")
    async def quick_reload(self, interaction : discord.Interaction):
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
        await interaction.channel.send("Finished quick reloading")
        logging.info("Finished quick reloading")
        await interaction.channel.send("Note: If the bot was just turned on, please use /purge_webhooks as there will be leftover webhooks from when the bot got turned off")

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
        text = data.log_stream.getvalue()
        with open("Logs.txt", "w") as file:
            file.write(text[-300000:])
        embed = discord.Embed(title="Last 3500 Characters of log", description="```" + text[-3500:] + "```", color=discord.Color.blue())
        with open("Logs.txt", "rb") as file:
            await interaction.response.send_message(embed=embed, file=discord.File(file, "Logs.txt"), ephemeral=True)               

    @app_commands.command(name = "deep_logging", description = "Toggles deep logging.")
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def deep_logging(self, interaction : discord.Interaction):
       if not await self.is_admin(interaction):
            embed = discord.Embed(title="You do not have permission to use this command.", color=discord.Color.yellow())
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
            return
       if config.Config.deep_logging:
           config.Config.deep_logging = False
           embed = discord.Embed(description="Deep Logging Disabled", color=discord.Color.blue())
           await interaction.response.send_message(embed=embed)
       else:
           config.Config.deep_logging = True
           embed = discord.Embed(description="Deep Logging Enabled", color=discord.Color.blue())
           await interaction.response.send_message(embed=embed)
       

    


