import os
import asyncio
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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


# ============================================================
# СИСТЕМА ЗАЯВОК (ФОРМА ЧЕРЕЗ СООБЩЕНИЯ)
# ============================================================

class ApplicationView(View):
    """Кнопки для заявки"""
    
    def __init__(self):
        super().__init__(timeout=None)
        self.applications = {}  # Хранение данных заявок

    @discord.ui.button(label="📝 Подать заявку", style=discord.ButtonStyle.green, custom_id="apply_button")
    async def apply_button(self, interaction: discord.Interaction, button: Button):
        """Кнопка для открытия формы заявки"""
        try:
            # Отправляем DM пользователю для заполнения формы
            embed = discord.Embed(
                title="📋 Форма заявки на Fox SMP",
                description="Ответьте на вопросы в этом чате.\nУ вас есть 5 минут на ответ.",
                color=discord.Color.from_rgb(0, 255, 136)
            )
            embed.add_field(name="❓ Вопрос 1", value="Какой ваш ник в Minecraft? (3-16 символов)", inline=False)
            
            await interaction.user.send(embed=embed)
            
            # Начинаем сбор данных
            await interaction.response.send_message(
                "✅ Форма заявки отправлена вам в Direct Message!",
                ephemeral=True
            )
            
            # Функция для получения ответа
            def check(msg):
                return msg.author == interaction.user and isinstance(msg.channel, discord.DMChannel)
            
            # Собираем ответы
            application_data = {}
            questions = [
                ("Какой ваш ник в Minecraft? (3-16 символов)", "nickname", 3, 16),
                ("Сколько вам лет? (8-100)", "age", None, None),
                ("Откуда вы узнали о сервере?", "source", 3, 100),
                ("Ник вашего друга (или напишите 'Нет')", "friend", 2, 50),
                ("Расскажите о себе и ваших интересах в Майнкрафте", "about", 10, 500),
            ]
            
            for i, (question, key, min_len, max_len) in enumerate(questions, 1):
                try:
                    embed = discord.Embed(
                        title=f"❓ Вопрос {i}/{len(questions)}",
                        description=question,
                        color=discord.Color.from_rgb(0, 255, 136)
                    )
                    await interaction.user.send(embed=embed)
                    
                    # Получаем ответ
                    try:
                        msg = await bot.wait_for('message', check=check, timeout=300)
                        answer = msg.content.strip()
                        
                        # Валидация
                        if key == "age":
                            try:
                                age = int(answer)
                                if age < 8 or age > 100:
                                    await interaction.user.send(
                                        "❌ Возраст должен быть от 8 до 100 лет. Попробуйте ещё раз."
                                    )
                                    i -= 1
                                    continue
                                application_data[key] = str(age)
                            except ValueError:
                                await interaction.user.send("❌ Возраст должен быть числом. Попробуйте ещё раз.")
                                i -= 1
                                continue
                        elif min_len and max_len:
                            if len(answer) < min_len or len(answer) > max_len:
                                await interaction.user.send(
                                    f"❌ Ответ должен быть от {min_len} до {max_len} символов. Попробуйте ещё раз."
                                )
                                i -= 1
                                continue
                        
                        application_data[key] = answer
                        await msg.add_reaction("✅")
                        
                    except asyncio.TimeoutError:
                        await interaction.user.send("⏱️ Время ожидания истекло. Пожалуйста, начните заново.")
                        return
                        
                except Exception as e:
                    logger.error(f"Ошибка в вопросе {i}: {e}")
                    continue
            
            # Отправляем заявку в канал модераторов
            if len(application_data) == len(questions):
                embed = discord.Embed(
                    title="📋 Новая заявка на Fox SMP",
                    color=discord.Color.from_rgb(0, 255, 136),
                    timestamp=discord.utils.utcnow()
                )
                
                embed.add_field(name="🎮 Ник Minecraft", value=f"`{application_data.get('nickname', 'N/A')}`", inline=False)
                embed.add_field(name="🎂 Возраст", value=f"`{application_data.get('age', 'N/A')} лет`", inline=True)
                embed.add_field(name="📢 Источник", value=f"`{application_data.get('source', 'N/A')}`", inline=True)
                embed.add_field(name="👥 Ник друга", value=f"`{application_data.get('friend', 'N/A')}`", inline=True)
                embed.add_field(name="ℹ️ О себе", value=application_data.get('about', 'N/A'), inline=False)
                embed.add_field(name="👤 От", value=f"{interaction.user.mention} ({interaction.user.name}#{interaction.user.discriminator})", inline=False)
                
                embed.set_footer(text="Fox SMP | Заявка получена")
                
                channel = bot.get_channel(CHANNEL_ID)
                if channel:
                    # Отправляем заявку
                    msg = await channel.send(embed=embed)
                    
                    # Добавляем кнопки для модераторов
                    approve_button = Button(label="✅ Одобрить", style=discord.ButtonStyle.green, custom_id=f"approve_{msg.id}")
                    reject_button = Button(label="❌ Отклонить", style=discord.ButtonStyle.red, custom_id=f"reject_{msg.id}")
                    
                    view = View()
                    view.add_item(approve_button)
                    view.add_item(reject_button)
                    
                    await msg.edit(view=view)
                    logger.info(f"✅ Заявка отправлена: {application_data.get('nickname')}")
                
                # Подтверждение пользователю
                confirm_embed = discord.Embed(
                    title="✅ Спасибо за вашу заявку!",
                    description="Ваша заявка успешно отправлена на рассмотрение.\n\nАдминистраторы ответят вам в течение 24 часов.",
                    color=discord.Color.from_rgb(0, 255, 136)
                )
                await interaction.user.send(embed=confirm_embed)
            else:
                await interaction.user.send("❌ Не удалось собрать все данные заявки. Пожалуйста, начните заново.")
                
        except Exception as e:
            logger.error(f"Ошибка в apply_button: {e}", exc_info=True)
            try:
                await interaction.response.send_message("❌ Ошибка при открытии формы. Попробуйте позже.", ephemeral=True)
            except:
                pass


# ============================================================
# СОБЫТИЯ БОТА
# ============================================================

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
    
    # Запускаем проверку соединения
    if not check_connection.is_running():
        check_connection.start()


@bot.event
async def on_disconnect():
    """Событие отключения"""
    logger.warning("⚠️ Бот отключился от Discord!")


@tasks.loop(minutes=5)
async def check_connection():
    """Проверка подключения каждые 5 минут"""
    try:
        if bot.is_closed():
            logger.error("❌ Соединение потеряно!")
        else:
            logger.info("✅ Бот онлайн и работает нормально")
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения: {e}")


@check_connection.before_loop
async def before_check_connection():
    """Ожидание готовности бота"""
    await bot.wait_until_ready()


# ============================================================
# КОМАНДЫ БОТА
# ============================================================

@bot.command(name="apply", description="Отправить кнопку заявки")
async def apply_command(ctx):
    """Команда для отправки кнопки заявки"""
    try:
        view = ApplicationView()
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
        
        await ctx.send(embed=embed, view=view)
        logger.info(f"✅ Команда !apply выполнена пользователем {ctx.author.name}")
    except Exception as e:
        logger.error(f"Ошибка в команде apply: {e}")
        await ctx.send("❌ Ошибка при отправке панели заявок")


@bot.command(name="setup", description="Установить панель заявок")
async def setup_command(ctx):
    """Команда для установки панели заявок"""
    try:
        view = ApplicationView()
        embed = discord.Embed(
            title="🎮 Fox SMP - Система приёма заявок",
            description="Заинтересованы присоединиться к нашему сообществу?",
            color=discord.Color.from_rgb(0, 255, 136)
        )
        embed.add_field(
            name="🚀 Как подать заявку?",
            value="Нажмите кнопку **'📝 Подать заявку'** и ответьте на вопросы в Direct Message",
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
        logger.info(f"✅ Команда !setup выполнена пользователем {ctx.author.name}")
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
        pass
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Команда требует дополнительные аргументы")
    else:
        logger.error(f"Ошибка команды: {error}", exc_info=True)
        await ctx.send(f"❌ Произошла ошибка: {error}")


# ============================================================
# ЗАПУСК БОТА С АВТОПЕРЕПОДКЛЮЧЕНИЕМ
# ============================================================

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
            wait_time = min(60 * retry_count, 300)
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
