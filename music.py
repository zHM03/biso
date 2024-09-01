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
            'channel_id': ctx.channel.id
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

            # Kuyruğun ilk şarkısını seç
            song = self.queue[0]

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
                await asyncio.sleep(5)
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
            table = Image.new('RGBA', (table_width, table_height), (0, 0, 0, 150))
            draw_table = ImageDraw.Draw(table)
            shadow_offset = 2
            shadow_color = (0, 0, 0, 128)
            draw_table.text((10 + shadow_offset, 10 + shadow_offset), song_text, font=song_font, fill=shadow_color)
            draw_table.text((10, 10), song_text, font=song_font, fill=(255, 255, 255))

            # Tabloyu arka plana ekle
            background.paste(table, (table_x, table_y), table)

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

            # Komut butonları ekle
            self.add_item(Button(label="Geç", style=discord.ButtonStyle.danger, custom_id="skip"))
            self.add_item(Button(label="Duraklat", style=discord.ButtonStyle.secondary, custom_id="pause"))
            self.add_item(Button(label="Devam Et", style=discord.ButtonStyle.success, custom_id="resume"))
            self.add_item(Button(label="Durdur", style=discord.ButtonStyle.danger, custom_id="stop"))
            self.add_item(Button(label="Temizle", style=discord.ButtonStyle.secondary, custom_id="clear"))

        async def prev_page(self, interaction: discord.Interaction):
            if self.page > 1:
                self.page -= 1
                await self.update_message(interaction)

        async def next_page(self, interaction: discord.Interaction):
            if self.page < self.num_pages:
                self.page += 1
                await self.update_message(interaction)

        async def update_message(self, interaction: discord.Interaction):
            await self.message.delete()
            await self.bot.get_cog("Music").send_queue(interaction.channel, page=self.page)

        async def on_timeout(self):
            await self.message.delete()

    @commands.command()
    async def add(self, ctx, *, url):
        """Kuyruğa şarkı ekler"""
        try:
            ydl_opts = self.ytdl_opts.copy()
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = info['formats'][0]['url']
                title = info.get('title', 'No Title')
                await self.play_song(ctx, url2, title)
                await ctx.send(f"{title} kuyruğa eklendi.")
        except Exception as e:
            await ctx.send(f"Bir hata oluştu: {str(e)}")

    @commands.command()
    async def queue(self, ctx):
        """Kuyruğu gösterir"""
        await self.send_queue(ctx)

    @commands.command()
    async def skip(self, ctx):
        """Şarkıyı geçer"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await self.play_next()
            await ctx.send("Şarkı geçildi.")
        else:
            await ctx.send("Şu anda çalan bir şarkı yok.")

    @commands.command()
    async def stop(self, ctx):
        """Botu durdurur ve kanaldan ayrılır"""
        if self.voice_client:
            self.queue.clear()
            self.user_queue.clear()
            if self.voice_client.is_playing():
                self.voice_client.stop()
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send("Bot durduruldu ve kanaldan ayrıldı.")
        else:
            await ctx.send("Bot şu anda bir sesli kanalda değil.")

    @commands.command()
    async def pause(self, ctx):
        """Çalmayı duraklatır"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("Şarkı duraklatıldı.")
        else:
            await ctx.send("Şu anda çalan bir şarkı yok.")

    @commands.command()
    async def resume(self, ctx):
        """Çalmayı devam ettirir"""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("Şarkı devam ettirildi.")
        else:
            await ctx.send("Şarkı devam ettirilemiyor.")

    @commands.command()
    async def clear(self, ctx):
        """Kuyruğu temizler"""
        self.queue.clear()
        self.user_queue.clear()
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
        await ctx.send("Kuyruk temizlendi.")

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Bot olarak giriş yapıldı: {bot.user.name}')

bot.add_cog(Music(bot))
bot.run(os.getenv('DISCORD_TOKEN'))
