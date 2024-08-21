import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.current_song = None

    @commands.command()
    async def p(self, ctx, url):
        if ctx.author.voice:
            channel = ctx.author.voice.channel

            if self.voice_client is None or not self.voice_client.is_connected():
                self.voice_client = await channel.connect()

            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'noplaylist': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'outtmpl': '%(id)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']
                self.current_song = info['title']

            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }

            def on_audio_end(error):
                if error:
                    print(f"Audio playback error: {error}")
                else:
                    print("Audio playback ended")
                self.current_song = None
                if self.voice_client.is_connected():
                    asyncio.run_coroutine_threadsafe(self.voice_client.disconnect(), self.bot.loop)

            try:
                ffmpeg_audio = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
                self.voice_client.play(ffmpeg_audio, after=on_audio_end)
                await ctx.send('Meow meowww meoww moewwwww')

            except Exception as e:
                print(f"Playback error: {e}")
                await ctx.send("Çalamadım.")

        else:
            await ctx.send('Sese katıl sese!')

    @commands.command()
    async def s(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("İyi bi nefes alayım")

    @commands.command()
    async def r(self, ctx):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("Devamkee")

    @commands.command()
    async def n(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("Bitirseydim be")

    @commands.command()
    async def l(self, ctx):
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send("Allah'a emanet.")
        else:
            await ctx.send("Yokkim ki gardeş.")

async def setup(bot):
    await bot.add_cog(Music(bot))