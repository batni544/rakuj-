"""
Karantina Sistemi (PostgreSQL versiyonu)
"""
import discord
from discord.ext import commands

from database.db import get_pool
from modules import logger

QUARANTINE_ROLE_NAME = "🔒 Karantina"


async def _get_or_create_quarantine_role(guild: discord.Guild) -> discord.Role | None:
    role = discord.utils.get(guild.roles, name=QUARANTINE_ROLE_NAME)
    if not role:
        try:
            role = await guild.create_role(name=QUARANTINE_ROLE_NAME,
                                           color=discord.Color.dark_grey(),
                                           reason="🛡️ Karantina rolü oluşturuldu")
        except discord.Forbidden:
            return None
    deny = discord.PermissionOverwrite(send_messages=False, add_reactions=False,
                                        speak=False, connect=False,
                                        create_public_threads=False, send_messages_in_threads=False)
    for channel in guild.channels:
        try:
            await channel.set_permissions(role, overwrite=deny, reason="🛡️ Karantina kısıtlaması")
        except (discord.Forbidden, discord.HTTPException):
            pass
    return role


async def quarantine_user(guild: discord.Guild, target: discord.Member,
                           reason: str, executor: discord.Member | None, pool) -> bool:
    role = await _get_or_create_quarantine_role(guild)
    if not role: return False
    try:
        await target.edit(roles=[role], reason=f"🔒 Karantina: {reason}")
        await pool.execute(
            "INSERT INTO quarantined (guild_id, user_id, reason) VALUES ($1,$2,$3)",
            guild.id, target.id, reason)
        await logger.send_log(guild, pool, logger.quarantine_embed(target, reason, executor))
        return True
    except discord.Forbidden:
        return False


async def unquarantine_user(guild: discord.Guild, target: discord.Member,
                             executor: discord.Member, pool) -> bool:
    role = discord.utils.get(guild.roles, name=QUARANTINE_ROLE_NAME)
    if role and role in target.roles:
        try:
            await target.remove_roles(role, reason=f"🔓 Karantina kaldırıldı — {executor}")
        except discord.Forbidden:
            return False
    await pool.execute(
        "UPDATE quarantined SET active=FALSE WHERE guild_id=$1 AND user_id=$2 AND active=TRUE",
        guild.id, target.id)
    await logger.send_log(guild, pool, logger.unquarantine_embed(target, executor))
    return True


class Quarantine(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        guild = after.guild
        role  = discord.utils.get(guild.roles, name=QUARANTINE_ROLE_NAME)
        if not role: return
        pool = await get_pool()
        row  = await pool.fetchrow(
            "SELECT id FROM quarantined WHERE guild_id=$1 AND user_id=$2 AND active=TRUE",
            guild.id, after.id)
        if not row: return
        if role not in after.roles:
            try:
                await after.add_roles(role, reason="🛡️ Karantina bypass engellendi")
                await logger.send_log(guild, pool, logger.warning(
                    "Karantina Bypass Girişimi",
                    f"{after.mention} karantinayı atlatmaya çalıştı! Rol geri eklendi."))
            except discord.Forbidden:
                pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Quarantine(bot))
