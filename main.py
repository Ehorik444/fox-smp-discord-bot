import discord
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
from mcrcon import MCRcon
from openai import OpenAI

# =======================
# ВСТАВЬ СЮДА ДАННЫЕ
# =======================

DISCORD_TOKEN = "MTIyMDQ0MjA5ODA4MDE1MzY5Mg.GZh0Wn.G4zd3ZdXYwWZp6wlVR38ulrXHpjkg98uIqnF3Y"
OPENAI_API_KEY = "ТВОЙ_OPENAI_KEY"

RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = "password"

SERVER_IP = "play.server.net"

# =======================

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# -------- AI проверка --------
def check_application(data: str):
    prompt = f"""
Ты модератор Minecraft сервера.

Ответь строго:
ACCEPT или REJECT
Причина: ...

Заявка:
{data}
"""

    response = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content

    if "ACCEPT" in text:
        return True, text
    return False, text


# -------- Форма --------
class ApplyModal(Modal, title="Заявка"):
    nick = TextInput(label="Ник Minecraft")
    age = TextInput(label="Возраст")
    source = TextInput(label="Откуда узнали?")
    inviter = TextInput(label="Кто пригласил?")
    about = TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        data = f"""
Ник: {self.nick}
Возраст: {self.age}
Источник: {self.source}
Пригласил: {self.inviter}
О себе: {self.about}
"""

        await interaction.response.send_message("⏳ Проверяем заявку...", ephemeral=True)

        accepted, reason = check_application(data)

        if accepted:
            try:
                with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                    mcr.command(f"whitelist add {self.nick}")
            except Exception as e:
                print("RCON ERROR:", e)

            role_new = discord.utils.get(interaction.guild.roles, name="Игрок")
            role_old = discord.utils.get(interaction.guild.roles, name="Новичок")

            if role_new:
                await interaction.user.add_roles(role_new)
            if role_old:
                await interaction.user.remove_roles(role_old)

            await interaction.user.send(
                f"✅ Заявка принята!\n"
                f"Ник: {self.nick}\n"
                f"IP: {SERVER_IP}"
            )

        else:
            await interaction.user.send(
                f"❌ Заявка отклонена\n{reason}"
            )


# -------- Кнопка --------
class ApplyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.green)
    async def apply(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ApplyModal())


# -------- Команда --------
@tree.command(name="applypanel", description="Панель заявок")
async def applypanel(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Нажми кнопку ниже, чтобы подать заявку:",
        view=ApplyView()
    )


# -------- Запуск --------
@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен как {client.user}")


client.run(DISCORD_TOKEN)
