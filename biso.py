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

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data['custom_id'] == 'skip':
            ctx = await bot.get_context(interaction.message)
            await ctx.invoke(bot.get_command('skip'))
        elif interaction.data['custom_id'] == 'pause':
            ctx = await bot.get_context(interaction.message)
            await ctx.invoke(bot.get_command('pause'))
        elif interaction.data['custom_id'] == 'resume':
            ctx = await bot.get_context(interaction.message)
            await ctx.invoke(bot.get_command('resume'))
        elif interaction.data['custom_id'] == 'stop':
            ctx = await bot.get_context(interaction.message)
            await ctx.invoke(bot.get_command('stop'))
        elif interaction.data['custom_id'] == 'clear':
            ctx = await bot.get_context(interaction.message)
            await ctx.invoke(bot.get_command('clear'))


        
        
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(TOKEN)
