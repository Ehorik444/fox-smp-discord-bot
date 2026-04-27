import discord
from config import VOICE_CATEGORY_ID

active_channels = {}

async def create_voice(interaction: discord.Interaction):
    guild = interaction.guild

    channel = await guild.create_voice_channel(
        name=f"🔊 {interaction.user.name}",
        category=guild.get_channel(VOICE_CATEGORY_ID)
    )

    active_channels[channel.id] = interaction.user.id

    await interaction.user.move_to(channel)
    await interaction.response.send_message("Создан войс!", ephemeral=True)


async def voice_cleanup(channel: discord.VoiceChannel):
    if len(channel.members) == 0:
        await channel.delete()
        active_channels.pop(channel.id, None)
