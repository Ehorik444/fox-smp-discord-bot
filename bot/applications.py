import discord
from discord.ext import commands
from discord import app_commands
import os

APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID"))

# =========================
# MODAL
# =========================

class ApplyModal(discord.ui.Modal, title="📩 Заявка на сервер"):

    nick = discord.ui.TextInput(label="Ваш ник", required=True)
    age = discord.ui.TextInput(label="Возраст", required=True)
    source = discord.ui.TextInput(label="Откуда узнали?", required=True)
    friend = discord.ui.TextInput(label="Ник друга", required=False)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.long, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(APPLICATION_CHANNEL_ID)

        if not channel:
            await interaction.response.send_message("❌ Канал заявок не найден", ephemeral=True)
            return

        embed = discord.Embed(
            title="📩 Новая заявка",
            color=0xfe8b29
        )
        embed.add_field(name="👤 Ник", value=self.nick.value, inline=False)
        embed.add_field(name="🎂 Возраст", value=self.age.value, inline=False)
        embed.add_field(name="📢 Откуда узнал", value=self.source.value, inline=False)
        embed.add_field(name="👥 Друг", value=self.friend.value or "Нет", inline=False)
        embed.add_field(name="📝 О себе", value=self.about.value, inline=False)
        embed.set_footer(text=f"ID: {interaction.user.id}")

        await channel.send(embed=embed, view=AcceptView())

        await interaction.response.send_message("✅ Заявка отправлена!", ephemeral=True)

# =========================
# BUTTON VIEW (ПОДАТЬ)
# =========================

class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # ВАЖНО!

    @discord.ui.button(
        label="📩 Подать заявку",
        style=discord.ButtonStyle.primary,
        custom_id="apply_button"  # ВАЖНО!
    )
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())

# =========================
# ACCEPT / DECLINE
# =========================

class AcceptView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # ВАЖНО!

    @discord.ui.button(
        label="✅ Принять",
        style=discord.ButtonStyle.success,
        custom_id="accept_button"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        member_id = int(interaction.message.embeds[0].footer.text.replace("ID: ", ""))
        member = interaction.guild.get_member(member_id)

        if member:
            role = discord.utils.get(interaction.guild.roles, name="Игрок")
            if role:
                await member.add_roles(role)

        await interaction.response.send_message("✅ Заявка принята", ephemeral=True)

    @discord.ui.button(
        label="❌ Отклонить",
        style=discord.ButtonStyle.danger,
        custom_id="decline_button"
    )
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Заявка отклонена", ephemeral=True)

# =========================
# COMMAND
# =========================

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="заявка", description="Создать сообщение с заявкой")
    async def create_apply(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📩 Заявка на сервер",
            description="Нажми кнопку ниже чтобы подать заявку",
            color=0xfe8b29
        )

        await interaction.channel.send(embed=embed, view=ApplyView())
        await interaction.response.send_message("✅ Сообщение создано", ephemeral=True)

# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Applications(bot))

    # РЕГИСТРАЦИЯ persistent views (ВАЖНО)
    bot.add_view(ApplyView())
    bot.add_view(AcceptView())
