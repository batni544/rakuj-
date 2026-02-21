"""
Setup Slash Commands (PostgreSQL versiyonu)
"""
import discord
from discord import app_commands
from discord.ext import commands

from database.db import get_pool
from modules import logger


class Setup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    setup_group = app_commands.Group(name="setup", description="⚙️ Bot ayarları")

    @setup_group.command(name="log-channel", description="📋 Log kanalını ayarla")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="Log kanalı")
    async def set_log(self, interaction: discord.Interaction, channel: discord.TextChannel):
        pool = await get_pool()
        await pool.execute(
            "INSERT INTO guilds (guild_id, log_channel_id) VALUES ($1,$2) "
            "ON CONFLICT (guild_id) DO UPDATE SET log_channel_id=$2",
            interaction.guild_id, channel.id)
        await interaction.response.send_message(embed=logger.success(
            "Log Kanalı Ayarlandı", f"Loglar {channel.mention} kanalına gönderilecek."), ephemeral=True)

    @setup_group.command(name="raid-threshold", description="⚡ Anti-raid eşiğini ayarla")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(count="Kaç kişi? (min 2)", seconds="Kaç saniyede? (min 3)")
    async def set_raid(self, interaction: discord.Interaction, count: int, seconds: int):
        if count < 2 or seconds < 3:
            return await interaction.response.send_message(
                embed=logger.error("Geçersiz", "Kişi ≥2, süre ≥3 olmalı."), ephemeral=True)
        pool = await get_pool()
        await pool.execute(
            "INSERT INTO guilds (guild_id, raid_threshold, raid_window_sec) VALUES ($1,$2,$3) "
            "ON CONFLICT (guild_id) DO UPDATE SET raid_threshold=$2, raid_window_sec=$3",
            interaction.guild_id, count, seconds)
        await interaction.response.send_message(embed=logger.success(
            "Raid Eşiği Güncellendi",
            f"`{seconds}` saniyede `{count}` kişi → raid modu başlar."), ephemeral=True)

    @setup_group.command(name="nuke-limits", description="💣 Anti-nuke limitlerini ayarla")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel_delete="Kanal silme", role_delete="Rol silme",
                           ban_count="Ban", kick_count="Kick", window_sec="Süre (sn)")
    async def set_nuke(self, interaction: discord.Interaction,
                       channel_delete: int = 3, role_delete: int = 3,
                       ban_count: int = 5, kick_count: int = 5, window_sec: int = 10):
        pool = await get_pool()
        await pool.execute(
            "INSERT INTO anti_nuke_config (guild_id,channel_delete,role_delete,ban_count,kick_count,window_sec) "
            "VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT (guild_id) DO UPDATE SET "
            "channel_delete=$2, role_delete=$3, ban_count=$4, kick_count=$5, window_sec=$6",
            interaction.guild_id, channel_delete, role_delete, ban_count, kick_count, window_sec)
        await interaction.response.send_message(embed=logger.success(
            "Nuke Limitleri Güncellendi", "",
            **{"🗑️ Kanal Silme": f"`{channel_delete}`/`{window_sec}sn`",
               "🏷️ Rol Silme": f"`{role_delete}`/`{window_sec}sn`",
               "🔨 Ban": f"`{ban_count}`/`{window_sec}sn`",
               "👟 Kick": f"`{kick_count}`/`{window_sec}sn`"}), ephemeral=True)

    whitelist_group = app_commands.Group(name="whitelist", description="✅ Whitelist", parent=setup_group)

    @whitelist_group.command(name="add", description="Whitelist'e ekle")
    @app_commands.default_permissions(administrator=True)
    async def wl_add(self, interaction: discord.Interaction, user: discord.Member):
        pool = await get_pool()
        await pool.execute(
            "INSERT INTO guilds (guild_id, whitelist) VALUES ($1, ARRAY[$2::BIGINT]) "
            "ON CONFLICT (guild_id) DO UPDATE SET whitelist = array_append(guilds.whitelist, $2) "
            "WHERE NOT (guilds.whitelist @> ARRAY[$2::BIGINT])",
            interaction.guild_id, user.id)
        await interaction.response.send_message(embed=logger.success(
            "Whitelist'e Eklendi", f"{user.mention} güvenlik kontrollerinden muaf."), ephemeral=True)

    @whitelist_group.command(name="remove", description="Whitelist'ten çıkar")
    @app_commands.default_permissions(administrator=True)
    async def wl_remove(self, interaction: discord.Interaction, user: discord.Member):
        pool = await get_pool()
        await pool.execute(
            "UPDATE guilds SET whitelist = array_remove(whitelist, $2) WHERE guild_id=$1",
            interaction.guild_id, user.id)
        await interaction.response.send_message(embed=logger.success(
            "Whitelist'ten Çıkarıldı", f"{user.mention} artık whitelist'te değil."), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Setup(bot))
