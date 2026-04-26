import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from rcon.source import Client # или другая библиотека RCON
import openai

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
RCON_HOST = os.getenv('MINECRAFT_RCON_HOST')
RCON_PORT = int(os.getenv('MINECRAFT_RCON_PORT'))
RCON_PASS = os.getenv('MINECRAFT_RCON_PASSWORD')
SERVER_IP = os.getenv('MINECRAFT_SERVER_IP')
NEWBIE_ROLE_ID = int(os.getenv('ROLE_ID_NEWBIE'))
PLAYER_ROLE_ID = int(os.getenv('ROLE_ID_PLAYER'))
GUILD_ID = int(os.getenv('GUILD_ID'))

openai.api_key = OPENAI_API_KEY

# Интенты для доступа к ролям и сообщениям
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Необходимо для изменения ролей

bot = commands.Bot(command_prefix='!', intents=intents)

class ApplicationModal(discord.ui.Modal, title='Заявка на сервер'):
    def __init__(self):
        super().__init__()

    mc_nickname = discord.ui.TextInput(
        label='Ваш ник в Minecraft',
        placeholder='Введите ник...',
        required=True,
        max_length=16,
        min_length=3
    )
    age = discord.ui.TextInput(
        label='Ваш возраст',
        placeholder='Введите возраст...',
        required=True,
        style=discord.TextStyle.short
    )
    how_found = discord.ui.TextInput(
        label='Откуда узнали о сервере?',        placeholder='Расскажите...',
        required=True,
        style=discord.TextStyle.paragraph
    )
    who_invited = discord.ui.TextInput(
        label='Кто пригласил?',
        placeholder='Имя пригласившего (если был)',
        required=False, # Необязательное поле
        style=discord.TextStyle.short
    )
    about = discord.ui.TextInput(
        label='Расскажите немного о себе',
        placeholder='Расскажите о своих интересах, опыте и т.д....',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=480
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Заявка отправлена! Ожидайте ответ.", ephemeral=True)
        
        application_data = {
            "mc_nickname": self.mc_nickname.value,
            "age": self.age.value,
            "how_found": self.how_found.value,
            "who_invited": self.who_invited.value if self.who_invited.value else "Не указан",
            "about": self.about.value
        }

        # Запуск обработки в фоне, чтобы не блокировать интеракцию
        asyncio.create_task(process_application(interaction.user, application_data))

async def process_application(user: discord.User, data: dict):
    try:
        # --- 1. Анализ OpenAI ---
        prompt = f"""
        Проанализируй следующую заявку на вступление на Minecraft сервер.
        Решение: принимается (true) или отклоняется (false).
        Если отклоняется, укажи краткую, уважительную причину отказа (на русском языке), которая будет отправлена пользователю.
        Заявка: {data}
        Ответь в строго формате JSON: {{"decision": true/false, "reason": "причина если false, иначе null"}}
        """
        
        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo", # или gpt-4
          messages=[{"role": "user", "content": prompt}],
          temperature=0.1 # Для более детерминированного вывода
        )
        
        response_text = response.choices[0].message['content'].strip()        # print(response_text) # Для отладки
        
        # Извлечение JSON из ответа (может потребоваться более надежный парсер)
        import json
        result = json.loads(response_text)
        
        decision = result.get("decision")
        reason = result.get("reason")

        # --- 2. Действия в зависимости от решения ---
        if decision:
            # --- Принятие ---
            # a. Добавить в белый список через RCON
            try:
                with Client(RCON_HOST, RCON_PORT, passwd=RCON_PASS, timeout=5) as client:
                    response_rcon = client.run(f'whitelist add {data["mc_nickname"]}')
                    print(f"RCON whitelist command response: {response_rcon}") # Лог
            except Exception as e:
                print(f"Ошибка RCON: {e}")
                await user.send("Произошла ошибка при добавлении вас в белый список. Администрация уведомлена.")
                return # Прервать, не отправляя сообщение о принятии

            # b. Отправить сообщение пользователю
            await user.send(f"Ваша заявка принята! Ваш ник: **{data['mc_nickname']}**. IP сервера: **{SERVER_IP}**. Добро пожаловать!")
            
            # c. Изменить роль в гильдии
            guild = bot.get_guild(GUILD_ID)
            if guild:
                member = guild.get_member(user.id)
                if member:
                    old_role = guild.get_role(NEWBIE_ROLE_ID)
                    new_role = guild.get_role(PLAYER_ROLE_ID)
                    if old_role:
                        await member.remove_roles(old_role)
                    if new_role:
                        await member.add_roles(new_role)
                    print(f"Роль пользователя {user.name} изменена.")
                else:
                    print(f"Пользователь {user.name} не найден в гильдии.")
            else:
                print("Гильдия не найдена.")
                
        else:
            # --- Отказ ---
            if reason:
                 await user.send(f"В вашей заявке отказано. Причина: {reason}")
            else:
                 await user.send("В вашей заявке отказано по техническим причинам.")

    except Exception as e:        print(f"Ошибка при обработке заявки для {user.name}: {e}")
        await user.send("Произошла ошибка при обработке вашей заявки. Администрация уведомлена.")


class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Кнопка всегда активна

    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary, emoji="📝")
    async def apply_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = ApplicationModal()
        await interaction.response.send_modal(modal)

@bot.event
async def on_ready():
    print(f'{bot.user} успешно подключен как бот.')
    # Регистрация представления для постоянной кнопки
    bot.add_view(ApplyView())

@bot.command(name='send_apply_msg')
@commands.has_permissions(administrator=True) # Только администратор может отправить
async def send_apply_message(ctx):
    view = ApplyView()
    embed = discord.Embed(
        title="Хочешь на наш сервер?",
        description="Нажми кнопку ниже, чтобы подать заявку!",
        color=0x00ff00
    )
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete() # Удалить команду администратора

bot.run(TOKEN)
