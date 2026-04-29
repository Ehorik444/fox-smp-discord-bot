import discord
from discord import app_commands
from db import create_application, update_status
from config import APPLICATION_LOG_CHANNEL
from utils import check_cooldown, check_daily_limit


class ApplyView(discord.ui.View):
    def __init__(self, app_id: int):
        super().__init__(timeout=None)
        self.app_id = app_id

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await update_status(self.app_id, "accepted")
        await interaction.response.send_message("Заявка принята", ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await update_status(self.app_id, "rejected")
        await interaction.response.send_message("Заявка отклонена", ephemeral=True)


class Applications(app_commands.Group):

    def __init__(self):
        super().__init__(name="apply", description="Система заявок")

    @app_commands.command(name="send", description="Отправить заявку")
    async def send(self, interaction: discord.Interaction, text: str):

        user_id = interaction.user.id

        if not check_cooldown(user_id):
            return await interaction.response.send_message(
                "⏳ Кулдаун 60 секунд", ephemeral=True
            )

        if not check_daily_limit(user_id):
            return await interaction.response.send_message(
                "🚫 Лимит 1 заявка в день", ephemeral=True
            )

        await create_application(user_id, text)

        channel = interaction.client.get_channel(APPLICATION_LOG_CHANNEL)

        embed = discord.Embed(
            title="Новая заявка",
            description=text,
            color=0x00ff00,
        )

        msg = await channel.send(embed=embed)
        await msg.edit(view=ApplyView(msg.id))

        await interaction.response.send_message("✅ Заявка отправлена", ephemeral=True)


async def setup(bot):
    bot.tree.add_command(Applications())
