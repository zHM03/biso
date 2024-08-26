import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
))

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.queue = []
        self.is_playing = False

        # yt-dlp ayarları
        self.ytdl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': '%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '256',
            }],
        }
        
    async def connect_to_voice_channel(self, ctx, channel):
        if channel.id not in self.voice_clients or not self.voice_clients[channel.id].is_connected():
            voice_client = await channel.connect()
            self.voice_clients[channel.id] = voice_client
        return self.voice_clients[channel.id]

    async def play_next(self):
        """Bir sonraki şarkıyı çal"""
        if self.queue:
            self.is_playing = True
            song = self.queue.pop(0)
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            try:
                ffmpeg_audio = discord.FFmpegPCMAudio(song['url'], **ffmpeg_options)
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                self.voice_client.play(ffmpeg_audio, after=lambda e: self.bot.loop.create_task(self.play_next()))
                channel = self.bot.get_channel(song['channel_id'])
                await channel.send(f"🎶 {song['title']} 🎶 çalıyor!")
            except Exception as e:
                print(f"Playback error: {e}")
                channel = self.bot.get_channel(song['channel_id'])
                await channel.send("Şarkıyı çalamadım.")
                self.is_playing = False
                await self.play_next()
        else:
            self.is_playing = False

    async def play_song(self, ctx, audio_url, song_title):
        """Şarkıyı kuyruğa ekler ve çalmaya başlar"""
        song = {
            'url': audio_url,
            'title': song_title,
            'channel_id': ctx.channel.id
        }
        self.queue.append(song)
        queue_message = "Kuyruğa eklendi:\n"
        for index, song in enumerate(self.queue):
            queue_message += f"{index + 1}. {song['title']}\n"
        await ctx.send(queue_message)

        if not self.is_playing:
            if not self.voice_client or not self.voice_client.is_connected():
                self.voice_client = await ctx.author.voice.channel.connect()
            await self.play_next()

    @commands.command()
    async def p(self, ctx, *, link):
        """YouTube veya Spotify bağlantısından şarkı ekler"""
        if not ctx.author.voice:
            await ctx.send("Bir sesli kanalda olmalısın!")
            return

        with YoutubeDL(self.ytdl_opts) as ydl:
            try:
                if "youtube.com/watch" in link or "youtu.be" in link:
                    # Eğer doğrudan YouTube URL'si ise, doğrudan bilgi al
                    info = ydl.extract_info(link, download=False)
                    await self.play_song(ctx, info['url'], info['title'])

                elif "spotify.com/track" in link:
                    # Eğer Spotify parça URL'si ise, Spotify'tan şarkı bilgilerini al
                    track_id = link.split('/')[-1].split('?')[0]
                    track_info = sp.track(track_id)
                    track_name = track_info['name']
                    artist_name = track_info['artists'][0]['name']
                    search_query = f"{track_name} {artist_name}"
                    
                    # Arama terimi ile bilgi al
                    search_query = f"ytsearch:{search_query}"
                    info = ydl.extract_info(search_query, download=False)
                    if 'entries' in info and len(info['entries']) > 0:
                        info = info['entries'][0]
                    await self.play_song(ctx, info['url'], info['title'])

                elif "spotify.com/playlist" in link:
                    # Eğer Spotify çalma listesi URL'si ise, listedeki tüm şarkıları ekle
                    playlist_id = link.split('/')[-1].split('?')[0]
                    playlist_info = sp.playlist(playlist_id)
                    for item in playlist_info['tracks']['items']:
                        track = item['track']
                        track_name = track['name']
                        artist_name = track['artists'][0]['name']
                        search_query = f"{track_name} {artist_name}"
                        
                        # Arama terimi ile bilgi al
                        search_query = f"ytsearch:{search_query}"
                        info = ydl.extract_info(search_query, download=False)
                        if 'entries' in info and len(info['entries']) > 0:
                            info = info['entries'][0]
                        await self.play_song(ctx, info['url'], info['title'])

                else:
                    # Arama terimi ile bilgi al
                    search_query = f"ytsearch:{link}"
                    info = ydl.extract_info(search_query, download=False)
                    if 'entries' in info and len(info['entries']) > 0:
                        info = info['entries'][0]
                    await self.play_song(ctx, info['url'], info['title'])

            except Exception as e:
                print(f"Error extracting audio: {e}")
                await ctx.send("Şarkıyı çalamadım.")

    @commands.command()
    async def n(self, ctx):
        """Çalınan şarkıyı atlar"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("Şarkıyı atlattım.")
        else:
            await ctx.send("Şu anda çalan bir şarkı yok.")

    @commands.command()
    async def l(self, ctx):
        """Botu sesli kanaldan çıkarır"""
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.queue.clear()
            self.is_playing = False
            await ctx.send("Sesli kanaldan ayrıldım.")
        else:
            await ctx.send("Bot bir sesli kanalda değil.")

    @commands.command()
    async def s(self, ctx):
        """Şarkıyı duraklatır"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("Şarkıyı duraklattım.")
        else:
            await ctx.send("Şu anda çalan bir şarkı yok.")

    @commands.command()
    async def r(self, ctx):
        """Şarkıyı devam ettirir"""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("Şarkıyı devam ettiriyorum.")
        else:
            await ctx.send("Şu anda duraklatılmış bir şarkı yok.")

async def setup(bot):
    await bot.add_cog(Music(bot)) 
