"""
Security Slash Commands (PostgreSQL versiyonu)
"""
import discord
from discord import app_commands
from discord.ext import commands

from database.db import get_pool
from modules import logger
from modules.quarantine import quarantine_user, unquarantine_user


class Security(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="quarantine", description="🔒 Kullanıcıyı karantinaya al")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(user="Hedef", reason="Sebep")
    async def quarantine_cmd(self, interaction: discord.Interaction,
                              user: discord.Member, reason: str = "Belirtilmedi"):
        await interaction.response.defer(ephemeral=True)
        if user.top_role >= interaction.user.top_role:
            return await interaction.followup.send(embed=logger.error(
                "Yetkisiz", "Kendinizden üst/eşit roldekini karantinaya alamazsınız."), ephemeral=True)
        pool = await get_pool()
        ok = await quarantine_user(interaction.guild, user, reason, interaction.user, pool)
        if ok:
            await interaction.followup.send(embed=logger.quarantine_embed(user, reason, interaction.user))
        else:
            await interaction.followup.send(embed=logger.error(
                "Hata", "Karantina başarısız. Bot yetkilerini kontrol et."), ephemeral=True)

    @app_commands.command(name="unquarantine", description="🔓 Karantinadan çıkar")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(user="Hedef")
    async def unquarantine_cmd(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        pool = await get_pool()
        ok = await unquarantine_user(interaction.guild, user, interaction.user, pool)
        if ok:
            await interaction.followup.send(embed=logger.unquarantine_embed(user, interaction.user))
        else:
            await interaction.followup.send(embed=logger.error(
                "Hata", "Kullanıcı karantinada değil."), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Security(bot))
