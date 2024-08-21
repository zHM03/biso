import discord
from discord.ext import commands

def setup(bot):
    @bot.command()
    async def biso(ctx):
        """Botun yanıt süresini gösterir."""
        await ctx.send('Meow!')

    @bot.command()
    @commands.has_permissions(kick_members=True)
    async def uçur(ctx, member: discord.Member, *, reason=None):
        """Etiketlenen kişiyi sunucudan atar."""
        if ctx.author == member:
            await ctx.send("Bunu benden yapmamı isteme!")
            return

        bot_role = ctx.guild.get_member(bot.user.id).top_role

        if bot_role.position <= member.top_role.position:
            await ctx.send("Sen kimsin lan!")
            return

        try:
            await ctx.send("Patimi yalıyorum bi saniye...")
            await ctx.send(f"{member} Götüne tekmeyi vurdum, UÇURDUM!! fiyuuu ㅇㅅㅇ")
            await member.kick(reason=reason)
        except discord.Forbidden:
            await ctx.send("Üşendim.")
        except discord.HTTPException as e:
            await ctx.send(f"Başaramdık usta, sağlam çıktı: {e}")
