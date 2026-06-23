import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
import datetime
import json
import os
from mcrcon import MCRcon
# ==========================================
#              НАСТРОЙКИ (CONFIG)
# ==========================================
# Замените значения ниже на ваши данные
TOKEN = 'YOUR_BOT_TOKEN'
GUILD_ID = 123456789012345678          # ID вашего сервера
ADMIN_CHANNEL_ID = 123456789012345678  # ID канала для модераторов
NOVICE_ROLE_ID = 123456789012345678    # ID роли "Новичок"
# Настройки Minecraft RCON
RCON_HOST = '127.0.0.1'
RCON_PORT = 25575
RCON_PASSWORD = 'your_rcon_password'
COOLDOWN_FILE = 'cooldowns.json'
# ==========================================
# Функции для работы с КД (сохранение в файл, чтобы не пропало после перезагрузки)
def load_cooldowns():
    if os.path.exists(COOLDOWN_FILE):
        try:
            with open(COOLDOWN_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}
def save_cooldowns(data):
    with open(COOLDOWN_FILE, 'w') as f:
        json.dump(data, f)
def check_cooldown(user_id):
    cooldowns = load_cooldowns()
    if str(user_id) in cooldowns:
        expiry = datetime.datetime.fromisoformat(cooldowns[str(user_id)])
        if datetime.datetime.now() < expiry:
            return expiry
        else:
            # КД истек, удаляем из списка
            del cooldowns[str(user_id)]
            save_cooldowns(cooldowns)
    return None
def set_cooldown(user_id):
    cooldowns = load_cooldowns()
    expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
    cooldowns[str(user_id)] = expiry.isoformat()
    save_cooldowns(cooldowns)
# Инициализация бота
class WhitelistBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
    async def setup_hook(self):
        # Регистрация View для того, чтобы кнопки работали после перезагрузки бота
        self.add_view(PersistentApplyView())
        # Синхронизация слеш-команд
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
bot = WhitelistBot()
# Функция отправки команд на сервер Minecraft
def rcon_command(command):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            return mcr.command(command)
    except Exception as e:
        return f"Ошибка RCON: {e}"
# Модальное окно анкеты
class ApplicationModal(ui.Modal, title='Анкета на Minecraft сервер'):
    nickname = ui.TextInput(label='Ник в игре', placeholder='Напр. Notch', min_length=3, max_length=16)
    age = ui.TextInput(label='Возраст', placeholder='Напр. 18', min_length=1, max_length=2)
    source = ui.TextInput(label='Откуда узнали о нас?', placeholder='Друзья, YouTube...', max_length=100)
    about = ui.TextInput(label='О себе', style=discord.TextStyle.paragraph, placeholder='Расскажите о себе...', min_length=10)
    async def on_submit(self, interaction: discord.Interaction):
        # Финальная проверка КД
        expiry = check_cooldown(interaction.user.id)
        if expiry:
            await interaction.response.send_message("Ошибка: вы уже подавали заявку недавно.", ephemeral=True)
            return
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        if not admin_channel:
            await interaction.response.send_message("Ошибка: админ-канал не найден. Сообщите администратору.", ephemeral=True)
            return
        # Создаем эмбед для админов
        embed = discord.Embed(title="📝 Новая заявка", color=discord.Color.blue())
        embed.add_field(name="Пользователь", value=interaction.user.mention, inline=True)
        embed.add_field(name="Ник в игре", value=self.nickname.value, inline=True)
        embed.add_field(name="Возраст", value=self.age.value, inline=True)
        embed.add_field(name="Откуда узнали", value=self.source.value, inline=False)
        embed.add_field(name="О себе", value=self.about.value, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id}")
        view = AdminReviewView(user_id=interaction.user.id, nickname=self.nickname.value)
        await admin_channel.send(embed=embed, view=view)
        
        await interaction.response.send_message("Ваша заявка успешно отправлена! Ожидайте решения модерации.", ephemeral=True)
# Кнопка под постом в общем канале
class PersistentApplyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label='Подать заявку', style=discord.ButtonStyle.green, custom_id='persistent_apply_btn')
    async def apply(self, interaction: discord.Interaction, button: ui.Button):
        expiry = check_cooldown(interaction.user.id)
        if expiry:
            time_left = expiry - datetime.datetime.now()
            h, rem = divmod(int(time_left.total_seconds()), 3600)
            m, _ = divmod(rem, 60)
            await interaction.response.send_message(f"❌ Вы сможете подать новую заявку через {h}ч. {m}мин.", ephemeral=True)
            return
        
        await interaction.response.send_modal(ApplicationModal())
# Кнопки для админов (Принять / Отклонить)
class AdminReviewView(ui.View):
    def __init__(self, user_id, nickname):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nickname = nickname
    @ui.button(label='Принять', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        
        # 1. Добавляем в вайтлист
        rcon_res = rcon_command(f"whitelist add {self.nickname}")
        
        status_msg = f"✅ Игрок **{self.nickname}** принят модератором {interaction.user.mention}."
        
        # 2. Снимаем роль
        if member:
            role = guild.get_role(NOVICE_ROLE_ID)
            if role and role in member.roles:
                await member.remove_roles(role)
                status_msg += "\n🔓 Роль 'Новичок' снята."
            try:
                await member.send(f"🎉 Поздравляем! Ваша заявка на сервер одобрена. Ваш ник **{self.nickname}** добавлен в белый список.")
            except:
                status_msg += "\n⚠️ Не удалось отправить ЛС игроку."
        
        await interaction.response.edit_message(content=status_msg, view=None)
    @ui.button(label='Отклонить', style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        set_cooldown(self.user_id)
        
        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                await member.send("❌ К сожалению, ваша заявка была отклонена. Вы сможете подать новую через 24 часа.")
            except:
                pass
        
        await interaction.response.edit_message(content=f"🚫 Заявка игрока (ID: {self.user_id}) отклонена модератором {interaction.user.mention}. Установлен КД 24 часа.", view=None)
# Слеш-команда для создания поста
@bot.tree.command(name="заявка", description="Создать сообщение с кнопкой подачи заявки")
@app_commands.checks.has_permissions(administrator=True)
async def setup_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌍 Набор на сервер",
        description="Хочешь играть с нами? Жми на кнопку ниже и заполняй анкету!\n\n*Убедись, что твой профиль открыт для получения личных сообщений.*",
        color=discord.Color.green()
    )
    await interaction.channel.send(embed=embed, view=PersistentApplyView())
    await interaction.response.send_message("Пост для заявок успешно создан!", ephemeral=True)
@bot.event
async def on_ready():
    print(f'Бот запущен как {bot.user}')
# Запуск
if __name__ == "__main__":
    if TOKEN == 'YOUR_BOT_TOKEN':
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ОШИБКА: ЗАМЕНИТЕ 'YOUR_BOT_TOKEN' В ФАЙЛЕ main.py")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        bot.run(TOKEN)
