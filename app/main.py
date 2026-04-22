import os
import discord
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
from dotenv import load_dotenv
from mcrcon import MCRcon

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
MOD_CHANNEL_ID = int(os.getenv("MOD_CHANNEL_ID"))

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


# ---------------- RCON ----------------
async def whitelist_add(nick: str):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            return mcr.command(f"whitelist add {nick}")
    except Exception as e:
        return f"RCON ERROR: {e}"


# ---------------- MODAL ----------------
class ApplicationModal(Modal, title="Заявка на сервер"):
    nickname = TextInput(label="Ник Minecraft", max_length=16)
    age = TextInput(label="Возраст", max_length=2)
    about = TextInput(label="О себе", style=discord.TextStyle.paragraph, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age_int = int(self.age.value)
        except:
            await interaction.response.send_message("Возраст должен быть числом", ephemeral=True)
            return

        nick = self.nickname.value
        about_text = self.about.value

        mod_channel = bot.get_channel(MOD_CHANNEL_ID)

        embed = discord.Embed(title="📨 Новая заявка", color=0x3498db)
        embed.add_field(name="Ник", value=nick, inline=False)
        embed.add_field(name="Возраст", value=age_int, inline=False)
        embed.add_field(name="О себе", value=about_text[:1024], inline=False)

        # AUTO ACCEPT
        if age_int >= 14 and len(about_text) >= 32:
            result = await whitelist_add(nick)

            embed.color = 0x00ff00
            embed.add_field(name="Статус", value="Авто-принят", inline=False)
            embed.add_field(name="RCON", value=result, inline=False)

            await mod_channel.send(embed=embed)
            await interaction.response.send_message("✅ Ты автоматически принят!", ephemeral=True)
        else:
            await mod_channel.send(embed=embed, view=ApplicationView(nick))
            await interaction.response.send_message("📨 Заявка отправлена", ephemeral=True)


# ---------------- MODERATION VIEW ----------------
class ApplicationView(View):
    def __init__(self, nickname: str):
        super().__init__(timeout=None)
        self.nickname = nickname

    @discord.ui.button(
        label="✅ Принять",
        style=discord.ButtonStyle.green,
        custom_id="accept_btn"
    )
    async def accept(self, interaction: discord.Interaction, button: Button):

        result = await whitelist_add(self.nickname)

        embed = interaction.message.embeds[0]
        embed.color = 0x00ff00
        embed.add_field(name="Статус", value="Принят", inline=False)
        embed.add_field(name="RCON", value=result, inline=False)

        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("Принято", ephemeral=True)

    @discord.ui.button(
        label="❌ Отклонить",
        style=discord.ButtonStyle.red,
        custom_id="deny_btn"
    )
    async def deny(self, interaction: discord.Interaction, button: Button):

        embed = interaction.message.embeds[0]
        embed.color = 0xff0000
        embed.add_field(name="Статус", value="Отклонён", inline=False)

        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("Отклонено", ephemeral=True)


# ---------------- APPLY BUTTON ----------------
class ApplyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📋 Подать заявку",
        style=discord.ButtonStyle.blurple,
        custom_id="apply_btn"
    )
    async def apply(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ApplicationModal())


# ---------------- SETUP COMMAND ----------------
@tree.command(name="setup", description="Создать систему заявок")
async def setup(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎮 Заявка на сервер",
        description="Нажми кнопку ниже, чтобы подать заявку",
        color=0x2ecc71
    )

    await interaction.channel.send(embed=embed, view=ApplyButtonView())
    await interaction.response.send_message("Готово", ephemeral=True)


# ---------------- READY ----------------
@bot.event
async def on_ready():

    # persistent views (БЕЗ ОШИБКИ)
    bot.add_view(ApplyButtonView())
    bot.add_view(ApplicationView("temp"))

    await tree.sync()
    print(f"Logged in as {bot.user}")


# ---------------- RUN ----------------
bot.run(TOKEN)
