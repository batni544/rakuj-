"""
Anti-Nuke Modülü (PostgreSQL versiyonu)
"""
import discord
from discord.ext import commands
from datetime import datetime, timezone
from collections import defaultdict

import config
from database.db import get_pool
from modules import logger
from modules.quarantine import quarantine_user

def _now(): return datetime.now(timezone.utc)

_action_counts: dict[int, dict[int, dict[str, list[datetime]]]] = defaultdict(
    lambda: defaultdict(lambda: defaultdict(list))
)
ACTION_NAMES = {
    "channel_delete": "Kanal Silme", "role_delete": "Rol Silme",
    "ban": "Toplu Ban", "kick": "Toplu Kick", "webhook_delete": "Webhook Silme",
}


async def _get_limits(guild_id: int) -> dict:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM anti_nuke_config WHERE guild_id=$1", guild_id)
    if row: return dict(row)
    return {"channel_delete": config.NUKE_CHANNEL_DELETE, "role_delete": config.NUKE_ROLE_DELETE,
            "ban_count": config.NUKE_BAN_COUNT, "kick_count": config.NUKE_KICK_COUNT,
            "webhook_delete": config.NUKE_WEBHOOK_DELETE, "window_sec": config.NUKE_WINDOW_SEC}


async def _register(guild: discord.Guild, user_id: int, action: str) -> None:
    pool   = await get_pool()
    now    = _now()
    limits = await _get_limits(guild.id)
    window = limits["window_sec"]

    counter = _action_counts[guild.id][user_id][action]
    counter[:] = [t for t in counter if (now - t).total_seconds() < window]
    counter.append(now)

    key_map = {"channel_delete": "channel_delete", "role_delete": "role_delete",
               "ban": "ban_count", "kick": "kick_count", "webhook_delete": "webhook_delete"}
    limit = limits.get(key_map.get(action, action), 3)

    if len(counter) >= limit:
        member = guild.get_member(user_id)
        if member:
            reason = f"🛡️ Anti-Nuke: {ACTION_NAMES.get(action, action)} limiti ({len(counter)}/{limit})"
            await quarantine_user(guild, member, reason, None, pool)
            await logger.send_log(guild, pool, logger.nuke_alert(guild, member, ACTION_NAMES.get(action, action), len(counter)))
            counter.clear()


class AntiNuke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry) -> None:
        guild = entry.guild
        if not guild: return
        pool = await get_pool()
        row  = await pool.fetchrow("SELECT whitelist FROM guilds WHERE guild_id=$1", guild.id)
        eid  = entry.user_id
        if eid == self.bot.user.id: return
        if row and eid in (row["whitelist"] or []): return

        act = entry.action
        if   act == discord.AuditLogAction.channel_delete: await _register(guild, eid, "channel_delete")
        elif act == discord.AuditLogAction.role_delete:    await _register(guild, eid, "role_delete")
        elif act == discord.AuditLogAction.ban:            await _register(guild, eid, "ban")
        elif act == discord.AuditLogAction.kick:           await _register(guild, eid, "kick")
        elif act == discord.AuditLogAction.webhook_delete: await _register(guild, eid, "webhook_delete")
        elif act == discord.AuditLogAction.role_update:
            target = entry.target
            if isinstance(target, discord.Role) and target.name == "@everyone":
                after = entry.after
                if hasattr(after, "permissions"):
                    p: discord.Permissions = after.permissions
                    if any([p.administrator, p.ban_members, p.kick_members, p.manage_guild]):
                        try:
                            await guild.default_role.edit(permissions=discord.Permissions.none(),
                                                          reason="🛡️ Anti-Nuke: @everyone tehlikeli yetki engellendi")
                        except discord.Forbidden: pass
                        member = guild.get_member(eid)
                        if member:
                            await quarantine_user(guild, member, "🛡️ @everyone tehlikeli yetki girişimi", None, pool)
                            await logger.send_log(guild, pool, logger.nuke_alert(guild, member, "@everyone Perm", 1))
        elif act == discord.AuditLogAction.bot_add:
            member = guild.get_member(eid)
            if member:
                await logger.send_log(guild, pool, logger.warning(
                    "Yeni Bot Eklendi",
                    f"{member.mention} → **{getattr(entry.target,'name','?')}** botu eklendi."))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiNuke(bot))
