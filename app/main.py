import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import re
from rcon.source import Client

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
RCON_HOST = os.getenv('MINECRAFT_RCON_HOST')
RCON_PORT = int(os.getenv('MINECRAFT_RCON_PORT'))
RCON_PASS = os.getenv('MINECRAFT_RCON_PASSWORD')
SERVER_IP = os.getenv('MINECRAFT_SERVER_IP')

NEWBIE_ROLE_ID = int(os.getenv('ROLE_ID_NEWBIE'))
PLAYER_ROLE_ID = int(os.getenv('ROLE_ID_PLAYER'))
GUILD_ID = int(os.getenv('GUILD_ID'))
TICKETS_CATEGORY_ID = int(os.getenv('TICKETS_CATEGORY_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ===================== УТИЛИТЫ =====================

def valid_nickname(nick: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9_]{3,16}$', nick))


async def run_rcon(command: str):
    loop = asyncio.get_running_loop()

    def _run():
        with Client(RCON_HOST, RCON_PORT, passwd=RCON_PASS, timeout=5) as client:
            return client.run(command)

    return await loop.run_in_executor(None, _run)


async def safe_dm(user: discord.User, text: str):
    try:
        await user.send(text)
    except discord.Forbidden:
        print(f"Не удалось отправить ЛС пользователю {user}")


# ===================== МОДАЛКА =====================

class ApplicationModal(discord.ui.Modal, title='Заявка на сервер'):

    mc_nickname = discord.ui.TextInput(label='Ник Minecraft', max_length=16)
    age = discord.ui.TextInput(label='Возраст')
    how_found = discord.ui.TextInput(label='Откуда узнали?', style=discord.TextStyle.paragraph)
    who_invited = discord.ui.TextInput(label='Кто пригласил?', required=False)
    about = discord.ui.TextInput(label='О себе', style=discord.TextStyle.paragraph, max_length=400)

    async def on_submit(self, interaction: discord.Interaction):

        if not valid_nickname(self.mc_nickname.value):
            return await interaction.response.send_message(
                "Некорректный ник Minecraft", ephemeral=True
            )

        await interaction.response.send_message("Заявка отправлена!", ephemeral=True)

        data = {
            "mc_nickname": self.mc_nickname.value,
            "age": self.age.value,
            "how_found": self.how_found.value,
            "who_invited": self.who_invited.value or "Не указан",
            "about": self.about.value
        }

        asyncio.create_task(create_ticket(interaction.user, data))


# ===================== СОЗДАНИЕ ТИКЕТА =====================

async def create_ticket(user: discord.User, data: dict):

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        return

    category = guild.get_channel(TICKETS_CATEGORY_ID)
    if not isinstance(category, discord.CategoryChannel):
        print("Invalid category")
        return

    # ❗ защита от дублей
    for ch in category.text_channels:
        if str(user.id) in ch.topic:
            await safe_dm(user, "У вас уже есть открытая заявка")
            return

    name = f"ticket-{user.name}-{user.id}"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True)
    }

    try:
        channel = await guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites,
            topic=str(user.id)
        )
    except discord.Forbidden:
        print("Нет прав создавать канал")
        return

    embed = discord.Embed(
        title=f"Заявка от {user}",
        description=f"ID: {user.id}",
        color=0x00aaff
    )

    for k, v in data.items():
        embed.add_field(name=k, value=v, inline=False)

    view = TicketView(user, data)
    message = await channel.send(embed=embed, view=view)
    view.message = message


# ===================== VIEW =====================

class TicketView(discord.ui.View):

    def __init__(self, user: discord.User, data: dict):
        super().__init__(timeout=None)
        self.user = user
        self.data = data
        self.message = None

    async def disable(self):
        for i in self.children:
            i.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def finalize(self, channel, success: bool, reason: str = ""):

        await self.disable()

        if success:
            try:
                await run_rcon(f'whitelist add {self.data["mc_nickname"]}')
            except Exception as e:
                print(f"RCON error: {e}")
                await safe_dm(self.user, "Ошибка whitelist")
                return

            await safe_dm(
                self.user,
                f"Вы приняты! IP: {SERVER_IP}"
            )

            member = channel.guild.get_member(self.user.id)
            if member:
                try:
                    old = channel.guild.get_role(NEWBIE_ROLE_ID)
                    new = channel.guild.get_role(PLAYER_ROLE_ID)

                    if old:
                        await member.remove_roles(old)
                    if new:
                        await member.add_roles(new)
                except discord.Forbidden:
                    print("Ошибка ролей")

        else:
            await safe_dm(self.user, f"Отказ: {reason or 'без причины'}")

        try:
            await channel.delete()
        except Exception as e:
            print(f"Ошибка удаления канала: {e}")

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.finalize(interaction.channel, True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DeclineModal(self))


# ===================== МОДАЛКА ОТКАЗА =====================

class DeclineModal(discord.ui.Modal, title="Причина отказа"):

    reason = discord.ui.TextInput(label="Причина", style=discord.TextStyle.paragraph)

    def __init__(self, view: TicketView):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.view.finalize(interaction.channel, False, self.reason.value)


# ===================== КНОПКА =====================

class ApplyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())


# ===================== EVENTS =====================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(ApplyView())


# ===================== КОМАНДА =====================

@bot.command()
@commands.has_permissions(administrator=True)
async def apply(ctx):
    embed = discord.Embed(
        title="Заявка",
        description="Нажмите кнопку",
        color=0x00ff00
    )
    await ctx.send(embed=embed, view=ApplyView())
    await ctx.message.delete()


bot.run(TOKEN)
