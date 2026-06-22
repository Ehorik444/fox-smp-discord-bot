import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
import datetime
import json
import os
from mcrcon import MCRcon
# --- CONFIGURATION ---
TOKEN = 'YOUR_BOT_TOKEN'
GUILD_ID = 123456789012345678  # ID вашего сервера
ADMIN_CHANNEL_ID = 123456789012345678  # ID канала для заявок
NOVICE_ROLE_ID = 123456789012345678  # ID роли "Новичок"
RCON_HOST = '127.0.0.1'
RCON_PORT = 25575
RCON_PASSWORD = 'your_rcon_password'
COOLDOWN_FILE = 'cooldowns.json'
# --- COOLDOWN HELPERS ---
def load_cooldowns():
    if os.path.exists(COOLDOWN_FILE):
        with open(COOLDOWN_FILE, 'r') as f:
            return json.load(f)
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
    return None
def set_cooldown(user_id):
    cooldowns = load_cooldowns()
    expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
    cooldowns[str(user_id)] = expiry.isoformat()
    save_cooldowns(cooldowns)
# --- BOT SETUP ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
    async def setup_hook(self):
        self.add_view(PersistentApplyView())
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
bot = MyBot()
# --- RCON HELPER ---
def rcon_command(command):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(command)
            return resp
    except Exception as e:
        return f"Error: {e}"
# --- MODAL ---
class ApplicationModal(ui.Modal, title='Заявка на сервер'):
    nickname = ui.TextInput(label='Ник в игре', placeholder='Ваш никнейм...')
    age = ui.TextInput(label='Возраст', placeholder='Сколько вам лет?')
    source = ui.TextInput(label='Откуда узнали?', placeholder='Ютуб, друзья, мониторинг...')
    about = ui.TextInput(label='О себе', style=discord.TextStyle.paragraph, placeholder='Расскажите немного о себе и своих планах на сервере.')
    async def on_submit(self, interaction: discord.Interaction):
        # Проверка на КД перед отправкой (на всякий случай)
        expiry = check_cooldown(interaction.user.id)
        if expiry:
            time_left = expiry - datetime.datetime.now()
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            await interaction.response.send_message(f"Вы сможете подать новую заявку через {hours}ч. {minutes}мин.", ephemeral=True)
            return
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        if not admin_channel:
            await interaction.response.send_message("Ошибка: Канал для заявок не найден.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Новая заявка: {interaction.user.name}", color=discord.Color.blue())
        embed.add_field(name="Ник", value=self.nickname.value, inline=True)
        embed.add_field(name="Возраст", value=self.age.value, inline=True)
        embed.add_field(name="Откуда узнали", value=self.source.value, inline=False)
        embed.add_field(name="О себе", value=self.about.value, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id}")
        view = AdminReviewView(user_id=interaction.user.id, nickname=self.nickname.value)
        
        await admin_channel.send(embed=embed, view=view)
        await interaction.response.send_message("Ваша заявка отправлена на рассмотрение!", ephemeral=True)
# --- VIEWS ---
class PersistentApplyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label='Подать заявку', style=discord.ButtonStyle.green, custom_id='apply_button')
    async def apply(self, interaction: discord.Interaction, button: ui.Button):
        expiry = check_cooldown(interaction.user.id)
        if expiry:
            time_left = expiry - datetime.datetime.now()
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            await interaction.response.send_message(f"Вы сможете подать новую заявку через {hours}ч. {minutes}мин.", ephemeral=True)
            return
        
        await interaction.response.send_modal(ApplicationModal())
class AdminReviewView(ui.View):
    def __init__(self, user_id, nickname):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nickname = nickname
    @ui.button(label='Принять', style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        
        # Whitelist via RCON
        rcon_res = rcon_command(f"whitelist add {self.nickname}")
        
        # Role management
        role_msg = ""
        if member:
            role = guild.get_role(NOVICE_ROLE_ID)
            if role:
                await member.remove_roles(role)
                role_msg = "Роль 'Новичок' снята."
            try:
                await member.send(f"Ваша заявка одобрена! Вы добавлены в белый список. {role_msg}")
            except:
                pass
        
        await interaction.response.edit_message(content=f"✅ Принято модератором {interaction.user.mention}. RCON: {rcon_res}", view=None)
    @ui.button(label='Отклонить', style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        set_cooldown(self.user_id)
        
        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                await member.send("К сожалению, ваша заявка была отклонена. Вы сможете попробовать снова через 24 часа.")
            except:
                pass
                
        await interaction.response.edit_message(content=f"❌ Отклонено модератором {interaction.user.mention}. КД 24ч установлен.", view=None)
# --- COMMANDS ---
@bot.tree.command(name="заявка", description="Создать сообщение для подачи заявок", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def application_setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Заявка на Minecraft сервер",
        description="Нажмите на кнопку ниже, чтобы заполнить анкету и получить доступ к серверу!",
        color=discord.Color.green()
    )
    await interaction.response.send_message("Сообщение создано.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=PersistentApplyView())
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
if __name__ == "__main__":
    bot.run(TOKEN)
