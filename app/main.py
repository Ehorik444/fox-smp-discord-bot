import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from rcon.source import Client # или другая библиотека RCON

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
RCON_HOST = os.getenv('MINECRAFT_RCON_HOST')
RCON_PORT = int(os.getenv('MINECRAFT_RCON_PORT'))
RCON_PASS = os.getenv('MINECRAFT_RCON_PASSWORD')
SERVER_IP = os.getenv('MINECRAFT_SERVER_IP')
NEWBIE_ROLE_ID = int(os.getenv('ROLE_ID_NEWBIE'))
PLAYER_ROLE_ID = int(os.getenv('ROLE_ID_PLAYER'))
GUILD_ID = int(os.getenv('GUILD_ID'))
TICKETS_CATEGORY_ID = int(os.getenv('TICKETS_CATEGORY_ID')) # Новый параметр

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
        label='Откуда узнали о сервере?',
        placeholder='Расскажите...',
        required=True,
        style=discord.TextStyle.paragraph    )
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

        # Запуск создания тикета в фоне
        asyncio.create_task(create_ticket(interaction.user, application_data))

async def create_ticket(user: discord.User, data: dict):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Гильдия не найдена.")
        return

    category = guild.get_channel(TICKETS_CATEGORY_ID)
    if not category or not isinstance(category, discord.CategoryChannel):
        print(f"Категория тикетов с ID {TICKETS_CATEGORY_ID} не найдена или не является категорией.")
        return

    # Создаём канал с именем, например, "ticket-{username}"
    ticket_name = f"ticket-{user.name.lower().replace(' ', '-')}-{user.discriminator}"
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True), # Позволяем пользователю читать тикет
    }
    ticket_channel = await guild.create_text_channel(ticket_name, category=category, overwrites=overwrites)
    
    # Отправляем сообщение с данными
    embed = discord.Embed(        title=f"Новая заявка от {user.display_name}",
        description=f"**Пользователь Discord:** {user.mention}\n**ID:** {user.id}",
        color=0x00aaff
    )
    embed.add_field(name="Ник в Minecraft", value=data["mc_nickname"], inline=False)
    embed.add_field(name="Возраст", value=data["age"], inline=False)
    embed.add_field(name="Откуда узнал?", value=data["how_found"], inline=False)
    embed.add_field(name="Кто пригласил?", value=data["who_invited"], inline=False)
    embed.add_field(name="О себе", value=data["about"], inline=False)

    view = TicketActionsView(user, data)
    message = await ticket_channel.send(embed=embed, view=view)
    # Опционально: прикрепить сообщение, чтобы оно всегда было видно наверху
    # await message.pin()

class TicketActionsView(discord.ui.View):
    def __init__(self, applicant: discord.User, data: dict):
        super().__init__(timeout=None) # Кнопки всегда активны
        self.applicant = applicant
        self.data = data

    async def finalize_ticket(self, channel: discord.TextChannel, success: bool, reason: str = ""):
        """Закрывает тикет: отправляет сообщение пользователю, выполняет действия и удаляет канал."""
        try:
            if success:
                # --- Принятие ---
                # a. Добавить в белый список через RCON
                try:
                    with Client(RCON_HOST, RCON_PORT, passwd=RCON_PASS, timeout=5) as client:
                        response_rcon = client.run(f'whitelist add {self.data["mc_nickname"]}')
                        print(f"RCON whitelist command response: {response_rcon}") # Лог
                except Exception as e:
                    print(f"Ошибка RCON: {e}")
                    await self.applicant.send("Произошла ошибка при добавлении вас в белый список. Администрация уведомлена.")
                    await channel.delete()
                    return # Прервать, не изменяя роль

                # b. Отправить сообщение пользователю
                await self.applicant.send(f"Ваша заявка принята! Ваш ник: **{self.data['mc_nickname']}**. IP сервера: **{SERVER_IP}**. Добро пожаловать!")

                # c. Изменить роль в гильдии
                guild = channel.guild
                member = guild.get_member(self.applicant.id)
                if member:
                    old_role = guild.get_role(NEWBIE_ROLE_ID)
                    new_role = guild.get_role(PLAYER_ROLE_ID)
                    if old_role:
                        await member.remove_roles(old_role)
                    if new_role:
                        await member.add_roles(new_role)                    print(f"Роль пользователя {self.applicant.name} изменена.")
                else:
                    print(f"Пользователь {self.applicant.name} не найден в гильдии.")
            else:
                # --- Отказ ---
                if reason:
                     await self.applicant.send(f"В вашей заявке отказано. Причина: {reason}")
                else:
                     await self.applicant.send("В вашей заявке отказано по техническим причинам.")

            # Удаляем канал тикета
            await channel.delete()
        except Exception as e:
            print(f"Ошибка при финализации тикета: {e}")


    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="✅")
    async def accept_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Отключаем кнопки
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        # Завершаем тикет как успешный
        await self.finalize_ticket(interaction.channel, success=True)


    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="❌")
    async def decline_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Создаём модальное окно для ввода причины
        modal = DeclineReasonModal(self)
        await interaction.response.send_modal(modal)

class DeclineReasonModal(discord.ui.Modal, title="Причина отказа"):
    def __init__(self, ticket_view: TicketActionsView):
        super().__init__()
        self.ticket_view = ticket_view

    reason = discord.ui.TextInput(
        label='Укажите причину отказа',
        placeholder='Например: неподобающее поведение, спам и т.д.',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() # Откладываем ответ, так как действия могут занять время
        # Отключаем кнопки в родительском View
        for item in self.ticket_view.children:
            item.disabled = True        # Обновляем сообщение, чтобы кнопки стали неактивны
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self.ticket_view)
        # Завершаем тикет с отказом
        await self.ticket_view.finalize_ticket(interaction.channel, success=False, reason=self.reason.value)


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
