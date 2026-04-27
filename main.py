import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


class ApplicationModal(Modal, title="📋 Заявка на Fox SMP"):
    """Модальное окно для подачи заявки на сервер"""
    
    nickname = TextInput(
        label="Ваш ник в Minecraft",
        placeholder="Введите ваш ник",
        required=True,
        min_length=3,
        max_length=16
    )
    
    age = TextInput(
        label="Ваш возраст",
        placeholder="Введите возраст (8-100)",
        required=True,
        min_length=1,
        max_length=3
    )
    
    source = TextInput(
        label="Откуда вы узнали о сервере?",
        placeholder="YouTube, друг, ВКонтакте и т.д.",
        required=True,
        min_length=3,
        max_length=100
    )
    
    friend_nick = TextInput(
        label="Ник друга (для розыгрышей)",
        placeholder="Если нет - напишите 'Нет'",
        required=True,
        min_length=2,
        max_length=50
    )
    
    about = TextInput(
        label="О себе",
        placeholder="Расскажите немного о себе, ваши интересы в Майнкрафте...",
        style=discord.TextStyle.long,
        required=True,
        min_length=10,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки заявки"""
        try:
            # Валидация возраста
            try:
                age_value = int(self.age.value)
                if age_value < 8 or age_value > 100:
                    await interaction.response.send_message(
                        "❌ Возраст должен быть от 8 до 100 лет!",
                        ephemeral=True
                    )
                    return
            except ValueError:
                await interaction.response.send_message(
                    "❌ Возраст должен быть числом!",
                    ephemeral=True
                )
                return

            channel = bot.get_channel(CHANNEL_ID)
            
            if not channel:
                await interaction.response.send_message(
                    "❌ Ошибка: канал не найден. Обратитесь к администратору.",
                    ephemeral=True
                )
                return

            # Создание эмбеда с информацией о заявке
            embed = discord.Embed(
                title="📋 Новая заявка на Fox SMP",
                color=discord.Color.from_rgb(0, 255, 136),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="🎮 Ник в Minecraft",
                value=f"`{self.nickname.value}`",
                inline=False
            )
            
            embed.add_field(
                name="🎂 Возраст",
                value=f"`{age_value} лет`",
                inline=True
            )
            
            embed.add_field(
                name="📢 Источник информации",
                value=f"`{self.source.value}`",
                inline=True
            )
            
            embed.add_field(
                name="👥 Ник друга",
                value=f"`{self.friend_nick.value}`",
                inline=True
            )
            
            embed.add_field(
                name="ℹ️ О себе",
                value=self.about.value,
                inline=False
            )
            
            embed.add_field(
                name="👤 Подал заявку",
                value=f"{interaction.user.mention} ({interaction.user.name}#{interaction.user.discriminator})",
                inline=False
            )
            
            embed.set_footer(
                text="Fox SMP | Заявка получена",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )

            # Отправка заявки в канал модераторов
            await channel.send(embed=embed)
            
            # Отправка подтверждения пользователю
            await interaction.response.send_message(
                "✅ **Спасибо за вашу заявку!**\n\n"
                "Ваша заявка успешно отправлена на рассмотрение.\n"
                "Администраторы ответят вам в течение 24 часов.",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Ошибка при обработке заявки: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при отправке заявки. Попробуйте позже.",
                ephemeral=True
            )


class ApplyView(View):
    """Виджет с кнопкой для открытия заявки"""
    
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📝 Подать заявку",
        style=discord.ButtonStyle.green,
        emoji="📋"
    )
    async def apply_button(self, interaction: discord.Interaction, button: Button):
        """Кнопка для открытия модального окна"""
        await interaction.response.send_modal(ApplicationModal())


@bot.event
async def on_ready():
    """Событие при запуске бота"""
    print(f"✅ Бот запущен как {bot.user}")
    print(f"📊 Статус: {bot.user.status}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Синхронизировано {len(synced)} команд")
    except Exception as e:
        print(f"❌ Ошибка при синхронизации команд: {e}")


@bot.command(name="apply", description="Отправить кнопку заявки")
async def apply_command(ctx):
    """Команда для отправки кнопки заявки"""
    view = ApplyView()
    embed = discord.Embed(
        title="📋 Подать заявку на Fox SMP",
        description="Нажмите кнопку ниже, чтобы заполнить заявку на присоединение к нашему серверу.",
        color=discord.Color.from_rgb(0, 255, 136)
    )
    embed.add_field(
        name="ℹ️ Что потребуется?",
        value="• Ваш ник в Minecraft\n"
              "• Возраст (8-100 лет)\n"
              "• Откуда вы узнали о сервере\n"
              "• Ник друга для розыгрышей\n"
              "• Небольшое описание о себе",
        inline=False
    )
    embed.set_color(discord.Color.from_rgb(0, 255, 136))
    
    await ctx.send(embed=embed, view=view)


@bot.command(name="setup", description="Установить панель заявок")
async def setup_command(ctx):
    """Команда для установки панели заявок"""
    view = ApplyView()
    embed = discord.Embed(
        title="🎮 Fox SMP - Система приёма заявок",
        description="Заинтересованы присоединиться к нашему сообществу?",
        color=discord.Color.from_rgb(0, 255, 136)
    )
    embed.add_field(
        name="🚀 Как подать заявку?",
        value="Нажмите кнопку **'📝 Подать заявку'** и заполните форму",
        inline=False
    )
    embed.add_field(
        name="⏱️ Время рассмотрения",
        value="Обычно ответ приходит в течение 24 часов",
        inline=False
    )
    embed.add_field(
        name="🎯 Требования",
        value="• Возраст: 8+\n"
              "• Стабильное интернет соединение\n"
              "• Уважение к игрокам и правилам сервера",
        inline=False
    )
    embed.set_image(url="https://images-ext-1.discordapp.net/external/W5pB4_l2C9jJNjkKLvGxmCZGGKz0pf3u4YvyQxD8Sww/%3Fsize%3D1024/https/cdn.discordapp.com/app-icons/780904845291921409/8ea04fcda4d8e09e1fbb1c9e36f26ca9.png")
    
    await ctx.send(embed=embed, view=view)


@bot.command(name="ping")
async def ping(ctx):
    """Команда для проверки задержки бота"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Задержка: `{latency}ms`")


# Обработка ошибок
@bot.event
async def on_command_error(ctx, error):
    """Обработка ошибок команд"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ У вас нет прав для выполнения этой команды!")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Игнорировать несуществующие команды
    else:
        print(f"Ошибка команды: {error}")
        await ctx.send(f"❌ Произошла ошибка: {error}")


if __name__ == "__main__":
    if not TOKEN:
        print("❌ ОШИБКА: DISCORD_TOKEN не найден в файле .env")
        exit(1)
    
    bot.run(TOKEN)
