import asyncio
from discord.ext import commands

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.user_queue = []
        self.search_task = None  # Arama görevini yönetmek için
        self.is_playing = False  # Şu anda şarkı çalınıyor mu?

    @commands.command(name='n')
    async def next_song(self, ctx):
        """Kuyruktaki bir sonraki şarkıya geçer."""
        voice_client = ctx.guild.voice_client  # Sesli kanalda mıyız kontrol et
        if not voice_client or not voice_client.is_playing():
            await ctx.send("Şu anda hiçbir şarkı çalmıyor.")
            return

        if len(self.queue) == 0:
            await ctx.send("Kuyrukta oynatılacak başka şarkı yok. Mevcut şarkı çalınıyor.")
            return

        # Mevcut şarkıyı 'completed' olarak işaretle ve kuyruğun ilk şarkısını çıkar
        current_song = self.queue.pop(0)
        current_song['status'] = 'completed'

        # Kuyrukta şarkı varsa bir sonraki şarkıyı çal
        if len(self.queue) > 0:
            next_song = self.queue[0]
            next_song['status'] = 'playing'
            await self.send_queue(ctx)  # Kuyruğun son halini gönder
            if voice_client.is_playing():
                voice_client.stop()  # Mevcut şarkıyı durdur
            await self.play_next()  # Bir sonraki şarkıyı çal
        else:
            await ctx.send("Kuyrukta daha fazla şarkı kalmadı.")
            # Kuyruk boşsa sesli kanaldan ayrılabilir veya başka işlemler yapılabilir


    @commands.command(name='s')
    async def pause_song(self, ctx):
        """Şarkıyı duraklatır"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            if ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel:
                ctx.voice_client.pause()
                await ctx.message.add_reaction('✅')
            else:
                await ctx.send("Karışma yav.")
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send("Sor bakayım şarkı var mı.")
            await ctx.message.add_reaction("❌")

    @commands.command(name='r')
    async def resume_song(self, ctx):
        """Şarkıyı devam ettirir"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            if ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel:
                ctx.voice_client.resume()
                await ctx.message.add_reaction('✅')
            else:
                await ctx.send("Çok mu istiyon.")
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send("Neyi devam edeyim neyiii?!?!.")
            await ctx.message.add_reaction("❌")

    @commands.command()
    async def l(self, ctx):
        """Botu sesli kanaldan çıkarır (sadece arama işlemi tamamlandığında)"""
        # Arama işlemini bekle
        if self.search_task and not self.search_task.done():
            await ctx.send("Arama işlemleri devam ettiği için şu anda sesli kanaldan ayrılamam. Arama işlemi bitene kadar bekleyeceğim.")
            await ctx.message.add_reaction("❌")
            return

        # Sesli kanaldan ayrılma işlemi
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_connected():
            await ctx.send("Allah'a emanet.")
            await ctx.message.add_reaction('✅')

            if self.is_playing:
                voice_client.stop()

            # Önce arama görevini iptal et
            if self.search_task:
                self.search_task.cancel()
                try:
                    await self.search_task
                except asyncio.CancelledError:
                    # Görev iptal edildi
                    pass
            
            # Sonrasında kanaldan ayrıl
            await voice_client.disconnect()
            self.queue.clear()  # Kuyruğu temizle
            self.user_queue.clear()  # Kullanıcı kuyruğunu temizle
            self.is_playing = False  # Çalma durumunu güncelle
            self.search_task = None  # Arama görevini sıfırla
        else:
            await ctx.send("Yokum ki.")
            await ctx.message.add_reaction("❌")



    @commands.command(name='d')
    async def delete_song(self, ctx, index: int):
        """Kuyruktaki belirli bir sıradaki şarkıyı siler"""
        if 1 <= index <= len(self.user_queue):
            if ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel:
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
    await bot.add_cog(MusicCommands(bot))
