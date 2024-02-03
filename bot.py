import discord
from discord.ext import commands
import data 
import logging
from io import StringIO
from discord import app_commands

log_stream = StringIO()    
logger = logging.basicConfig(stream=log_stream, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
data.init(log_stream)

class LLM (commands.Bot):
    shown_warning = False
    async def setup_hook(self):
        logging.info("Bot is starting")
        await bot.load_extension("cogs.generics")
        await self.tree.sync()

# Sets up bot
intents = discord.Intents.default()
intents.message_content = True
bot = LLM(command_prefix="", intents=intents, help_command=None)

# Finishes setting up the bot
@bot.event
async def on_ready():
    if bot.shown_warning == False: 
        bot.shown_warning = True
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name="/reload MUST BE USED BY A BOT ADMIN/OWNER!"))
    logging.info(f'Logged in as {bot.user}, begin using the bot!')

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):
    logging.info(error)
    s = ""
    if not interaction.guild.get_member(bot.user.id).guild_permissions.embed_links:
        s += "The bot is missing embed link permissions in this server!\n"
    if not interaction.guild.get_member(bot.user.id).guild_permissions.manage_webhooks:
        s += "The bot is missing webhook permissions in this server!\n"
    if not interaction.guild.get_member(bot.user.id).guild_permissions.manage_threads:
        s += "The bot is missing thread edit permissions in this server!\n"
    await interaction.response.send_message(s)
    

bot.run(data.TOKEN, log_handler=logger)