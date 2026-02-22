"""
Panic Mode (PostgreSQL versiyonu)
"""
import discord
from discord import ui, app_commands
from discord.ext import commands

from database.db import get_pool
from modules import logger
from config import Color


class PanicView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="✅ Panik Modunu Kapat", style=discord.ButtonStyle.success,
               custom_id="panic_off_btn", emoji="🔓")
    async def panic_off(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                embed=logger.error("Yetkisiz", "Administrator gerekiyor."), ephemeral=True)
        pool = await get_pool()
        await deactivate_panic(interaction.guild, interaction.user, pool)
        button.disabled = True
        button.label = "✅ Panik Modu Kapatıldı"
        await interaction.message.edit(view=self)
        await interaction.response.send_message(
            embed=logger.panic_off_embed(interaction.guild, interaction.user))


async def activate_panic(guild: discord.Guild, executor: discord.Member | None, pool) -> None:
    deny = discord.PermissionOverwrite(send_messages=False, add_reactions=False,
                                        create_public_threads=False, send_messages_in_threads=False)
    for ch in guild.text_channels:
        try:
            await ch.set_permissions(guild.default_role, overwrite=deny, reason="🚨 Panic Mode")
        except (discord.Forbidden, discord.HTTPException):
            pass
    await pool.execute(
        "INSERT INTO guilds (guild_id, panic_mode) VALUES ($1, TRUE) "
        "ON CONFLICT (guild_id) DO UPDATE SET panic_mode=TRUE", guild.id)
    if guild.owner and executor != guild.owner:
        try:
            await guild.owner.send(embed=logger.warning(
                "🚨 Panik Modu Aktif!",
                f"**{guild.name}**\nKim: {executor.mention if executor else 'Sistem'}"))
        except discord.Forbidden:
            pass
    await logger.send_log(guild, pool, logger.panic_on_embed(guild, executor))


async def deactivate_panic(guild: discord.Guild, executor: discord.Member, pool) -> None:
    for ch in guild.text_channels:
        try:
            await ch.set_permissions(guild.default_role, overwrite=None, reason="✅ Panic kapatıldı")
        except (discord.Forbidden, discord.HTTPException):
            pass
    await pool.execute("UPDATE guilds SET panic_mode=FALSE WHERE guild_id=$1", guild.id)
    await logger.send_log(guild, pool, logger.panic_off_embed(guild, executor))


class PanicMode(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.add_view(PanicView())

    async def cog_load(self) -> None:
        pool = await get_pool()
        rows = await pool.fetch("SELECT guild_id FROM guilds WHERE panic_mode=TRUE")
        for row in rows:
            g = self.bot.get_guild(row["guild_id"])
            if g and g.owner:
                try:
                    await g.owner.send(embed=logger.warning(
                        "⚠️ Panik Modu Hâlâ Aktif",
                        f"**{g.name}** — `/unpanic` ile kapatın."))
                except discord.Forbidden:
                    pass

    @app_commands.command(name="panic", description="🚨 Panik modunu aktifleştir")
    @app_commands.default_permissions(administrator=True)
    async def panic_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        pool = await get_pool()
        await activate_panic(interaction.guild, interaction.user, pool)
        await interaction.followup.send(
            embed=logger.panic_on_embed(interaction.guild, interaction.user), view=PanicView())

    @app_commands.command(name="unpanic", description="✅ Panik modunu kapat")
    @app_commands.default_permissions(administrator=True)
    async def unpanic_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        pool = await get_pool()
        await deactivate_panic(interaction.guild, interaction.user, pool)
        await interaction.followup.send(embed=logger.panic_off_embed(interaction.guild, interaction.user))

    @app_commands.command(name="lockdown", description="🔒 Kanalı kilitle")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(channel="Kanal (boş = mevcut kanal)")
    async def lockdown_cmd(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        target = channel or interaction.channel
        try:
            await target.set_permissions(interaction.guild.default_role, send_messages=False)
            await interaction.response.send_message(embed=logger.success("Kilitlendi", f"{target.mention} kilitlendi."))
        except discord.Forbidden:
            await interaction.response.send_message(embed=logger.error("Hata", "Yetki yok."), ephemeral=True)

    @app_commands.command(name="unlockdown", description="🔓 Kilidi kaldır")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(channel="Kanal (boş = mevcut kanal)")
    async def unlockdown_cmd(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        target = channel or interaction.channel
        try:
            await target.set_permissions(interaction.guild.default_role, overwrite=None)
            await interaction.response.send_message(embed=logger.success("Kilit Açıldı", f"{target.mention} açıldı."))
        except discord.Forbidden:
            await interaction.response.send_message(embed=logger.error("Hata", "Yetki yok."), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PanicMode(bot))
