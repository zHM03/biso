import discord
from discord.ext import commands
from discord.ui import View, Button
from yt_dlp import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
from visualize import Visualizer

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
        self.user_queue = []
        self.is_playing = False
        self.items_per_page = 5
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
        self.last_message = None
        self.search_task = None
        self.visualizer = Visualizer()

    async def play_song(self, ctx, audio_url, song_title):
        """Şarkıyı hem kod kuyruğuna hem de kullanıcı kuyruğuna ekler ve çalmaya başlar"""
        song = {
            'url': audio_url,
            'title': song_title,
            'channel_id': ctx.channel.id,
            'status': 'playing' if not self.is_playing else 'pending'  # İlk şarkı için playing, diğerleri için pending
        }
        # Şarkıyı hem kod kuyruğuna hem de kullanıcı kuyruğuna ekle
        self.queue.append(song)
        self.user_queue.append(song)
        
        # Kuyruğu güncelle
        await self.send_queue(ctx)
        
        if not self.is_playing:
            if not self.voice_client or not self.voice_client.is_connected():
                self.voice_client = await ctx.author.voice.channel.connect()
            await self.play_next()
    
    async def play_next(self):
        """Bir sonraki şarkıyı çal"""
        if len(self.queue) > 0:  # Kod kuyrukta şarkı varsa
            self.is_playing = True  # Oynatma durumunu aktif olarak ayarla
    
            # Kuyruğun ilk şarkısını seç
            song = self.queue[0]
            song['status'] = 'playing'  # Durumu 'playing' olarak ayarla
    
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
    
            def after_playing(error):
                if error:
                    print(f'Error: {error}')
                # Şarkı tamamlandığında durumu güncelle
                self.bot.loop.create_task(self.song_finished(song))
                
            try:
                # Ses dosyasını oynat
                self.voice_client.play(discord.FFmpegPCMAudio(song['url'], **ffmpeg_options), after=after_playing)
                
                # Kuyruğu güncelle
                # await self.send_queue(self.bot.get_channel(song['channel_id']), page=1)  # Bu satırı kaldırdık
    
            except Exception as e:
                print(f'Error: {str(e)}')
                self.is_playing = False
                # Hata durumunda kuyruğu yeniden başlat
                await self.play_next()
        else:
            self.is_playing = False  # Kuyruk boşsa oynatmayı durdur
            if self.voice_client and self.voice_client.is_connected():
                # Kuyruk hala boşsa ve sesli kanalda kimse yoksa ayrıl
                await self.voice_client.disconnect()
                self.user_queue.clear()  # Kullanıcı kuyruğunu temizle
    
    async def song_finished(self, song):
        """Şarkı bitince çalışacak işlem"""
        # Tamamlanan şarkıyı tamamlanmış olarak işaretle
        song['status'] = 'completed' 
        # Şarkı bitiminden sonra kuyruğun ilk şarkısını çıkar
        self.queue.pop(0)
        
        # Eğer kuyruğunda daha fazla şarkı varsa bir sonraki şarkıyı çalmaya başla
        if len(self.queue) > 0:
            # Kuyruğun ilk şarkısını 'playing' olarak ayarla
            self.queue[0]['status'] = 'playing'
            # Kuyruğu güncelle (sadece bir kez)
            await self.send_queue(self.bot.get_channel(self.queue[0]['channel_id']))  
            await self.play_next()
    
    
    async def send_queue(self, ctx, page=1):
        num_pages = (len(self.user_queue) + self.items_per_page - 1) // self.items_per_page
    
        buffer = await self.visualizer.generate_queue_image(self.user_queue, page)
    
        if self.last_message:
            try:
                await self.last_message.delete()
            except discord.NotFound:
                pass
    
        new_message = await ctx.send(file=discord.File(fp=buffer, filename='queue.png'))
    
        self.last_message = new_message
    
        view = self.QueueView(self.bot, new_message, page=page, num_pages=num_pages)
        await new_message.edit(view=view)

    class QueueView(View):
        def __init__(self, bot, message, page=1, num_pages=1):
            super().__init__(timeout=360)
            self.bot = bot
            self.message = message
            self.page = page
            self.num_pages = num_pages
            self.items_per_page = 5
            self.user_queue = bot.get_cog("Music").user_queue

            self.prev_button = Button(label="Prev", style=discord.ButtonStyle.primary, disabled=(self.page == 1))
            self.next_button = Button(label="Next", style=discord.ButtonStyle.primary, disabled=(self.page == self.num_pages))

            self.prev_button.callback = self.prev_page
            self.next_button.callback = self.next_page

            self.add_item(self.prev_button)
            self.add_item(self.next_button)

        async def prev_page(self, interaction: discord.Interaction):
            if self.page > 1:
                self.page -= 1
                await self.update_message(interaction)

        async def next_page(self, interaction: discord.Interaction):
            if self.page < self.num_pages:
                self.page += 1
                await self.update_message(interaction)

        async def update_message(self, interaction: discord.Interaction):
            cog = self.bot.get_cog("Music")
            await cog.send_queue(interaction.channel, page=self.page)
            await interaction.response.defer()

    @commands.command()
    async def p(self, ctx, *, link):
        """YouTube veya Spotify bağlantısından şarkı ekler"""
        if not ctx.author.voice:
            await ctx.send("Bir sesli kanalda olmalısın!")
            return

        if self.voice_client and self.voice_client.channel != ctx.author.voice.channel:
            await ctx.send("Müsait değilim.")
            return

        if self.search_task and not self.search_task.done():
            self.search_task.cancel()

        with YoutubeDL(self.ytdl_opts) as ydl:
            try:
                if "youtube.com/watch" in link or "youtu.be" in link:
                    info = ydl.extract_info(link, download=False)
                    await self.play_song(ctx, info['url'], info['title'])
                    await ctx.message.add_reaction('✅')

                elif "spotify.com/track" in link:
                    track_id = link.split('/')[-1].split('?')[0]
                    track_info = sp.track(track_id)
                    track_name = track_info['name']
                    artist_name = track_info['artists'][0]['name']
                    search_query = f"{track_name} {artist_name}"
                    search_query = f"ytsearch:{search_query}"
                    info = ydl.extract_info(search_query, download=False)
                    if 'entries' in info and len(info['entries']) > 0:
                        info = info['entries'][0]
                        await self.play_song(ctx, info['url'], info['title'])
                        await ctx.message.add_reaction('✅')

                else:
                    search_query = f"ytsearch:{link}"
                    info = ydl.extract_info(search_query, download=False)
                    if 'entries' in info and len(info['entries']) > 0:
                        info = info['entries'][0]
                        await self.play_song(ctx, info['url'], info['title'])
                        await ctx.message.add_reaction('✅')
                    else:
                        await ctx.message.add_reaction('❌')

            except Exception as e:
                print(f"Error extracting audio: {e}")
                await ctx.message.add_reaction('❌')
            
async def setup(bot):
    await bot.add_cog(Music(bot))