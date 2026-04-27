import discord
from discord.ext import commands
import json
import os

LINK_FILE = "links.json"

# =========================
# 💾 LOAD / SAVE
# =========================

def load_links():
    if not os.path.exists(LINK_FILE):
        return {}
    with open(LINK_FILE, "r") as f:
        return json.load(f)

def save_links(data):
    with open(LINK_FILE, "w") as f:
        json.dump(data, f, indent=4)

links = load_links()

# =========================
# ⚙️ COG
# =========================

class LinkSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 🔗 LINK
    # =========================
    @commands.hybrid_command(name="link", description="Привязать Minecraft аккаунт")
    async def link(self, ctx, nickname: str):

        user_id = str(ctx.author.id)

        # уже привязан
        if user_id in links:
            await ctx.send("❌ У тебя уже привязан аккаунт")
            return

        # ник уже занят
        if nickname in links.values():
            await ctx.send("❌ Этот ник уже привязан")
            return

        links[user_id] = nickname
        save_links(links)

        await ctx.send(f"✅ Аккаунт привязан: **{nickname}**")

    # =========================
    # 🔓 UNLINK
    # =========================
    @commands.hybrid_command(name="unlink", description="Отвязать аккаунт")
    async def unlink(self, ctx):

        user_id = str(ctx.author.id)

        if user_id not in links:
            await ctx.send("❌ У тебя нет привязки")
            return

        nickname = links[user_id]
        del links[user_id]
        save_links(links)

        await ctx.send(f"🔓 Отвязано: **{nickname}**")

    # =========================
    # 📊 ПРОВЕРКА
    # =========================
    @commands.hybrid_command(name="whoami", description="Мой Minecraft аккаунт")
    async def whoami(self, ctx):

        user_id = str(ctx.author.id)

        if user_id not in links:
            await ctx.send("❌ Нет привязки")
            return

        await ctx.send(f"🎮 Ты привязан к: **{links[user_id]}**")

# =========================
# 🚀 SETUP
# =========================

async def setup(bot):
    await bot.add_cog(LinkSystem(bot))
