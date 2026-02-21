"""
Rakuji Security Bot — Ana Giriş Noktası
"""
import asyncio
import discord
from discord.ext import commands

import config
from database.db import init_db

# ─── Intents ────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members       = True   # Anti-raid için üye katılım olayları
intents.message_content = True  # Heat algo için mesaj içeriği
intents.moderation    = True   # Timeout yetkisi


# ─── Bot ────────────────────────────────────────────────────────
class RakujiBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",   # Fallback prefix (slash komutlar ana)
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        # Veritabanı başlat
        await init_db()
        print("✅ Veritabanı bağlantısı kuruldu.")

        # Cog'ları yükle
        cogs = [
            # Güvenlik modülleri
            "modules.anti_raid",
            "modules.anti_nuke",
            "modules.quarantine",
            "modules.panic_mode",
            "modules.filters",
            # Slash komutlar
            "commands.setup",
            "commands.security",
            "commands.moderation",
            "commands.stats",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"  ✔ {cog} yüklendi")
            except Exception as e:
                print(f"  ✘ {cog} yüklenemedi: {e}")

        # Slash komutları Discord'a kaydet (global)
        synced = await self.tree.sync()
        print(f"✅ {len(synced)} slash komutu senkronize edildi.")

    async def on_ready(self) -> None:
        print(f"\n{'─'*40}")
        print(f"  {config.BOT_EMOJI}  {config.BOT_NAME} v{config.BOT_VERSION}")
        print(f"  Bot: {self.user} ({self.user.id})")
        print(f"  Sunucu sayısı: {len(self.guilds)}")
        print(f"{'─'*40}\n")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"🛡️ {len(self.guilds)} sunucuyu koruyorum",
            )
        )

    async def on_command_error(self, ctx, error) -> None:
        pass  # Slash komutlar kullandığımız için prefix hataları görmezden gel


# ─── Çalıştır ───────────────────────────────────────────────────
async def main():
    bot = RakujiBot()
    async with bot:
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
