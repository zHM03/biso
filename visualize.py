import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

class Visualize(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def show_queue(self, ctx, queue):
        embed = discord.Embed(title="🎵 **Şarkı Kuyruğu** 🎵", color=0x1DB954)
        embed.set_image(url="https://getwallpapers.com/wallpaper/full/6/f/3/1300907-chopper-wallpaper-for-computer-1920x1200-for-full-hd.jpg")

        for i, item in enumerate(queue):
            search_query = item['search_query']
            with YoutubeDL({'quiet': True, 'extractaudio': True, 'audioformat': 'mp3'}) as ydl:
                try:
                    info = ydl.extract_info(search_query, download=False)['entries'][0]
                    duration = info.get('duration', 'Bilinmiyor')
                    duration_formatted = f"{duration // 60}:{duration % 60:02d}" if duration != 'Bilinmiyor' else 'Bilinmiyor'
                    url = info.get('webpage_url', 'Link Bulunamadı')  # YouTube linkini alıyoruz
                except Exception as e:
                    print(f"Error retrieving duration: {e}")
                    duration_formatted = 'Bilinmiyor'
                    url = 'Link Bulunamadı'
            
            # Daha büyük ve belirgin öğeler için emoji ve kalın yazı
            embed.add_field(
                name=f"🎵 **Şarkı {i + 1}:**", 
                value=f"**{item['title']}**\nSüre: {duration_formatted} ⏳\n[YouTube Linki]({url})", 
                inline=False
            )

        embed.set_footer(text="Liste büyüdü! Daha fazlası yakında... 🎧")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Visualize(bot))
