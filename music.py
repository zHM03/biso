import discord
from discord.ext import commands
from discord.ui import View, Button
from yt_dlp import YoutubeDL
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import io
from PIL import Image, ImageDraw, ImageFont
import asyncio

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
))

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.queue = []  # Kodun yönettiği ana kuyruk
        self.user_queue = []  # Kullanıcının gördüğü kuyruk
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

    async def play_song(self, ctx, audio_url, song_title):
        """Şarkıyı hem kod kuyruğuna hem de kullanıcı kuyruğuna ekler ve çalmaya başlar"""
        song = {
            'url': audio_url,
            'title': song_title,
            'channel_id': ctx.channel.id,
            'status': 'pending'  # Başlangıç durumu
        }
        # Şarkıyı hem kod kuyruğuna hem de kullanıcı kuyruğuna ekle
        self.queue.append(song)
        self.user_queue.append(song)
        await self.send_queue(ctx)  # Kullanıcı kuyruğunu güncelle

        if not self.is_playing:
            if not self.voice_client or not self.voice_client.is_connected():
                self.voice_client = await ctx.author.voice.channel.connect()
            await self.play_next()

    async def play_next(self):
        """Bir sonraki şarkıyı çal"""
        if len(self.queue) > 0:  # Kod kuyrukta şarkı varsa
            self.is_playing = True  # Oynatma durumunu aktif olarak ayarla
            song = self.queue[0] # Kuyruğun ilk şarkısını seç
            song['status'] = 'playing'  # Şarkı çalmaya başladı
            self.currently_playing = song

            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }

            try:
                # Ses dosyasını oynat
                self.voice_client.play(discord.FFmpegPCMAudio(song['url'], **ffmpeg_options), after=lambda e: self.bot.loop.create_task(self.play_next()))
                # Kod kuyruğundan şarkıyı geçici olarak kaldır
                self.queue.pop(0)
            except Exception as e:  # Hata durumunda çalışacak blok
                print(f'Error: {str(e)}')
                self.is_playing = False
                await self.play_next()
        else:
            self.is_playing = False  # Kuyruk boşsa oynatmayı durdur
            if self.voice_client and self.voice_client.is_connected():
                # Şarkı bitiminden sonra 5 saniye bekle
                await asyncio.sleep(1)
                # Kuyruk hala boşsa ve sesli kanalda kimse yoksa ayrıl
                if len(self.queue) == 0 and not self.voice_client.is_playing():
                    await self.voice_client.disconnect()
                    self.user_queue.clear()  # Kullanıcı kuyruğunu temizle

    async def send_queue(self, ctx, page=1):
        """Kullanıcının kuyruğunu görsel olarak gönderir"""
        num_pages = (len(self.user_queue) + self.items_per_page - 1) // self.items_per_page

        background_path = os.getenv('BACKGROUND_IMAGE_PATH', 'assets/chopper.jpg')
        background = Image.open(background_path).convert('RGBA')
        img_width, img_height = background.size

        base_width = 800
        width_percent = base_width / float(img_width)
        height_size = int(float(img_height) * width_percent)
        background = background.resize((base_width, height_size), Image.LANCZOS)

        overlay = Image.new('RGBA', background.size, (0, 0, 0, 150))
        background = Image.alpha_composite(background, overlay)

        try:
            title_font = ImageFont.truetype("assets/pirata.ttf", 50)
            song_font = ImageFont.truetype("assets/pirata.ttf", 30)
        except IOError:
            title_font = ImageFont.load_default()
            song_font = ImageFont.load_default()

        draw = ImageDraw.Draw(background)

        songs_text = "SONGS\n"
        text_bbox = draw.textbbox((0, 0), songs_text, font=title_font)
        songs_text_width = text_bbox[2] - text_bbox[0]
        songs_text_height = text_bbox[3] - text_bbox[1]
        songs_text_x = (background.width - songs_text_width) // 2
        songs_text_y = 10  # Yukarıdan 10 piksel aşağıda
        draw.text((songs_text_x, songs_text_y), songs_text, font=title_font, fill=(255, 255, 255))

        start_index = (page - 1) * self.items_per_page
        end_index = min(start_index + self.items_per_page, len(self.user_queue))

        current_y = songs_text_y + songs_text_height + 60

        for index, song in enumerate(self.user_queue[start_index:end_index]):
            status_image = "pending.png"  # Varsayılan durum resmi
            if song['status'] == 'playing':
                status_image = "playing.png"
            elif song['status'] == 'completed':
                status_image = "completed.png"
                
            status_img = Image.open(f"assets/{status_image}").convert("RGBA")
            song_text = f"{start_index + index + 1}. {song['title']}"

            # Metin boyutunu hesapla
            text_bbox = draw.textbbox((0, 0), song_text, font=song_font)
            song_text_width = text_bbox[2] - text_bbox[0]
            song_text_height = text_bbox[3] - text_bbox[1]
            table_width = song_text_width + 40
            table_height = song_text_height + 20
            table_x = 20
            table_y = current_y

            # Şeffaf tabloyu oluştur
            table = Image.new('RGBA', (table_width + emoji_size[0] + 10, table_height), (0, 0, 0, 150))
            draw_table = ImageDraw.Draw(table)
            shadow_offset = 2
            shadow_color = (0, 0, 0, 128)
            draw_table.text((10 + shadow_offset, 10 + shadow_offset), song_text, font=song_font, fill=shadow_color)
            draw_table.text((10, 10), song_text, font=song_font, fill=(255, 255, 255))

            # Tabloyu arka plana ekle
            background.paste(table, (table_x + 40, table_y), table)
            background.paste(status_img, (table_x, table_y), status_img)

            current_y += table_height + 10

        buffer = io.BytesIO()
        background.save(buffer, format='PNG', optimize=True, quality=30)
        buffer.seek(0)

        if self.last_message:
            try:
                await self.last_message.delete()
            except discord.NotFound:
                pass

        new_message = await ctx.send(file=discord.File(fp=buffer, filename='queue.png'))

        self.last_message = new_message

        # Butonları oluştur ve görseli gönder
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

            self.prev_button = Button(label="Önceki Sayfa", style=discord.ButtonStyle.primary, disabled=(self.page == 1))
            self.next_button = Button(label="Sonraki Sayfa", style=discord.ButtonStyle.primary, disabled=(self.page == self.num_pages))

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

                elif "spotify.com/playlist" in link:
                    playlist_id = link.split('/')[-1].split('?')[0]
                    playlist_info = sp.playlist(playlist_id)
                    tracks_count = len(playlist_info['tracks']['items'])
                    success_count = 0
                    for item in playlist_info['tracks']['items']:
                        track = item['track']
                        track_name = track['name']
                        artist_name = track['artists'][0]['name']
                        search_query = f"{track_name} {artist_name}"
                        search_query = f"ytsearch:{search_query}"
                        info = ydl.extract_info(search_query, download=False)
                        if 'entries' in info and len(info['entries']) > 0:
                            info = info['entries'][0]
                        await self.play_song(ctx, info['url'], info['title'])
                        success_count += 1
                    if  success_count == tracks_count:
                        await ctx.message.add_reaction("✅")
                    else:
                        await ctx.message.add_reaction("❌")

                

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

    @commands.command()
    async def n(self, ctx):
        """Çalınan şarkıyı atlar"""
        if self.voice_client and self.voice_client.is_playing():
            if ctx.author.voice and ctx.author.voice.channel == self.voice_client.channel:
                # Eğer kuyruk boşsa
                if len(self.queue) == 0:
                    await ctx.send("Şarkılar bitti be geç geç geç nereye kadar!.")
                    await ctx.message.add_reaction("❌")
                else:
                    self.voice_client.stop()
                    await ctx.message.add_reaction('✅')
            else:
                await ctx.send("Sen ne karışıyon!.")
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send("Neyi geçeyim gardeş neyiii?!?!.")
            await ctx.message.add_reaction("❌")

    @commands.command()
    async def s(self, ctx):
        """Şarkıyı duraklatır"""
        if self.voice_client and self.voice_client.is_playing():
            if ctx.author.voice and ctx.author.voice.channel == self.voice_client.channel:
                self.voice_client.pause()
                await ctx.message.add_reaction('✅')
            else:
                await ctx.send("Karışma yav.")
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send("Sor bakayım şarkı var mı.")
            await ctx.message.add_reaction("❌")

    @commands.command()
    async def r(self, ctx):
        """Şarkıyı devam ettirir"""
        if self.voice_client and self.voice_client.is_paused():
            if ctx.author.voice and ctx.author.voice.channel == self.voice_client.channel:
                self.voice_client.resume()
                await ctx.message.add_reaction('✅')
            else:
                await ctx.send("Çok mu istiyon.")
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send("Neyi devam edeyim neyiii?!?!.")
            await ctx.message.add_reaction("❌")

    @commands.command()
    async def l(self, ctx):
        """Botu sesli kanaldan çıkarır"""
        if self.voice_client and self.voice_client.is_connected():
            if ctx.author.voice and ctx.author.voice.channel == self.voice_client.channel:
                await ctx.send("Allah'a emanet.")
                await ctx.message.add_reaction('✅')
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                await self.voice_client.disconnect()
                self.queue.clear()
                self.user_queue.clear()
                self.is_playing = False
            else:
                await ctx.send("Yiyosa gel!.")
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send("yokum ki.")
            await ctx.message.add_reaction("❌")

    @commands.command()
    async def d(self, ctx, index: int):
        """Kuyruktaki belirli bir sıradaki şarkıyı siler"""
        if 1 <= index <= len(self.user_queue):
            if ctx.author.voice and ctx.author.voice.channel == self.voice_client.channel:
                song_to_remove = self.user_queue.pop(index - 1)  # Kuyruktaki şarkıyı kaldır
                for i, song in enumerate(self.queue):  # Kod kuyruğundaki şarkıyı da kaldır (eğer varsa)
                    if song['url'] == song_to_remove['url']:
                        self.queue.pop(i)
                        break
                await ctx.send(f"{index}. sıradaki şarkı kuyruktan kaldırıldı.")
                await self.send_queue(ctx)  # Kuyruk güncellenmiş haliyle yeniden gönderilir
                await ctx.message.add_reaction('✅')
            else:
                await ctx.send("Tanıyamadım, kimdiniz")
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send(f"Kuyrukta {index}. numaralı şarkı yog.")
            await ctx.message.add_reaction("❌")
            
async def setup(bot):
    await bot.add_cog(Music(bot))
