"""
Moderasyon Slash Commands (PostgreSQL versiyonu)
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

from database.db import get_pool
from modules import logger
from config import Color


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="warn", description="⚠️ Uyarı ver")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(user="Hedef", reason="Sebep")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        pool = await get_pool()
        row = await pool.fetchrow(
            "SELECT warns FROM users WHERE guild_id=$1 AND user_id=$2",
            interaction.guild_id, user.id)
        total = (row["warns"] if row else 0) + 1
        await pool.execute(
            "INSERT INTO users (guild_id, user_id, warns, last_warn_at, last_warn_reason) "
            "VALUES ($1,$2,1,NOW(),$3) "
            "ON CONFLICT (guild_id,user_id) DO UPDATE SET "
            "warns=users.warns+1, last_warn_at=NOW(), last_warn_reason=$3",
            interaction.guild_id, user.id, reason)
        await pool.execute(
            "INSERT INTO action_log (guild_id,action_type,target_id,executor_id,reason) VALUES ($1,$2,$3,$4,$5)",
            interaction.guild_id, "warn", user.id, interaction.user.id, reason)
        await interaction.response.send_message(
            embed=logger.warn_embed(user, interaction.user, reason, total))
        try:
            await user.send(embed=logger.warning(
                f"Uyarı — {interaction.guild.name}", f"**Sebep:** {reason}\n**Toplam:** {total}"))
        except discord.Forbidden:
            pass

    @app_commands.command(name="warnings", description="📊 Uyarı geçmişi")
    @app_commands.default_permissions(manage_messages=True)
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        pool = await get_pool()
        row = await pool.fetchrow(
            "SELECT warns, last_warn_reason, last_warn_at FROM users WHERE guild_id=$1 AND user_id=$2",
            interaction.guild_id, user.id)
        if not row or not row["warns"]:
            return await interaction.response.send_message(
                embed=logger.info("Temiz Sicil", f"{user.mention} için kayıt yok."), ephemeral=True)
        e = logger.info("Uyarı Geçmişi")
        e.add_field(name="📊 Toplam", value=f"`{row['warns']}`", inline=True)
        e.add_field(name="📅 Son Uyarı", value=str(row["last_warn_at"])[:19] if row["last_warn_at"] else "-", inline=True)
        e.add_field(name="📝 Son Sebep", value=row["last_warn_reason"] or "-", inline=False)
        e.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="kick", description="👟 Kick")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(user="Hedef", reason="Sebep")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Belirtilmedi"):
        pool = await get_pool()
        try:
            await user.kick(reason=reason)
            await interaction.response.send_message(
                embed=logger.mod_action_embed("Kick", user, interaction.user, reason))
            await pool.execute(
                "INSERT INTO action_log (guild_id,action_type,target_id,executor_id,reason) VALUES ($1,$2,$3,$4,$5)",
                interaction.guild_id, "kick", user.id, interaction.user.id, reason)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=logger.error("Hata", "Kick yetkisi yok."), ephemeral=True)

    @app_commands.command(name="ban", description="🔨 Ban")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user="Hedef", reason="Sebep", delete_days="Mesaj silme süresi (0-7)")
    async def ban(self, interaction: discord.Interaction, user: discord.Member,
                  reason: str = "Belirtilmedi", delete_days: int = 1):
        pool = await get_pool()
        try:
            await user.ban(reason=reason, delete_message_days=min(delete_days, 7))
            await interaction.response.send_message(
                embed=logger.mod_action_embed("Ban", user, interaction.user, reason, Color.ERROR))
            await pool.execute(
                "INSERT INTO action_log (guild_id,action_type,target_id,executor_id,reason) VALUES ($1,$2,$3,$4,$5)",
                interaction.guild_id, "ban", user.id, interaction.user.id, reason)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=logger.error("Hata", "Ban yetkisi yok."), ephemeral=True)

    @app_commands.command(name="tempban", description="⏱️ Geçici ban")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user="Hedef", minutes="Süre (dakika)", reason="Sebep")
    async def tempban(self, interaction: discord.Interaction, user: discord.Member,
                      minutes: int, reason: str = "Belirtilmedi"):
        try:
            await user.ban(reason=f"Geçici Ban ({minutes}dk): {reason}")
            await interaction.response.send_message(
                embed=logger.mod_action_embed("Ban", user, interaction.user, reason, Color.ERROR,
                                              {"⏱️ Süre": f"`{minutes} dakika`"}))

            async def _unban():
                import asyncio
                await asyncio.sleep(minutes * 60)
                try:
                    await interaction.guild.unban(user, reason="Geçici ban süresi doldu")
                except Exception:
                    pass

            self.bot.loop.create_task(_unban())
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=logger.error("Hata", "Ban yetkisi yok."), ephemeral=True)

    @app_commands.command(name="purge", description="🗑️ Mesaj temizle")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="Silinecek mesaj (max 100)")
    async def purge(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=min(amount, 100))
        await interaction.followup.send(
            embed=logger.success("Temizlendi", f"`{len(deleted)}` mesaj silindi."), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
