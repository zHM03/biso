import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import commands as cmd
import events
import music

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Events ve komutlar burada yükleniyor
events.setup(bot)
cmd.setup(bot)

@bot.event
async def on_ready():
    print('Bisooo göreve hazır')
    try:
        await bot.load_extension('music')
    except Exception as e:
        print(f"Extension yüklenirken hata oluştu: {e}")        
        
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(TOKEN)