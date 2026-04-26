import os
import discord
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
from dotenv import load_dotenv
from mcrcon import MCRcon
from openai import OpenAI

load_dotenv()

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ----------- AI проверка заявки -----------
def check_application(data: str):
    prompt = f"""
Ты модератор Minecraft сервера. Оцени заявку и ответь строго в формате:

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


# ----------- Modal форма -----------
class ApplyModal(Modal, title="Заявка на сервер"):
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

        await interaction.response.send_message("⏳ Заявка отправлена на рассмотрение...", ephemeral=True)

        accepted, reason = check_application(data)

        if accepted:
            # --- RCON ---
            with MCRcon(
                os.getenv("RCON_HOST"),
                os.getenv("RCON_PASSWORD"),
                port=int(os.getenv("RCON_PORT"))
            ) as mcr:
                mcr.command(f"whitelist add {self.nick}")

            # --- роли ---
            role = discord.utils.get(interaction.guild.roles, name="Игрок")
            old_role = discord.utils.get(interaction.guild.roles, name="Новичок")

            if role:
                await interaction.user.add_roles(role)
            if old_role:
                await interaction.user.remove_roles(old_role)

            # --- ЛС ---
            await interaction.user.send(
                f"✅ Заявка принята!\n"
                f"Ник: {self.nick}\n"
                f"IP: {os.getenv('SERVER_IP')}"
            )

        else:
            await interaction.user.send(
                f"❌ Заявка отклонена\n{reason}"
            )


# ----------- Кнопка -----------
class ApplyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.green)
    async def apply(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ApplyModal())


# ----------- Команда -----------
@tree.command(name="applypanel", description="Создать панель заявок")
async def applypanel(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Нажмите кнопку ниже, чтобы подать заявку:",
        view=ApplyView()
    )


# ----------- Запуск -----------
@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен как {client.user}")


client.run(os.getenv("DISCORD_TOKEN"))
