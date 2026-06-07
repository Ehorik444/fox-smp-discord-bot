import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import re

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен бота из .env
TOKEN = os.getenv('TOKEN')

# ID категории, в которой будут создаваться каналы заявок (замените на реальный ID)
APPLICATION_CATEGORY_ID = int(os.getenv('APPLICATION_CATEGORY_ID')) 

if APPLICATION_CATEGORY_ID is None:
    raise ValueError("ID категории для заявок APPLICATION_CATEGORY_ID не найден в файле .env")

# Проверяем, что токен задан
if TOKEN is None:
    raise ValueError("Токен Discord бота не найден в файле .env")

# Определяем намерения (intents), необходимые для работы команд и компонентов
intents = discord.Intents.default()
intents.message_content = True  # Необходимо для получения содержимого сообщений в командах
intents.guilds = True  # Необходимо для взаимодействия с гильдией (сервером) и каналами
intents.members = True # Может понадобиться, если нужно получать информацию о участниках

# Инициализируем бота с префиксом и намерениями
bot = commands.Bot(command_prefix='/', intents=intents)

def sanitize_channel_name(name: str) -> str:
    """Преобразует строку в допустимое имя канала."""
    # Оставляем только буквы, цифры, дефисы и подчеркивания, затем обрезаем до 100 символов
    sanitized = re.sub(r'[^\w\-_]', '', name.lower()).replace('_', '-').strip('-_')
    return sanitized[:100]

class ApplicationModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Форма заявки")

    # Поля ввода для модального окна
    nickname = discord.ui.TextInput(
        label='Ник',
        placeholder='Введите ваш ник...',
        required=True,
        max_length=100
    )

    age = discord.ui.TextInput(
        label='Возраст',
        placeholder='Введите ваш возраст...',
        required=True,
        style=discord.TextStyle.short,
        max_length=3
    )

    source = discord.ui.TextInput(
        label='Откуда узнали?',
        placeholder='Откуда вы узнали о нас?...',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    about = discord.ui.TextInput(
        label='О себе',
        placeholder='Расскажите немного о себе...',
        required=True,
        style=discord.TextStyle.long,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Получаем гильдию (сервер)
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Ошибка: невозможно получить доступ к серверу.", ephemeral=True)
            return

        # Получаем категорию для заявок
        category = discord.utils.get(guild.categories, id=APPLICATION_CATEGORY_ID)
        if not category:
            await interaction.response.send_message("Ошибка: категория для заявок не найдена.", ephemeral=True)
            return

        # Санитизируем ник для имени канала
        clean_nickname = sanitize_channel_name(self.nickname.value)

        # Формируем имя канала
        channel_name = f"заявка-{clean_nickname}"

        # Проверяем, существует ли уже канал с таким именем
        existing_channel = discord.utils.get(category.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"Ошибка: канал для заявки '{channel_name}' уже существует.", ephemeral=True)
            return

        try:
            # Создаем новый канал в указанной категории
            new_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                topic=f"Заявка от {interaction.user.display_name} ({interaction.user.id})"
            )
        except discord.DiscordException as e:
            print(f"Ошибка при создании канала: {e}")
            await interaction.response.send_message("Произошла ошибка при создании канала заявки. Администрация уведомлена.", ephemeral=True)
            return

        # Создаем Embed с данными заявки
        embed = discord.Embed(title="Новая заявка", color=0x00ff00)
        embed.add_field(name="Пользователь", value=f"{interaction.user.mention} ({interaction.user.display_name})", inline=False)
        embed.add_field(name="Ник", value=self.nickname.value, inline=False)
        embed.add_field(name="Возраст", value=self.age.value, inline=False)
        embed.add_field(name="Откуда узнали", value=self.source.value, inline=False)
        embed.add_field(name="О себе", value=self.about.value, inline=False)

        # Отправляем Embed в созданный канал
        await new_channel.send(embed=embed)

        # Отправляем сообщение пользователю в канале, где была нажата кнопка
        await interaction.response.send_message(f"Заявка создана! Проверьте канал {new_channel.mention}.", ephemeral=True)

        # Можно дополнительно отправить сообщение в сам канал, если нужно
        # await new_channel.send(f"Заявка от {interaction.user.mention} была отправлена.")


class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.green)
    async def submit_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = ApplicationModal()
        await interaction.response.send_modal(modal)


@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен и готов к работе!')


@bot.command(name='panel')
async def panel(ctx, action: str):
    if action == 'zaiavka':
        embed = discord.Embed(
            title="ЗАЯВКА",
            description="Нажми кнопку ниже, чтобы подать заявку",
            color=0xfe8b29 # Красный цвет заголовка
        )
        view = ApplicationView()
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send("Неизвестная команда. Используйте `/panel zaiavka`.")


# Запуск бота
bot.run(TOKEN)
