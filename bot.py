import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413454282:AAHx_w5JNjCs7watnJaAfR_6bmgxiBmcBYo"
OWNER_ID = "5860896814"

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🐬", callback_data="P"), InlineKeyboardButton("TikTok 🕰️", callback_data="P")],
        [InlineKeyboardButton("YouTube 🪼", callback_data="P"), InlineKeyboardButton("Instagram 🦋", callback_data="P")],
        [InlineKeyboardButton("X (Twitter) 🐦‍⬛", callback_data="P")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quality_label(height):
    if height >= 2160: return "4K / UHD"
    if height >= 1080: return "1080p / FHD"
    if height >= 720: return "720p / HD"
    return f"{height}p"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًابك في بوت ATLAS للتنزيل 🍷\nأرسل رابط الفيديو مباشرة للبدء:",
        reply_markup=main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "http" in text:
        await process_video_link(update, context, text)
    else:
        await update.message.reply_text("أرسل رابط الفيديو المباشر لتحميله 📥")

async def process_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url):
    msg = await update.message.reply_text("⏳ جاري فحص الرابط...")
    try:
        ydl_opts = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            heights_seen = set()
            
            for f in sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True):
                h = f.get('height')
                if h and h >= 144 and h not in heights_seen:
                    label = get_quality_label(h)
                    buttons.append([InlineKeyboardButton(label, callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)
            
            if not buttons:
                await msg.edit_text("جاري التحميل تلقائياً...")
                await download_video(update, context, url, "best")
            else:
                await msg.edit_text("اختر الجودة المناسبة:", reply_markup=InlineKeyboardMarkup(buttons[:10]))
    except:
        await msg.edit_text("❌ لم أتمكن من استخراج الجودات، تأكد من صحة الرابط.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "P":
        await query.message.reply_text("أرسل رابط الفيديو المباشر الآن 🔗")
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.edit_message_text("📥 جاري التحميل والدمج... انتظر قليلاً.")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id if hasattr(target, 'message') else target.chat_id
    file_name = f"video_{chat_id}.mp4"
    ydl_opts = {
        'format': f"{f_id}+bestaudio/best",
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open(file_name, 'rb') as video:
            await context.bot.send_video(chat_id=chat_id, video=video, caption="✅ تم التحميل بواسطة ATLAS")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text="❌ فشل التحميل، قد يكون الفيديو محمي أو الرابط غير مدعوم.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    print("البوت يعمل بدون اشتراك إجباري...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
