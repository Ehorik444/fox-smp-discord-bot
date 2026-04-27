import discord
import uuid
from database import tickets
from config import TICKET_CATEGORY_ID

async def create_ticket(interaction: discord.Interaction, reason: str):
    guild = interaction.guild

    ticket_id = str(uuid.uuid4())[:8]

    channel = await guild.create_text_channel(
        name=f"ticket-{ticket_id}",
        category=guild.get_channel(TICKET_CATEGORY_ID)
    )

    tickets[ticket_id] = {
        "user": interaction.user.id,
        "reason": reason,
        "channel": channel.id
    }

    await channel.send(
        f"🎫 **Новая жалоба**\n"
        f"От: {interaction.user.mention}\n"
        f"Причина: {reason}\n\n"
        f"Реакции: ✅ решить / ❌ закрыть"
    )

    await interaction.response.send_message("Жалоба отправлена!", ephemeral=True)
