"""
Anti-Raid Modülü (PostgreSQL versiyonu)
"""
import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import config
from database.db import get_pool
from modules import logger

_join_cache: dict[int, list[datetime]] = defaultdict(list)
_raid_mode: dict[int, bool] = {}
_heat_cache: dict[int, dict[int, list[datetime]]] = defaultdict(lambda: defaultdict(list))
_repeat_cache: dict[int, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _calc_risk_score(member: discord.Member) -> int:
    score = 0
    age = (_now() - member.created_at).days
    if age < 1:   score += 50
    elif age < 7: score += 30
    elif age < 30:score += 15
    if not member.avatar: score += 20
    if len(member.mutual_guilds) < 2: score += 10
    if sum(c.isdigit() for c in member.name) >= 4: score += 10
    return score


async def _set_raid_mode(guild: discord.Guild, active: bool) -> None:
    _raid_mode[guild.id] = active
    pool = await get_pool()
    embed = logger.raid_alert(guild, config.RAID_JOIN_COUNT, config.RAID_WINDOW_SEC) if active else logger.raid_off(guild)
    await logger.send_log(guild, pool, embed)
    if active and guild.owner:
        try:
            await guild.owner.send(embed=logger.warning(
                "🚨 Sunucunuz Raid Altında!",
                f"**{guild.name}** sunucusunda raid tespit edildi!\nBot yeni katılımları otomatik kick'liyor."
            ))
        except discord.Forbidden:
            pass


class AntiRaid(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        pool  = await get_pool()

        row = await pool.fetchrow("SELECT whitelist, raid_threshold, raid_window_sec FROM guilds WHERE guild_id=$1", guild.id)
        if row and member.id in (row["whitelist"] or []):
            return

        # Raid modu aktifse direkt kick
        if _raid_mode.get(guild.id):
            try:
                await member.kick(reason="🚨 Raid modu aktif — otomatik kick")
                await logger.send_log(guild, pool, logger.warning("Raid Mode: Otomatik Kick", f"{member.mention} kick'lendi."))
            except discord.Forbidden:
                pass
            return

        # Hız tespiti
        now = _now()
        threshold = row["raid_threshold"] if row else config.RAID_JOIN_COUNT
        window    = row["raid_window_sec"] if row else config.RAID_WINDOW_SEC
        cache = _join_cache[guild.id]
        cache[:] = [t for t in cache if (now - t).total_seconds() < window]
        cache.append(now)
        if len(cache) >= threshold:
            await _set_raid_mode(guild, True)
            self.bot.loop.call_later(60, lambda: self.bot.loop.create_task(_set_raid_mode(guild, False)))

        # Risk skoru
        score = _calc_risk_score(member)
        if score >= config.RISK_KICK_SCORE:
            try:
                await member.kick(reason=f"⚠️ Yüksek risk skoru ({score}/100)")
                await logger.send_log(guild, pool, logger.risk_kick_embed(member, score))
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        guild  = message.guild
        author = message.author
        now    = _now()
        pool   = await get_pool()

        row = await pool.fetchrow("SELECT whitelist FROM guilds WHERE guild_id=$1", guild.id)
        if row and author.id in (row["whitelist"] or []):
            return

        # Hız spam
        heat = _heat_cache[guild.id][author.id]
        heat[:] = [t for t in heat if (now - t).total_seconds() < config.HEAT_MSG_WINDOW]
        heat.append(now)
        if len(heat) >= config.HEAT_MSG_COUNT:
            await self._timeout(author, guild, pool, config.HEAT_TIMEOUT_MIN,
                                f"⚡ Hız spam — {config.HEAT_MSG_COUNT} mesaj/{config.HEAT_MSG_WINDOW}sn")
            _heat_cache[guild.id][author.id].clear()
            return

        # Tekrar spam
        reps = _repeat_cache[guild.id][author.id]
        reps.append(message.content)
        if len(reps) > 5: reps.pop(0)
        if len(reps) >= 3 and len(set(reps[-3:])) == 1 and reps[-1].strip():
            await self._timeout(author, guild, pool, 5, "🔁 Tekrar mesaj spam")
            _repeat_cache[guild.id][author.id].clear()

    async def _timeout(self, member: discord.Member, guild: discord.Guild, pool, mins: int, reason: str):
        try:
            await member.timeout(discord.utils.utcnow() + timedelta(minutes=mins), reason=reason)
            await logger.send_log(guild, pool, logger.warning(
                "Otomatik Timeout", f"{member.mention} `{mins}` dakika timeout.\n**Sebep:** {reason}"))
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AntiRaid(bot))
