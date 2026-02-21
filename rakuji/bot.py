"""
Rakuji Security Bot — Ana Giriş Noktası
"""
import asyncio
import os
import discord
from aiohttp import web
from discord.ext import commands

import config
from database.db import init_db

# ─── Keep-Alive HTTP Sunucusu (UptimeRobot için) ────────────────
async def health(request):
    return web.Response(text="🛡️ Rakuji Security Bot — Online")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ HTTP sunucusu ::{port} portunda çalışıyor")

# ─── Intents ────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members        = True
intents.message_content = True
intents.moderation     = True


# ─── Bot ────────────────────────────────────────────────────────
class RakujiBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        await init_db()
        print("✅ Veritabanı bağlantısı kuruldu.")

        cogs = [
            "modules.anti_raid",
            "modules.anti_nuke",
            "modules.quarantine",
            "modules.panic_mode",
            "modules.filters",
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

        synced = await self.tree.sync()
        print(f"✅ {len(synced)} slash komutu senkronize edildi.")

    async def on_ready(self) -> None:
        print(f"\n{'─'*40}")
        print(f"  {config.BOT_EMOJI}  {config.BOT_NAME} v{config.BOT_VERSION}")
        print(f"  Bot: {self.user} ({self.user.id})")
        print(f"  Sunucu sayısı: {len(self.guilds)}")
        print(f"{'─'*40}\n")
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"🛡️ {len(self.guilds)} sunucuyu koruyorum",
        ))

    async def on_command_error(self, ctx, error) -> None:
        pass


# ─── Çalıştır ───────────────────────────────────────────────────
async def main():
    await start_web()           # HTTP sunucusunu başlat
    bot = RakujiBot()
    async with bot:
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
