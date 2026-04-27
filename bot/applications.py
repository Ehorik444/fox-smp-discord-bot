import discord
from discord.ext import commands
import os

APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID", "0"))
ACCEPT_ROLE_ID = int(os.getenv("ACCEPT_ROLE_ID", "0"))

# =========================
# MODAL
# =========================

class ApplicationModal(discord.ui.Modal, title="📩 Заявка"):

    nickname = discord.ui.TextInput(label="Ник")
    age = discord.ui.TextInput(label="Возраст")
    source = discord.ui.TextInput(label="Откуда узнал")
    friend = discord.ui.TextInput(label="Ник друга", required=False)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        channel = interaction.guild.get_channel(APPLICATION_CHANNEL_ID)

        embed = discord.Embed(
            title="📩 Новая заявка",
            color=0xfe8b29
        )

        embed.add_field(name="Ник", value=self.nickname.value)
        embed.add_field(name="Возраст", value=self.age.value)
        embed.add_field(name="Источник", value=self.source.value)
        embed.add_field(name="Друг", value=self.friend.value or "Нет")
        embed.add_field(name="О себе", value=self.about.value)

        embed.set_footer(text=str(interaction.user.id))  # 🔥 сохраняем ID

        view = ReviewView()

        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ Заявка отправлена!",
            ephemeral=True
        )

# =========================
# VIEW ПОДАЧИ
# =========================

class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩 Подать заявку",
        style=discord.ButtonStyle.success,
        custom_id="apply_button"
    )
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())

# =========================
# VIEW ПРОВЕРКИ (АДМИНЫ)
# =========================

class ReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Принять",
        style=discord.ButtonStyle.success,
        custom_id="accept_app"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        user_id = int(interaction.message.embeds[0].footer.text)
        member = interaction.guild.get_member(user_id)

        if not member:
            await interaction.response.send_message("❌ Игрок не найден", ephemeral=True)
            return

        role = interaction.guild.get_role(ACCEPT_ROLE_ID)

        if role:
            await member.add_roles(role)

        # меняем embed
        embed = interaction.message.embeds[0]
        embed.color = 0x00ff00
        embed.title = "✅ Заявка принята"

        await interaction.message.edit(embed=embed, view=None)

        try:
            await member.send("🎉 Ваша заявка принята! Добро пожаловать на сервер.")
        except:
            pass

        await interaction.response.send_message("✅ Принято", ephemeral=True)

    @discord.ui.button(
        label="❌ Отклонить",
        style=discord.ButtonStyle.danger,
        custom_id="deny_app"
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):

        user_id = int(interaction.message.embeds[0].footer.text)
        member = interaction.guild.get_member(user_id)

        embed = interaction.message.embeds[0]
        embed.color = 0xff0000
        embed.title = "❌ Заявка отклонена"

        await interaction.message.edit(embed=embed, view=None)

        try:
            await member.send("❌ Ваша заявка отклонена.")
        except:
            pass

        await interaction.response.send_message("❌ Отклонено", ephemeral=True)

# =========================
# COG
# =========================

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="заявка", description="Создать кнопку заявки")
    async def app_panel(self, ctx):

        embed = discord.Embed(
            title="📩 Заявка на сервер",
            description="Нажми кнопку ниже",
            color=0xfe8b29
        )

        await ctx.send(embed=embed, view=ApplicationView())

# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Applications(bot))

    bot.add_view(ApplicationView())
    bot.add_view(ReviewView())
