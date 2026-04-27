import discord
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("TOKEN")
APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================================
# 🚀 READY
# ======================================================

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"🔁 Slash команды: {len(synced)}")
    except Exception as e:
        print("Sync error:", e)

# ======================================================
# 📩 МОДАЛКА ЗАЯВКИ
# ======================================================

class ApplicationModal(discord.ui.Modal, title="📩 Заявка на сервер"):

    nickname = discord.ui.TextInput(label="Ник", required=True)
    age = discord.ui.TextInput(label="Возраст", required=True)
    source = discord.ui.TextInput(label="Откуда узнал", required=True)
    friend = discord.ui.TextInput(label="Ник друга (если есть)", required=False)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):

        channel = interaction.guild.get_channel(APPLICATION_CHANNEL_ID)

        embed = discord.Embed(
            title="📩 Новая заявка",
            color=0xfe8b29
        )

        embed.add_field(name="Ник", value=self.nickname.value, inline=True)
        embed.add_field(name="Возраст", value=self.age.value, inline=True)
        embed.add_field(name="Источник", value=self.source.value, inline=False)
        embed.add_field(name="Друг", value=self.friend.value or "Нет", inline=True)
        embed.add_field(name="О себе", value=self.about.value, inline=False)

        embed.set_footer(text=f"Игрок: {interaction.user}")

        if channel:
            await channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Заявка отправлена!",
            ephemeral=True
        )

# ======================================================
# 🎮 ПАНЕЛЬ
# ======================================================

class MainPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        # 💎 Донат
        self.add_item(discord.ui.Button(
            label="💎 Донат",
            style=discord.ButtonStyle.link,
            url="https://buy.fox-smp.ru"
        ))

        # 🧱 Сборка
        self.add_item(discord.ui.Button(
            label="🧱 Сборка",
            style=discord.ButtonStyle.link,
            url="https://modrinth.com/project/foxsmpmodpack"
        ))

        # 📱 Telegram
        self.add_item(discord.ui.Button(
            label="📱 Telegram",
            style=discord.ButtonStyle.link,
            url="https://t.me/foxsmp_official"
        ))

        # 🟦 VK
        self.add_item(discord.ui.Button(
            label="🟦 VK",
            style=discord.ButtonStyle.link,
            url="https://vk.ru/foxsmp_official"
        ))

        # ▶️ YouTube
        self.add_item(discord.ui.Button(
            label="▶️ YouTube",
            style=discord.ButtonStyle.link,
            url="https://youtube.com/@0_ehorik_0.YouTube"
        ))

        # 🟣 Twitch
        self.add_item(discord.ui.Button(
            label="🟣 Twitch",
            style=discord.ButtonStyle.link,
            url="https://m.twitch.tv/0_ehorik_0_/"
        ))

    # 📩 ЗАЯВКА
    @discord.ui.button(label="📩 Подать заявку", style=discord.ButtonStyle.success)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(ApplicationModal())

    # 📜 ПРАВИЛА
    @discord.ui.button(label="📜 Правила", style=discord.ButtonStyle.primary)
    async def rules(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed1 = discord.Embed(
            title="📜 Правила FOXSMP (1/2)",
            color=0xfe8b29
        )

        embed1.description = (
            "1.1 Маты разрешены\n\n"
            "1.2 Оскорбления — мут/бан\n"
            "1.3 Caps/спам — мут\n"
            "1.4 Реклама — бан\n"
            "1.5 Клевета — мут\n"
            "1.6 Запрещён контент — бан\n"
            "1.7 Попрошайничество — мут\n"
            "1.8 Политика — бан\n\n"
            "2.1 Раздачи разрешены\n"
            "2.2 RMT — бан\n"
            "2.3 Читы — бан\n"
            "2.4 Мошенничество — бан\n"
        )

        embed2 = discord.Embed(
            title="📜 Правила FOXSMP (2/2)",
            color=0xfe8b29
        )

        embed2.description = (
            "2.5 Багоюз — бан\n"
            "2.6 Помехи — бан\n"
            "2.7 Фишинг — бан навсегда\n\n"
            "3. Аккаунты — ответственность владельца\n"
            "3.3 Продажа — бан навсегда\n"
            "3.4 Мультиакки — бан\n\n"
            "4. Администрация имеет право менять правила\n\n"
            "5. Постройки с оскорблениями — снос + бан"
        )

        await interaction.response.send_message(
            embeds=[embed1, embed2],
            ephemeral=True
        )

# ======================================================
# ⚙️ КОМАНДА ПАНЕЛИ
# ======================================================

@bot.tree.command(name="панель", description="Создать панель сервера")
async def panel(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нет прав", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎮 FOXSMP SERVER",
        description=(
            "Добро пожаловать!\n\n"
            "📜 Правила\n"
            "📩 Заявка\n"
            "💎 Донат\n"
            "🧱 Сборка\n"
            "🌐 Соцсети"
        ),
        color=0xfe8b29
    )

    await interaction.channel.send(embed=embed, view=MainPanelView())

    await interaction.response.send_message("✅ Панель создана", ephemeral=True)

# ======================================================
# ▶️ RUN
# ======================================================

bot.run(TOKEN)
