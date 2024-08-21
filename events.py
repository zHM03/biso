import discord

def setup(bot):
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
