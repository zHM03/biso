import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
from collections import deque

load_dotenv()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.current_song = None
        self.queue = deque()  # Kuyruk için bir deque oluşturun

        # Spotify API yetkilendirme
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv('SPOTIPY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
        ))

    def get_spotify_track_name(self, url):
        try:
            track_id = url.split('/')[-1].split('?')[0]
            track_info = self.sp.track(track_id)
            track_name = track_info['name']
            artist_name = track_info['artists'][0]['name']
            return f"{track_name} {artist_name}"
        except Exception as e:
            print(f"Error retrieving Spotify track info: {e}")
            return None

    def get_spotify_playlist_tracks(self, playlist_url):
        try:
            playlist_id = playlist_url.split('/')[-1].split('?')[0]
            results = self.sp.playlist_tracks(playlist_id)
            tracks = [{'name': f"{item['track']['name']} {item['track']['artists'][0]['name']}",
                       'id': item['track']['id']} for item in results['items']]
            return tracks
        except Exception as e:
            print(f"Error retrieving Spotify playlist: {e}")
            return []

    async def play_next(self, ctx):
        if self.queue:
            next_song = self.queue.popleft()  # Kuyruktan bir şarkıyı çıkar
            search_query = next_song['search_query']
            audio_url = next_song['url']
            self.current_song = next_song['title']

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
                self.bot.loop.create_task(self.play_next(ctx))  # Kuyruğu kontrol et

            try:
                ffmpeg_audio = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                self.voice_client.play(ffmpeg_audio, after=on_audio_end)
                await ctx.send(f"🎶 {self.current_song} 🎶 ")

            except Exception as e:
                print(f"Playback error: {e}")
                await ctx.send("Çalamadım.")
                
    # Music sınıfı içinde
    @commands.command()
    async def show_queue(self, ctx):
        visualize = self.bot.get_cog("Visualize")
        if visualize:
         await visualize.show_queue(ctx, self.queue)
        else:
            await ctx.send("Visualize modülü yüklenmemiş.")

    @commands.command()
    async def p(self, ctx, *, search):
        if ctx.author.voice:
            channel = ctx.author.voice.channel

        if self.voice_client is None or not self.voice_client.is_connected():
            self.voice_client = await channel.connect()

        ydl_opts = {
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

        search_query = search

        if "spotify.com/track" in search:
            track_name = self.get_spotify_track_name(search)
            if track_name is None:
                await ctx.send("Şarkıyı bilmiyorum.")
                return
            search_query = f"ytsearch:{track_name}"
        elif "spotify.com/playlist" in search:
            playlist_tracks = self.get_spotify_playlist_tracks(search)
            if not playlist_tracks:
                await ctx.send("Playlisti bilmiyorum.")
                return

            # İlk şarkıyı arat ve çal
            first_track = playlist_tracks[0]
            search_query = f"ytsearch:{first_track['name']}"
            with YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(search_query, download=False)['entries'][0]
                    audio_url = info['url']
                    song_title = info['title']

                    self.queue.append({
                        'search_query': search_query,
                        'url': audio_url,
                        'title': song_title
                    })

                    # Kuyruğa diğer şarkıları ekle
                    for track in playlist_tracks[1:]:
                        search_query = f"ytsearch:{track['name']}"
                        self.queue.append({'search_query': search_query, 'url': None, 'title': track['name']})

                    if not self.voice_client.is_playing() and not self.voice_client.is_paused():
                        await self.play_next(ctx)
                    else:
                        await ctx.send(f"Playlist kuyruktadır, ilk şarkı çalınıyor ve diğer şarkılar aratılıyor.")
                    
                    # Diğer şarkıları arat ve kuyruğa ekle
                    for track in playlist_tracks[1:]:
                        search_query = f"ytsearch:{track['name']}"
                        with YoutubeDL(ydl_opts) as ydl:
                            try:
                                info = ydl.extract_info(search_query, download=False)['entries'][0]
                                audio_url = info['url']
                                song_title = info['title']

                                # Kuyrukta bulunan ilgili şarkının URL'sini güncelle
                                for item in self.queue:
                                    if item['title'] == track['name']:
                                        item['url'] = audio_url
                                        break

                            except Exception as e:
                                print(f"Error extracting audio: {e}")

                except Exception as e:
                    print(f"Error extracting audio for the first track: {e}")
                    await ctx.send("İlk şarkıyı çalamadım.")

        else:
            search_query = f"ytsearch:{search}"
            with YoutubeDL(ydl_opts) as ydl:
                try:
                    if "youtube.com" in search_query or "youtu.be" in search_query:
                        info = ydl.extract_info(search_query, download=False)
                        if 'entries' in info and len(info['entries']) > 0:
                            info = info['entries'][0]
                        else:
                            raise ValueError("No entries found in YouTube search results.")
                    else:
                        info = ydl.extract_info(search_query, download=False)['entries'][0]

                    audio_url = info['url']
                    song_title = info['title']

                    self.queue.append({
                        'search_query': search_query,
                        'url': audio_url,
                        'title': song_title
                    })

                    if not self.voice_client.is_playing() and not self.voice_client.is_paused():
                        await self.play_next(ctx)

                    # Anında kuyruk listesini göster
                    await self.show_queue(ctx)

                except Exception as e:
                    print(f"Error extracting audio: {e}")
                    await ctx.send("Hafızamda yok be.")

    @commands.command()
    async def s(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("İyi bi nefes alıp veriyoruz...")
        elif self.voice_client:
            await ctx.send("Şu anda duraklatılmış bir şey yok.")

    @commands.command()
    async def r(self, ctx):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("Süper, devam")
        elif self.voice_client:
            await ctx.send("Şu anda duraklatılmış bir şey yok.")

    @commands.command()
    async def n(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("Bir sonraki şarkıya geçiyorum.")
            await self.play_next(ctx)

    @commands.command()
    async def l(self, ctx):
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send("Seni yalnız bırakıyorum!")

async def setup(bot):
    await bot.add_cog(Music(bot))
