import discord
from discord.ext import commands
import os
import time
from rcon import run_rcon

APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
ACCEPT_ROLE_ID = int(os.getenv("ACCEPT_ROLE_ID", "0"))

# 🧠 хранение заявок и кулдауна
active_applications = set()
cooldowns = {}

COOLDOWN_TIME = 600  # 10 минут

# =========================
# 📩 MODAL
# =========================

class ApplicationModal(discord.ui.Modal, title="📩 Заявка"):

    nickname = discord.ui.TextInput(label="Ник")
    age = discord.ui.TextInput(label="Возраст")
    source = discord.ui.TextInput(label="Откуда узнал")
    friend = discord.ui.TextInput(label="Ник друга", required=False)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        user_id = interaction.user.id
        now = time.time()

        # ⏳ КУЛДАУН
        if user_id in cooldowns and now - cooldowns[user_id] < COOLDOWN_TIME:
            await interaction.response.send_message(
                "⏳ Подожди перед новой заявкой",
                ephemeral=True
            )
            return

        # 🧠 АНТИ-ДУБЛЬ
        if user_id in active_applications:
            await interaction.response.send_message(
                "❌ У тебя уже есть активная заявка",
                ephemeral=True
            )
            return

        active_applications.add(user_id)
        cooldowns[user_id] = now

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

        embed.set_footer(text=str(user_id))

        await channel.send(embed=embed, view=ReviewView())

        await interaction.response.send_message(
            "✅ Заявка отправлена!",
            ephemeral=True
        )

# =========================
# 📩 КНОПКА
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
# 🧑‍💼 REVIEW
# =========================

class ReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.success, custom_id="accept_app")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = interaction.message.embeds[0]
        user_id = int(embed.footer.text)
        member = interaction.guild.get_member(user_id)
        nickname = embed.fields[0].value

        # 🎮 whitelist
        run_rcon(f"whitelist add {nickname}")

        # 🎭 роль
        role = interaction.guild.get_role(ACCEPT_ROLE_ID)
        if role and member:
            await member.add_roles(role)

        # убрать из активных
        active_applications.discard(user_id)

        embed.color = 0x00ff00
        embed.title = "✅ Заявка принята"
        await interaction.message.edit(embed=embed, view=None)

        # 📊 лог
        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(f"✅ Принят: {member} ({nickname})")

        if member:
            try:
                await member.send("🎉 Ты принят на сервер!")
            except:
                pass

        await interaction.response.send_message("✅ Готово", ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger, custom_id="deny_app")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = interaction.message.embeds[0]
        user_id = int(embed.footer.text)
        member = interaction.guild.get_member(user_id)

        active_applications.discard(user_id)

        embed.color = 0xff0000
        embed.title = "❌ Заявка отклонена"
        await interaction.message.edit(embed=embed, view=None)

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(f"❌ Отклонен: {member}")

        if member:
            try:
                await member.send("❌ Тебя не приняли")
            except:
                pass

        await interaction.response.send_message("❌ Готово", ephemeral=True)

# =========================
# ⚙️ COG
# =========================

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="заявка", description="Создать заявку")
    async def app_panel(self, ctx):

        embed = discord.Embed(
            title="📩 Заявка",
            description="Нажми кнопку",
            color=0xfe8b29
        )

        await ctx.send(embed=embed, view=ApplicationView())

    # 🟢 ONLINE
    @commands.hybrid_command(name="online", description="Онлайн Minecraft")
    async def online(self, ctx):

        result = run_rcon("list")

        embed = discord.Embed(title="🟢 Онлайн сервера", color=0x00ff00)

        if result:
            embed.description = f"```{result}```"
        else:
            embed.description = "❌ Сервер недоступен"

        await ctx.send(embed=embed)

# =========================
# 🚀 SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Applications(bot))
    bot.add_view(ApplicationView())
    bot.add_view(ReviewView())
