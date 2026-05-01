import os
import yt_dlp
import re
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413954282:AAHx_w5JNjCs7watnJaAfR_6bmgxiBmcBYo"
OWNER_ID = "5868896814"

# --- القنوات والحسابات ---
DEFAULT_CHANNELS = [
    {"title": "📢 قناة 1", "url": "https://t.me/rsll61", "verify_id": "@rsll61"},
    {"title": "🤖 بوت Hack696", "url": "https://t.me/Hack696bot", "verify_id": None},
    {"title": "🎵 TikTok", "url": "https://www.tiktok.com/@sou.r31", "verify_id": None},
]

AI_RESPONSES = {
    "من انت": "أنا بوت مخصص لتحميل الفيديوهات من مواقع التواصل الاجتماعي بجودة عالية.",
    "كيف احمل": "أرسل رابط الفيديو المباشر وسأعطيك خيارات الجودة.",
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته! كيف يمكنني مساعدتك؟",
}

WELCOME_MSG = "مرحبًا أنا بوت مايكي،مخصص للتنزيل فيديوهات من مواقع التواصل الاجتماعي، أرسل رابط مباشر أو اختر إحدى المنصات تحت:"

# --- الوظائف المساعدة ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🟦", callback_data="P"), InlineKeyboardButton("TikTok 🖤", callback_data="P")],
        [InlineKeyboardButton("YouTube 🟥", callback_data="P"), InlineKeyboardButton("Instagram 🟪", callback_data="P")],
        [InlineKeyboardButton("X (Twitter) ⬛", callback_data="P")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quality_label(height):
    if height >= 2160: return "4K / UHD"
    if height >= 1440: return "1440p / 2K"
    if height >= 1080: return "1080p / FHD"
    if height >= 720: return "720p / HD"
    return f"{height}p"

async def check_subscription(user_id, bot):
    for channel in DEFAULT_CHANNELS:
        if channel["verify_id"]:
            try:
                member = await bot.get_chat_member(channel["verify_id"], user_id)
                if member.status in ['left', 'kicked']: return False
            except: return False
    return True

# --- الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context.bot):
        buttons = [[InlineKeyboardButton(c["title"], url=c["url"])] for c in DEFAULT_CHANNELS]
        buttons.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="verify")])
        await update.message.reply_text("🚫 يجب عليك الاشتراك في الحسابات التالية أولاً:", reply_markup=InlineKeyboardMarkup(buttons))
        return
    
    await update.message.reply_text(WELCOME_MSG, reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "http" in text:
        if len(text.split()) > 1:
            await update.message.reply_text("رجاءً أرسل رابط بدون أي كلمات معه.")
            return
        await process_video(update, context, text)
    else:
        response = next((v for k, v in AI_RESPONSES.items() if k in text), None)
        if response: await update.message.reply_text(response)

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url):
    msg = await update.message.reply_text("⏳ جاري جلب الجودات المتاحة...")
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            seen = set()
            for f in sorted(formats, key=lambda x: x.get('height', 0), reverse=True):
                h = f.get('height')
                if h and h >= 360 and h not in seen and f.get('vcodec') != 'none':
                    buttons.append([InlineKeyboardButton(get_quality_label(h), callback_data=f"dl|{url}|{f['format_id']}")])
                    seen.add(h)
            await msg.edit_text("اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons[:10]))
    except: await msg.edit_text("❌ فشل التحليل، تأكد من الرابط.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "verify":
        if await check_subscription(query.from_user.id, context.bot):
            await query.message.edit_text(WELCOME_MSG, reply_markup=main_menu())
        else:
            await query.answer("❌ لم تشترك في جميع القنوات بعد!", show_alert=True)
            
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.message.edit_text("📥 جاري التحميل والمعالجة...")
        await download_and_send(query, context, url, f_id)

async def download_and_send(target, context, url, f_id):
    chat_id = target.message.chat_id
    file_name = f"vid_{chat_id}.mp4"
    ydl_opts = {
        'format': f"{f_id}+bestaudio/best",
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await context.bot.send_video(chat_id=chat_id, video=open(file_name, 'rb'), caption="تم التحميل بنجاح ✅")
        os.remove(file_name)
        await context.bot.send_message(chat_id=chat_id, text=WELCOME_MSG, reply_markup=main_menu())
    except: await context.bot.send_message(chat_id=chat_id, text="❌ خطأ في التحميل.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
