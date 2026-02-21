"""
Spam / Link / Caps Filtre Modülü (PostgreSQL versiyonu)
"""
import re
import discord
from discord.ext import commands

from database.db import get_pool
from modules import logger

INVITE_REGEX = re.compile(r"(discord\.gg|discord\.com/invite)/\S+", re.IGNORECASE)


class Filters(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        guild  = message.guild
        author = message.author
        pool   = await get_pool()

        row = await pool.fetchrow("SELECT whitelist FROM guilds WHERE guild_id=$1", guild.id)
        if row and author.id in (row["whitelist"] or []):
            return

        content = message.content

        # ── Discord davet linki engelle ──
        if INVITE_REGEX.search(content):
            try:
                await message.delete()
                await author.send(embed=logger.warning(
                    "Davet Linki Engellendi",
                    f"**{guild.name}** sunucusunda Discord davet linkleri paylaşılamaz."))
            except (discord.Forbidden, discord.HTTPException):
                pass
            return

        # ── Aşırı caps (%70+, min 8 harf) ──
        letters = [c for c in content if c.isalpha()]
        if len(letters) >= 8:
            if sum(1 for c in letters if c.isupper()) / len(letters) >= 0.70:
                try:
                    await message.delete()
                    await message.channel.send(
                        embed=logger.warning("Caps Lock", f"{author.mention}, lütfen büyük harf kullanmayın!"),
                        delete_after=5)
                except (discord.Forbidden, discord.HTTPException):
                    pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Filters(bot))
