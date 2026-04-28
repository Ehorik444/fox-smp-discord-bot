import discord
from discord.ext import commands
from discord import app_commands
import asyncio

APPLICATION_CHANNEL_ID = 1496595878700388463
LOG_CHANNEL_ID = 1496595878700388463  # можешь поменять

send_queue = asyncio.Queue()


# =========================
# WORKER (анти-лаг ядро)
# =========================

async def sender_worker(bot):
    await bot.wait_until_ready()

    while True:
        channel_id, embed, view = await send_queue.get()

        for attempt in range(5):
            try:
                channel = bot.get_channel(channel_id)

                if channel is None:
                    channel = await bot.fetch_channel(channel_id)

                await channel.send(embed=embed, view=view)
                print("✅ Заявка отправлена")
                break

            except Exception as e:
                print(f"❌ Ошибка отправки ({attempt+1}):", e)
                await asyncio.sleep(2 * (attempt + 1))

        send_queue.task_done()


# =========================
# MODAL
# =========================

class ApplicationModal(discord.ui.Modal, title="📋 Заявка на сервер"):

    nick = discord.ui.TextInput(label="Ник в Minecraft")
    age = discord.ui.TextInput(label="Возраст")
    source = discord.ui.TextInput(label="Откуда узнал?")
    friend = discord.ui.TextInput(label="Ник друга (необязательно)", required=False)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="📩 Новая заявка",
            color=0xfe8b29
        )

        embed.add_field(name="👤 Пользователь", value=interaction.user.mention, inline=False)
        embed.add_field(name="🎮 Ник", value=self.nick.value)
        embed.add_field(name="🎂 Возраст", value=self.age.value)
        embed.add_field(name="📢 Откуда узнал", value=self.source.value, inline=False)
        embed.add_field(name="👥 Друг", value=self.friend.value or "Нет", inline=False)
        embed.add_field(name="📝 О себе", value=self.about.value, inline=False)

        await send_queue.put((APPLICATION_CHANNEL_ID, embed, ReviewView()))

        await interaction.followup.send("✅ Заявка отправлена!", ephemeral=True)


# =========================
# КНОПКА ПОДАЧИ
# =========================

class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📨 Подать заявку", style=discord.ButtonStyle.primary)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())


# =========================
# КНОПКИ ПРИНЯТЬ / ОТКЛОНИТЬ
# =========================

class ReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Заявка принята", ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Заявка отклонена", ephemeral=True)


# =========================
# COG
# =========================

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(sender_worker(bot))

    @app_commands.command(name="заявка", description="Создать сообщение с кнопкой заявки")
    async def application(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📨 Подача заявки",
            description="Нажмите кнопку ниже, чтобы подать заявку",
            color=0xfe8b29
        )

        await interaction.response.send_message(embed=embed, view=ApplyView())


async def setup(bot):
    await bot.add_cog(Applications(bot))
