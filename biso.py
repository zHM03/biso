import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from pydub import AudioSegment
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Biso göreve hazır')
    
@bot.command()
async def biso(ctx):
    """Botun yanıt süresini gösterir."""
    await ctx.send('Meow!')
    

# botla mesajlaşma komutu
@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    if message.content.lower() == 'sa':
        await message.channel.send(f'as {message.author.mention}!')
        
    elif message.content.lower() == 'merhaba':
        await message.channel.send(f'merhabana merhaba gardeeş {message.author.mention}!')
        
    elif message.content.lower() == 'selam':
        await message.channel.send(f'selam {message.author.mention}!')
        
    await bot.process_commands(message)


 #!uçur komutu
@bot.command()
@commands.has_permissions(kick_members=True)
async def uçur(ctx, member: discord.Member, *, reason=None):
    """Etiketlenen kişiyi sunucudan atar."""
    if ctx.author == member:
        await ctx.send("bunu benden yapmamı isteme!")
        return
    
    # Botun rolünü ve etiketlenen kişinin rolünü al
    bot_role = ctx.guild.get_member(bot.user.id).top_role

    if bot_role.position <= member.top_role.position:
        await ctx.send("Sen kimsin lan!")
        return

    try:
        # Öncelikle bilgilendirme mesajını gönder
        await ctx.send("Patimi yalıyorum bi saniye...")

        # Sonra ikinci mesajı gönder
        await ctx.send(f"{member} Götüne tekmeyi vurdum, UÇURDUM!! fiyuuu ㅇㅅㅇ")

        # Kullanıcıyı sunucudan at
        await member.kick(reason=reason)
    except discord.Forbidden:
        await ctx.send("üşendim.")
    except discord.HTTPException as e:
        await ctx.send(f"Başaramdık usta, sağlam çıktı: {e}")

@bot.command()
async def play(ctx, url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        mp3_file = filename.replace('.webm', '.mp3')  # Eğer .webm formatında indirildiyse

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        voice_client = await channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(mp3_file))

        await ctx.send(f'Çalınıyor: {info["title"]}')

        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()

        os.remove(mp3_file)
    else:
        await ctx.send('Önce bir ses kanalına katılmalısınız!')

bot.run(TOKEN)




