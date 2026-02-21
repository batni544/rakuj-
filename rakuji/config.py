import os
from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.getenv("DISCORD_TOKEN", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# ─── Renk Paleti ────────────────────────────────────────────────
class Color:
    SUCCESS    = 0x2ECC71   # Yeşil
    ERROR      = 0xE74C3C   # Kırmızı
    WARNING    = 0xF39C12   # Turuncu
    INFO       = 0x5865F2   # Discord moru
    DANGER     = 0xFF0000   # Panic kırmızısı
    QUARANTINE = 0x9B59B6   # Mor
    RAID       = 0xFF6600   # Turuncu-kırmızı
    NUKE       = 0xFF2222   # Parlak kırmızı
    MOD        = 0x1ABC9C   # Teal
    LOG        = 0x2C2F33   # Koyu gri

# ─── Anti-Raid Varsayılan Ayarlar ───────────────────────────────
RAID_JOIN_COUNT    = 5    # Kaç kişi katılırsa raid sayılır
RAID_WINDOW_SEC    = 10   # Kaç saniye içinde
HEAT_MSG_COUNT     = 5    # Kaç mesaj → timeout
HEAT_MSG_WINDOW    = 5    # Kaç saniyede
HEAT_TIMEOUT_MIN   = 10   # Timeout süresi (dakika)
RISK_KICK_SCORE    = 60   # Bu skoru geçen otomatik kick alır
RISK_VERIFY_SCORE  = 40   # Bu skoru geçen doğrulama moduna girer

# ─── Anti-Nuke Varsayılan Limitler ──────────────────────────────
NUKE_CHANNEL_DELETE = 3
NUKE_ROLE_DELETE    = 3
NUKE_BAN_COUNT      = 5
NUKE_KICK_COUNT     = 5
NUKE_WEBHOOK_DELETE = 2
NUKE_WINDOW_SEC     = 10

# ─── Bot Bilgisi ────────────────────────────────────────────────
BOT_NAME    = "Rakuji Security"
BOT_VERSION = "1.0.0"
BOT_EMOJI   = "🛡️"
