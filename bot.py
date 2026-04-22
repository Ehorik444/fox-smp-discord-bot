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


# ---------- RCON ----------
async def whitelist_add(nick):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            return mcr.command(f"whitelist add {nick}")
    except Exception as e:
        return str(e)


# ---------- MODAL ----------
class ApplicationModal(Modal, title="Заявка на сервер"):
    nickname = TextInput(label="Ник Minecraft", max_length=16)
    age = TextInput(label="Возраст", max_length=2)
    about = TextInput(
        label="О себе",
        style=discord.TextStyle.paragraph,
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age_int = int(self.age.value)
        except:
            await interaction.response.send_message(
                "Возраст должен быть числом",
                ephemeral=True
            )
            return

        about_text = self.about.value
        nick = self.nickname.value

        mod_channel = bot.get_channel(MOD_CHANNEL_ID)

        embed = discord.Embed(
            title="📨 Новая заявка",
            color=0x3498db
        )
        embed.add_field(name="Ник", value=nick)
        embed.add_field(name="Возраст", value=age_int)
        embed.add_field(name="О себе", value=about_text[:1024])
        embed.set_footer(text=f"ID: {interaction.user.id}")

        # -------- АВТО-ПРИНЯТИЕ --------
        if age_int >= 14 and len(about_text) >= 32:
            result = await whitelist_add(nick)

            embed.color = 0x00ff00
            embed.add_field(name="Авто-принят", value="Да", inline=False)
            embed.add_field(name="RCON", value=result, inline=False)

            await mod_channel.send(embed=embed)

            await interaction.response.send_message(
                "✅ Ты автоматически принят!",
                ephemeral=True
            )
        else:
            view = ApplicationView(nick)

            await mod_channel.send(embed=embed, view=view)

            await interaction.response.send_message(
                "📨 Заявка отправлена на рассмотрение",
                ephemeral=True
            )


# ---------- КНОПКИ МОДЕРАЦИИ ----------
class ApplicationView(View):
    def __init__(self, nickname):
        super().__init__(timeout=None)
        self.nickname = nickname

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: Button):
        result = await whitelist_add(self.nickname)

        embed = interaction.message.embeds[0]
        embed.color = 0x00ff00
        embed.add_field(name="Статус", value="Принят", inline=False)

        await interaction.message.edit(embed=embed, view=None)

        await interaction.response.send_message(
            f"Игрок {self.nickname} добавлен\n{result}",
            ephemeral=True
        )

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: Button):
        embed = interaction.message.embeds[0]
        embed.color = 0xff0000
        embed.add_field(name="Статус", value="Отклонён", inline=False)

        await interaction.message.edit(embed=embed, view=None)

        await interaction.response.send_message(
            "Заявка отклонена",
            ephemeral=True
        )


# ---------- КНОПКА ПОДАЧИ ----------
class ApplyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 Подать заявку", style=discord.ButtonStyle.blurple)
    async def apply(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ApplicationModal())


# ---------- КОМАНДА SETUP ----------
@tree.command(name="mcsetup", description="Создать кнопку подачи заявки")
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 Заявка на сервер",
        description="Нажми кнопку ниже, чтобы подать заявку",
        color=0x2ecc71
    )

    await interaction.channel.send(embed=embed, view=ApplyButtonView())
    await interaction.response.send_message(
        "Готово",
        ephemeral=True
    )


# ---------- READY ----------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен как {bot.user}")


bot.run(TOKEN)
