import discord
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("TOKEN")  # обязательно задай в env

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
        print(f"🔁 Slash команды синхронизированы: {len(synced)}")
    except Exception as e:
        print("Sync error:", e)

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

    # 📜 ПРАВИЛА
    @discord.ui.button(label="📜 Правила", style=discord.ButtonStyle.primary)
    async def rules(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed1 = discord.Embed(
            title="📜 Правила сервера FOXSMP (1/2)",
            color=0xfe8b29
        )

        embed1.description = (
            "**1. Общение**\n\n"
            "1.1 Маты разрешены.\n\n"
            "1.2.1 Оскорбления — мут 30м–5ч\n"
            "1.2.2 Родственники — бан 3 дня\n\n"
            "1.3.1 Caps — мут 10м\n"
            "1.3.2 Спам — мут 30м\n\n"
            "1.4 Реклама — мут/бан\n"
            "1.5 Клевета — мут 1д\n"
            "1.6 Запрещён контент — бан\n"
            "1.7 Попрошайничество — мут\n"
            "1.8 Политика — бан\n\n"
            "**2. Игра**\n\n"
            "2.1 Раздачи — можно\n"
            "2.2 RMT — бан 5д\n"
            "2.3 Читы — бан до навсегда\n"
            "2.4 Мошенничество — бан\n"
            "2.5 Багоюз — бан\n"
        )

        embed2 = discord.Embed(
            title="📜 Правила сервера FOXSMP (2/2)",
            color=0xfe8b29
        )

        embed2.description = (
            "2.6 Помехи — бан\n"
            "2.7 Фишинг — бан навсегда\n"
            "2.8 Командный флуд — бан\n"
            "2.9 Провокации — мут\n"
            "2.10 Выдача за админа — мут\n\n"
            "**3. Аккаунт**\n"
            "3.1 Ответственность на владельце\n"
            "3.2 Ники/скины — запрещены\n"
            "3.3 Продажа — бан\n"
            "3.4 Мультиакки — бан\n\n"
            "**4. Администрация**\n"
            "Имеет право менять правила\n\n"
            "**5. Постройки**\n"
            "Запрещённые — снос + бан"
        )

        await interaction.response.send_message(
            embeds=[embed1, embed2],
            ephemeral=True
        )

# ======================================================
# ⚙️ КОМАНДА СОЗДАНИЯ ПАНЕЛИ
# ======================================================

@bot.tree.command(name="панель", description="Создать главную панель")
async def panel(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нет прав", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎮 FOXSMP",
        description=(
            "Добро пожаловать на сервер!\n\n"
            "📜 Ознакомьтесь с правилами\n"
            "🧱 Скачайте сборку\n"
            "💎 Поддержите проект\n"
            "🌐 Подпишитесь на соцсети"
        ),
        color=0xfe8b29
    )

    await interaction.channel.send(embed=embed, view=MainPanelView())

    await interaction.response.send_message("✅ Панель создана", ephemeral=True)

# ======================================================
# ▶️ ЗАПУСК
# ======================================================

bot.run(TOKEN)
