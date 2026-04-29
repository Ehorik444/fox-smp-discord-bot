import discord
from discord import app_commands
from discord.ext import commands
from db import get_guild, update_setting, create_guild


class SaaSPanelView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    # 📜 Логи
    @discord.ui.button(label="📜 Логи", style=discord.ButtonStyle.primary)
    async def logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📜 Логи подключаются к базе данных (готово к расширению)",
            ephemeral=True
        )

    # 🤖 Auto approve toggle
    @discord.ui.button(label="🤖 Auto-Approve", style=discord.ButtonStyle.success)
    async def auto_approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        row = get_guild(self.guild_id)
        new = 0 if row[2] == 1 else 1

        update_setting(self.guild_id, "auto_approve", new)

        await interaction.response.send_message(
            f"🤖 Auto-Approve: {'ON' if new else 'OFF'}",
            ephemeral=True
        )

    # ⛔ Auto ban toggle
    @discord.ui.button(label="⛔ Auto-Ban", style=discord.ButtonStyle.danger)
    async def auto_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        row = get_guild(self.guild_id)
        new = 0 if row[3] == 1 else 1

        update_setting(self.guild_id, "auto_ban", new)

        await interaction.response.send_message(
            f"⛔ Auto-Ban: {'ON' if new else 'OFF'}",
            ephemeral=True
        )

    # ⚙️ Spam limit
    @discord.ui.button(label="⚙️ Spam +1", style=discord.ButtonStyle.secondary)
    async def spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        row = get_guild(self.guild_id)
        new = row[4] + 1

        update_setting(self.guild_id, "spam_limit", new)

        await interaction.response.send_message(
            f"⚙️ Spam limit: {new}",
            ephemeral=True
        )


class SaaSPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel", description="SaaS Admin Panel")
    async def panel(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Нет доступа", ephemeral=True)

        create_guild(interaction.guild.id)

        row = get_guild(interaction.guild.id)

        embed = discord.Embed(
            title="🧠 SaaS Admin Panel",
            description="Управление ботом на уровне сервера",
            color=0x00ff99
        )

        embed.add_field(name="Auto-Approve", value=str(bool(row[2])))
        embed.add_field(name="Auto-Ban", value=str(bool(row[3])))
        embed.add_field(name="Spam Limit", value=str(row[4]))

        view = SaaSPanelView(interaction.guild.id)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SaaSPanel(bot))
