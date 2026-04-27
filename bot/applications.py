import discord
from discord.ext import commands
import os
from rcon import run_rcon

APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID", "0"))
ACCEPT_ROLE_ID = int(os.getenv("ACCEPT_ROLE_ID", "0"))

# =========================
# 📩 MODAL (форма заявки)
# =========================

class ApplicationModal(discord.ui.Modal, title="📩 Заявка"):

    nickname = discord.ui.TextInput(label="Ник")
    age = discord.ui.TextInput(label="Возраст")
    source = discord.ui.TextInput(label="Откуда узнал")
    friend = discord.ui.TextInput(label="Ник друга", required=False)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        channel = interaction.guild.get_channel(APPLICATION_CHANNEL_ID)

        embed = discord.Embed(
            title="📩 Новая заявка",
            color=0xfe8b29
        )

        embed.add_field(name="Ник", value=self.nickname.value)
        embed.add_field(name="Возраст", value=self.age.value)
        embed.add_field(name="Источник", value=self.source.value)
        embed.add_field(name="Друг", value=self.friend.value or "Нет")
        embed.add_field(name="О себе", value=self.about.value)

        # сохраняем ID пользователя
        embed.set_footer(text=str(interaction.user.id))

        await channel.send(embed=embed, view=ReviewView())

        await interaction.response.send_message(
            "✅ Заявка отправлена!",
            ephemeral=True
        )

# =========================
# 📩 КНОПКА ПОДАЧИ
# =========================

class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩 Подать заявку",
        style=discord.ButtonStyle.success,
        custom_id="apply_button"
    )
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())

# =========================
# 🧑‍💼 АДМИН ПАНЕЛЬ
# =========================

class ReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # =========================
    # ✅ ПРИНЯТЬ
    # =========================
    @discord.ui.button(
        label="✅ Принять",
        style=discord.ButtonStyle.success,
        custom_id="accept_app"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        try:
            embed = interaction.message.embeds[0]

            user_id = int(embed.footer.text)
            member = interaction.guild.get_member(user_id)

            nickname = embed.fields[0].value

            # 🎮 whitelist
            result = run_rcon(f"whitelist add {nickname}")

            if result is None:
                await interaction.response.send_message("❌ Ошибка RCON", ephemeral=True)
                return

            # 🎭 роль
            role = interaction.guild.get_role(ACCEPT_ROLE_ID)
            if role and member:
                await member.add_roles(role)

            # обновляем embed
            embed.color = 0x00ff00
            embed.title = "✅ Заявка принята"

            await interaction.message.edit(embed=embed, view=None)

            # сообщение игроку
            if member:
                try:
                    await member.send(
                        f"🎉 Ваша заявка принята!\n"
                        f"Вы добавлены в whitelist как: **{nickname}**"
                    )
                except:
                    pass

            await interaction.response.send_message("✅ Принято", ephemeral=True)

        except Exception as e:
            print("ACCEPT ERROR:", e)
            await interaction.response.send_message("❌ Ошибка", ephemeral=True)

    # =========================
    # ❌ ОТКЛОНИТЬ
    # =========================
    @discord.ui.button(
        label="❌ Отклонить",
        style=discord.ButtonStyle.danger,
        custom_id="deny_app"
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):

        try:
            embed = interaction.message.embeds[0]

            user_id = int(embed.footer.text)
            member = interaction.guild.get_member(user_id)

            embed.color = 0xff0000
            embed.title = "❌ Заявка отклонена"

            await interaction.message.edit(embed=embed, view=None)

            if member:
                try:
                    await member.send("❌ Ваша заявка отклонена")
                except:
                    pass

            await interaction.response.send_message("❌ Отклонено", ephemeral=True)

        except Exception as e:
            print("DENY ERROR:", e)
            await interaction.response.send_message("❌ Ошибка", ephemeral=True)

# =========================
# ⚙️ COG
# =========================

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="заявка", description="Создать сообщение с заявкой")
    async def app_panel(self, ctx):

        embed = discord.Embed(
            title="📩 Заявка на сервер",
            description="Нажми кнопку ниже",
            color=0xfe8b29
        )

        await ctx.send(embed=embed, view=ApplicationView())

# =========================
# 🚀 SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Applications(bot))

    # 🔥 чтобы кнопки НЕ умирали
    bot.add_view(ApplicationView())
    bot.add_view(ReviewView())
