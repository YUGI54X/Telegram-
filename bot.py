import os
import re
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
URL_RE = re.compile(r"https?://\S+")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8413954282:AAFLK9JkREO_F0bNwAZx1SrdXIIaiNvtYnA") # يفضل مسحه ووضعه في Railway Variables
OWNER_ID = int(os.environ.get("TELEGRAM_OWNER_ID", "0"))
OWNER_USERNAME = os.environ.get("TELEGRAM_OWNER_USERNAME", "").strip().lstrip("@")

# تصحيح الروابط بإضافة /
OWNER_CONTACT_URL = f"https://t.me{OWNER_USERNAME}" if OWNER_USERNAME else "https://t.me"

FREE_LIMIT = 25
WELCOME_TEXT = "مرحباً بك 👋 أنا بوت تحميل الفيديوهات. أرسل الرابط مباشرة."

TELEGRAM_VERIFY_CHANNELS = [
    {"username": "@Naru62x", "title": "قناة Naru62x", "url": "https://t.meNaru62x"},
]

users = {}
verified_users = set()

logging.basicConfig(level=logging.INFO)

# --- الدوال ---
async def is_subscribed_telegram(context, user_id):
    if user_id == OWNER_ID: return True
    for ch in TELEGRAM_VERIFY_CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch["username"], user_id)
            if member.status not in ("member", "administrator", "creator"): return False
        except: return False
    return True

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ يوتيوب", callback_data="msg"), InlineKeyboardButton("🎵 تيك توك", callback_data="msg")],
        [InlineKeyboardButton("👤 تواصل مع المالك", url=OWNER_CONTACT_URL)]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscribed_telegram(context, user_id):
        kb = [[InlineKeyboardButton(f"✈️ {ch['title']}", url=ch['url'])] for ch in TELEGRAM_VERIFY_CHANNELS]
        kb.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="verify")])
        await update.message.reply_text("🚫 اشترك أولاً:", reply_markup=InlineKeyboardMarkup(kb))
        return
    await update.message.reply_text(f"{WELCOME_TEXT}", reply_markup=main_menu_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not URL_RE.match(url):
        await update.message.reply_text("الرجاء إرسال رابط صحيح 🔗")
        return

    msg = await update.message.reply_text("⏳ جاري التحميل... قد يستغرق ذلك دقيقة.")
    
    try:
        # إعدادات yt-dlp للتحميل
        ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو
        await update.message.reply_video(video=open('video.mp4', 'rb'))
        os.remove('video.mp4') # حذف الملف بعد الإرسال لتوفير المساحة
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}")

# --- التشغيل ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^verify$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
