import discord
from discord import app_commands
from discord.ext import commands
from db import db
import os
from datetime import datetime, timedelta

LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))


# ---------- BUTTONS ----------

class AppView(discord.ui.View):
    def __init__(self, app_id: int):
        super().__init__(timeout=None)
        self.app_id = app_id

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.update_status(self.app_id, "accepted")

        await interaction.response.send_message("✅ Принято", ephemeral=True)

        channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(f"✅ Заявка #{self.app_id} принята {interaction.user.mention}")

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.update_status(self.app_id, "rejected")

        await interaction.response.send_message("❌ Отклонено", ephemeral=True)

        channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(f"❌ Заявка #{self.app_id} отклонена {interaction.user.mention}")


# ---------- COG ----------

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="apply", description="Подать заявку")
    async def apply(self, interaction: discord.Interaction):

        # 🔒 анти-спам (1 заявка в день)
        last = await db.get_last_application(interaction.user.id, interaction.guild.id)

        if last:
            if last["created_at"] + timedelta(days=1) > datetime.utcnow():
                return await interaction.response.send_message(
                    "⛔ Можно только 1 заявку в день",
                    ephemeral=True
                )

        app_id = await db.create_application(
            interaction.user.id,
            interaction.guild.id
        )

        view = AppView(app_id)

        await interaction.response.send_message(
            f"📩 Заявка #{app_id} отправлена",
            ephemeral=True
        )

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(
                f"📩 Новая заявка #{app_id} от {interaction.user.mention}",
                view=view
            )


async def setup(bot):
    await bot.add_cog(Applications(bot))
