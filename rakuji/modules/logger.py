"""
Logger / Embed Builder (PostgreSQL versiyonu)
"""
import discord
from datetime import datetime, timezone
from config import Color, BOT_NAME, BOT_EMOJI


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _footer(embed: discord.Embed) -> discord.Embed:
    embed.timestamp = _now()
    embed.set_footer(text=f"{BOT_EMOJI} {BOT_NAME}")
    return embed


def success(title: str, description: str = "", **fields) -> discord.Embed:
    e = discord.Embed(title=f"✅  {title}", description=description, color=Color.SUCCESS)
    for k, v in fields.items():
        e.add_field(name=k, value=v, inline=False)
    return _footer(e)


def error(title: str, description: str = "", **fields) -> discord.Embed:
    e = discord.Embed(title=f"❌  {title}", description=description, color=Color.ERROR)
    for k, v in fields.items():
        e.add_field(name=k, value=v, inline=False)
    return _footer(e)


def warning(title: str, description: str = "", **fields) -> discord.Embed:
    e = discord.Embed(title=f"⚠️  {title}", description=description, color=Color.WARNING)
    for k, v in fields.items():
        e.add_field(name=k, value=v, inline=False)
    return _footer(e)


def info(title: str, description: str = "", **fields) -> discord.Embed:
    e = discord.Embed(title=f"ℹ️  {title}", description=description, color=Color.INFO)
    for k, v in fields.items():
        e.add_field(name=k, value=v, inline=False)
    return _footer(e)


def raid_alert(guild: discord.Guild, count: int, window: int) -> discord.Embed:
    e = discord.Embed(
        title="🚨  RAID TESPİT EDİLDİ",
        description=f"Son **{window} saniye** içinde **{count}** kullanıcı katıldı!\nRaid koruması aktifleştirildi.",
        color=Color.RAID,
    )
    e.add_field(name="🏠 Sunucu", value=guild.name, inline=True)
    e.add_field(name="⚡ Durum", value="`🔴 RAID MODE AKTİF`", inline=True)
    if guild.icon:
        e.set_thumbnail(url=guild.icon.url)
    return _footer(e)


def raid_off(guild: discord.Guild) -> discord.Embed:
    e = discord.Embed(title="✅  Raid Modu Deaktive Edildi", description="Sunucu normal durumuna döndü.", color=Color.SUCCESS)
    e.add_field(name="🏠 Sunucu", value=guild.name, inline=True)
    return _footer(e)


def nuke_alert(guild: discord.Guild, user: discord.Member, action: str, count: int) -> discord.Embed:
    e = discord.Embed(
        title="💣  NUKE GİRİŞİMİ TESPİT EDİLDİ",
        description="Tehlikeli eylem limiti aşıldı! Kullanıcı karantinaya alındı.",
        color=Color.NUKE,
    )
    e.add_field(name="👤 Kullanıcı", value=f"{user.mention} (`{user.id}`)", inline=False)
    e.add_field(name="⚡ Eylem", value=f"`{action}`", inline=True)
    e.add_field(name="🔢 Sayı", value=f"`{count}`", inline=True)
    e.set_thumbnail(url=user.display_avatar.url)
    return _footer(e)


def quarantine_embed(user: discord.Member, reason: str, executor: discord.Member | None = None) -> discord.Embed:
    e = discord.Embed(title="🔒  Kullanıcı Karantinaya Alındı", color=Color.QUARANTINE)
    e.add_field(name="👤 Kullanıcı", value=f"{user.mention} (`{user.id}`)", inline=False)
    e.add_field(name="📝 Sebep", value=reason, inline=False)
    if executor:
        e.add_field(name="👮 İşlemi Yapan", value=f"{executor.mention}", inline=True)
    e.set_thumbnail(url=user.display_avatar.url)
    return _footer(e)


def unquarantine_embed(user: discord.Member, executor: discord.Member) -> discord.Embed:
    e = discord.Embed(title="🔓  Kullanıcı Karantinadan Çıkarıldı", color=Color.SUCCESS)
    e.add_field(name="👤 Kullanıcı", value=f"{user.mention} (`{user.id}`)", inline=True)
    e.add_field(name="👮 İşlemi Yapan", value=f"{executor.mention}", inline=True)
    e.set_thumbnail(url=user.display_avatar.url)
    return _footer(e)


def panic_on_embed(guild: discord.Guild, executor: discord.Member | None) -> discord.Embed:
    e = discord.Embed(
        title="🚨  PANİK MODU AKTİFLEŞTİRİLDİ",
        description="**Tüm kanallar kilitlendi!**\nTehdit geçtikten sonra butona basarak modu kapatın.",
        color=Color.DANGER,
    )
    if executor:
        e.add_field(name="⚡ Aktifleştiren", value=f"{executor.mention}", inline=True)
    e.add_field(name="🏠 Sunucu", value=guild.name, inline=True)
    if guild.icon:
        e.set_thumbnail(url=guild.icon.url)
    return _footer(e)


def panic_off_embed(guild: discord.Guild, executor: discord.Member) -> discord.Embed:
    e = discord.Embed(title="✅  Panik Modu Kapatıldı", description="Kanallar tekrar açıldı.", color=Color.SUCCESS)
    e.add_field(name="👮 Kapatan", value=f"{executor.mention}", inline=True)
    return _footer(e)


def mod_action_embed(action: str, user, executor: discord.Member, reason: str,
                     color: int = Color.MOD, extra: dict | None = None) -> discord.Embed:
    icons = {"Ban": "🔨", "Kick": "👟", "Uyarı": "⚠️", "Mute": "🔇", "Purge": "🗑️"}
    e = discord.Embed(title=f"{icons.get(action, '🛡️')}  {action}", color=color)
    e.add_field(name="👤 Hedef", value=f"{user.mention} (`{user.id}`)", inline=False)
    e.add_field(name="👮 Yetkili", value=f"{executor.mention}", inline=True)
    e.add_field(name="📝 Sebep", value=reason or "Belirtilmedi", inline=True)
    if extra:
        for k, v in extra.items():
            e.add_field(name=k, value=str(v), inline=True)
    e.set_thumbnail(url=user.display_avatar.url)
    return _footer(e)


def warn_embed(user: discord.Member, executor: discord.Member, reason: str, total_warns: int) -> discord.Embed:
    e = discord.Embed(title="⚠️  Uyarı Verildi", color=Color.WARNING)
    e.add_field(name="👤 Kullanıcı", value=f"{user.mention} (`{user.id}`)", inline=False)
    e.add_field(name="👮 Yetkili", value=executor.mention, inline=True)
    e.add_field(name="📝 Sebep", value=reason, inline=True)
    e.add_field(name="📊 Toplam Uyarı", value=f"`{total_warns}`", inline=True)
    e.set_thumbnail(url=user.display_avatar.url)
    return _footer(e)


def risk_kick_embed(user: discord.Member, score: int) -> discord.Embed:
    e = discord.Embed(title="🚫  Yüksek Riskli Hesap", description="Otomatik kick uygulandı.", color=Color.RAID)
    e.add_field(name="👤 Kullanıcı", value=f"{user.mention} (`{user.id}`)", inline=False)
    e.add_field(name="📊 Risk Skoru", value=f"`{score}/100`", inline=True)
    e.add_field(name="📅 Hesap Yaşı", value=f"`{(discord.utils.utcnow() - user.created_at).days} gün`", inline=True)
    e.set_thumbnail(url=user.display_avatar.url)
    return _footer(e)


async def send_log(guild: discord.Guild, pool, embed: discord.Embed) -> None:
    """Log kanalına embed gönder."""
    row = await pool.fetchrow("SELECT log_channel_id FROM guilds WHERE guild_id=$1", guild.id)
    if not row or not row["log_channel_id"]:
        return
    ch = guild.get_channel(row["log_channel_id"])
    if ch and isinstance(ch, discord.TextChannel):
        try:
            await ch.send(embed=embed)
        except discord.Forbidden:
            pass
