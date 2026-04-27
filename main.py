import os
import asyncio
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID")) if os.getenv("GUILD_ID") else None
CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID")) if os.getenv("APPLICATION_CHANNEL_ID") else None

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

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
                logger.error(f"Канал {CHANNEL_ID} не найден")
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
            
            logger.info(f"Новая заявка от {interaction.user.name}: {self.nickname.value}")
            
        except asyncio.TimeoutError:
            logger.error("Timeout при обработке заявки")
            try:
                await interaction.response.send_message(
                    "❌ Время ожидания истекло. Попробуйте позже.",
                    ephemeral=True
                )
            except:
                pass
        except Exception as e:
            logger.error(f"Ошибка при обработке заявки: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    "❌ Произошла ошибка при отправке заявки. Попробуйте позже.",
                    ephemeral=True
                )
            except:
                pass


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
        try:
            await interaction.response.send_modal(ApplicationModal())
        except Exception as e:
            logger.error(f"Ошибка при открытии модального окна: {e}")
            await interaction.response.send_message(
                "❌ Ошибка при открытии формы. Попробуйте позже.",
                ephemeral=True
            )


@bot.event
async def on_ready():
    """Событие при запуске бота"""
    logger.info(f"✅ Бот запущен как {bot.user}")
    logger.info(f"📊 Статус: {bot.user.status}")
    logger.info(f"🔗 ID сервера: {GUILD_ID}")
    logger.info(f"💬 ID канала для заявок: {CHANNEL_ID}")
    
    try:
        synced = await bot.tree.sync()
        logger.info(f"🔄 Синхронизировано {len(synced)} команд")
    except Exception as e:
        logger.error(f"❌ Ошибка при синхронизации команд: {e}")
    
    # Запуск задачи мониторинга
    if not check_connection.is_running():
        check_connection.start()


@bot.event
async def on_error(event, *args, **kwargs):
    """Глобальная обработка ошибок"""
    logger.error(f"Ошибка в событии {event}:", exc_info=True)


@bot.event
async def on_disconnect():
    """Событие отключения"""
    logger.warning("⚠️ Бот отключился от Discord!")


@tasks.loop(minutes=5)
async def check_connection():
    """Проверка подключения каждые 5 минут"""
    try:
        if bot.is_closed():
            logger.error("❌ Соединение потеряно! Переподключение...")
            await bot.close()
        else:
            logger.info("✅ Бот онлайн и работает нормально")
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения: {e}")


@check_connection.before_loop
async def before_check_connection():
    """Ожидание готовности бота перед началом проверок"""
    await bot.wait_until_ready()


@bot.command(name="apply", description="Отправить кнопку заявки")
async def apply_command(ctx):
    """Команда для отправки кнопки заявки"""
    try:
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
        logger.info(f"Команда !apply выполнена пользователем {ctx.author.name}")
    except Exception as e:
        logger.error(f"Ошибка в команде apply: {e}")
        await ctx.send("❌ Ошибка при отправке панели заявок")


@bot.command(name="setup", description="Установить панель заявок")
async def setup_command(ctx):
    """Команда для установки панели заявок"""
    try:
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
        
        await ctx.send(embed=embed, view=view)
        logger.info(f"Команда !setup выполнена пользователем {ctx.author.name}")
    except Exception as e:
        logger.error(f"Ошибка в команде setup: {e}")
        await ctx.send("❌ Ошибка при установке панели заявок")


@bot.command(name="ping")
async def ping(ctx):
    """Команда для проверки задержки бота"""
    try:
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Задержка: `{latency}ms`")
    except Exception as e:
        logger.error(f"Ошибка в команде ping: {e}")
        await ctx.send("❌ Ошибка при получении пинга")


@bot.event
async def on_command_error(ctx, error):
    """Обработка ошибок команд"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ У вас нет прав для выполнения этой команды!")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Игнорировать несуществующие команды
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Команда требует дополнительные аргументы")
    else:
        logger.error(f"Ошибка команды: {error}", exc_info=True)
        await ctx.send(f"❌ Произошла ошибка: {error}")


async def main():
    """Главная функция с обработкой переподключения"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with bot:
                await bot.start(TOKEN)
        except discord.errors.LoginFailure:
            logger.error("❌ ОШИБКА: Неверный токен Discord!")
            return
        except Exception as e:
            retry_count += 1
            wait_time = min(60 * retry_count, 300)  # Максимум 5 минут
            logger.error(f"❌ Бот упал! Попытка переподключения {retry_count}/{max_retries} через {wait_time}с")
            logger.error(f"Ошибка: {e}", exc_info=True)
            await asyncio.sleep(wait_time)
    
    logger.error("❌ Максимум попыток переподключения достигнут!")


if __name__ == "__main__":
    if not TOKEN:
        logger.error("❌ ОШИБКА: DISCORD_TOKEN не найден в файле .env")
        exit(1)
    
    if not GUILD_ID or not CHANNEL_ID:
        logger.error("❌ ОШИБКА: GUILD_ID или APPLICATION_CHANNEL_ID не найдены в файле .env")
        exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
