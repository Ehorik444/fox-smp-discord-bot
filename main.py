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
bot = commands.Bot(command_prefix="!", intents=intents)


class ApplicationModal(Modal, title="Заявка"):
    name = TextInput(label="Ваше имя", placeholder="Введите имя")
    age = TextInput(label="Ваш возраст", placeholder="Введите возраст")
    reason = TextInput(label="Почему вы хотите?", style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(CHANNEL_ID)

        embed = discord.Embed(title="Новая заявка", color=discord.Color.green())
        embed.add_field(name="Имя", value=self.name.value, inline=False)
        embed.add_field(name="Возраст", value=self.age.value, inline=False)
        embed.add_field(name="Причина", value=self.reason.value, inline=False)
        embed.set_footer(text=f"От: {interaction.user}")

        await channel.send(embed=embed)
        await interaction.response.send_message("Заявка отправлена!", ephemeral=True)


class ApplyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.green)
    async def apply(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ApplicationModal())


@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")


@bot.command()
async def setup(ctx):
    view = ApplyView()
    await ctx.send("Нажмите кнопку ниже, чтобы подать заявку:", view=view)


bot.run(TOKEN)
