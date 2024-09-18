import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('Bisooo göreve hazır')
    try:
        await bot.load_extension('music')
        await bot.load_extension('commands')  # Komutları yükleyin
    except Exception as e:
        print(f"Extension yüklenirken hata oluştu: {e}")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(TOKEN)
