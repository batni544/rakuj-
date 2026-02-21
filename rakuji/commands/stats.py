"""
Stats & Log Slash Commands (PostgreSQL versiyonu)
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

from database.db import get_pool
from modules import logger
from config import BOT_NAME, BOT_VERSION, BOT_EMOJI, Color


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._start_time = datetime.now(timezone.utc)

    @app_commands.command(name="stats", description="📊 Bot istatistikleri")
    async def stats(self, interaction: discord.Interaction):
        pool  = await get_pool()
        guild = interaction.guild

        quarantined = await pool.fetchval(
            "SELECT COUNT(*) FROM quarantined WHERE guild_id=$1 AND active=TRUE", guild.id) or 0
        actions = await pool.fetchval(
            "SELECT COUNT(*) FROM action_log WHERE guild_id=$1", guild.id) or 0

        uptime  = datetime.now(timezone.utc) - self._start_time
        hours, r = divmod(int(uptime.total_seconds()), 3600)
        minutes  = r // 60

        e = discord.Embed(title=f"{BOT_EMOJI} {BOT_NAME} — İstatistikler", color=Color.INFO)
        e.add_field(name="🤖 Versiyon",    value=f"`{BOT_VERSION}`", inline=True)
        e.add_field(name="⏱️ Uptime",      value=f"`{hours}s {minutes}dk`", inline=True)
        e.add_field(name="🏓 Gecikme",     value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        e.add_field(name="🔒 Karantinada", value=f"`{quarantined}` kullanıcı", inline=True)
        e.add_field(name="📋 Aksiyon",     value=f"`{actions}` toplam", inline=True)
        e.add_field(name="👥 Üye",         value=f"`{guild.member_count}`", inline=True)
        e.set_thumbnail(url=self.bot.user.display_avatar.url)
        e.set_footer(text=f"{BOT_EMOJI} {BOT_NAME}")
        e.timestamp = datetime.now(timezone.utc)
        await interaction.response.send_message(embed=e)

    @app_commands.command(name="logs", description="📋 Son güvenlik logları")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(amount="Kaç log? (max 10)")
    async def logs(self, interaction: discord.Interaction, amount: int = 5):
        pool = await get_pool()
        rows = await pool.fetch(
            "SELECT action_type, target_id, executor_id, reason, created_at "
            "FROM action_log WHERE guild_id=$1 ORDER BY created_at DESC LIMIT $2",
            interaction.guild_id, min(amount, 10))
        if not rows:
            return await interaction.response.send_message(
                embed=logger.info("Kayıt Yok", "Henüz log yok."), ephemeral=True)
        e = discord.Embed(title=f"📋 Son {min(amount, 10)} Log", color=Color.LOG)
        for r in rows:
            target   = f"<@{r['target_id']}>" if r["target_id"] else "-"
            executor = f"<@{r['executor_id']}>" if r["executor_id"] else "Sistem"
            e.add_field(
                name=f"`{r['action_type'].upper()}` — {str(r['created_at'])[:19]}",
                value=f"🎯 {target} | 👮 {executor}\n📝 {r['reason'] or '-'}",
                inline=False)
        e.set_footer(text=f"{BOT_EMOJI} {BOT_NAME}")
        e.timestamp = datetime.now(timezone.utc)
        await interaction.response.send_message(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Stats(bot))
