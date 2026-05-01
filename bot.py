import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413954282:AAHx_w5JNjCs7watnJaAfR_6bmgxiBmcBYo"
OWNER_ID = "5868896814"

# --- لوحة المفاتيح الرئيسية مع الإيموجي ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🟦", callback_data="PLAT"), InlineKeyboardButton("TikTok 🖤", callback_data="PLAT")],
        [InlineKeyboardButton("YouTube 🟥", callback_data="PLAT"), InlineKeyboardButton("Instagram 🟪", callback_data="PLAT")],
        [InlineKeyboardButton("X (Twitter) ⬛", callback_data="PLAT")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

WELCOME_MSG = "مرحبًابك، أنا بوت مايكي، مخصص للتنزيل فيديوهات من مواقع التواصل الاجتماعي بجودة عالية، أرسل رابط مباشر أو اختر إحدى المنصات تحت:"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG, reply_markup=main_menu())

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("الرجاء إرسال رابط صحيح 🔗")
        return

    msg = await update.message.reply_text("⏳ جاري تحليل الرابط وجلب الجودات...")

    try:
        # إعدادات خاصة لتجاوز حماية انستقرام والمواقع الأخرى
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            buttons = []
            heights = set()
            for f in formats:
                h = f.get('height')
                # تصفية الجودات لضمان وجود فيديو وصوت
                if h and h not in heights and f.get('vcodec') != 'none':
                    heights.add(h)
                    buttons.append([InlineKeyboardButton(f"🎬 {h}p", callback_data=f"dl|{url}|{f['format_id']}")])
            
            if not buttons:
                await msg.edit_text("جاري التحميل بأفضل جودة متاحة تلقائياً...")
                await download_video(update, context, url, "best")
            else:
                await msg.edit_text("اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons[:8]))
    except Exception as e:
        await msg.edit_text("❌ فشل جلب البيانات. تأكد من أن الرابط عام وليس لحساب خاص.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "PLAT":
        await query.message.reply_text("أرسل رابط الفيديو الآن 🔗")
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.message.edit_text("📥 جاري التحميل والمعالجة... قد يستغرق ذلك دقيقة.")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id if hasattr(target, 'message') else target.chat_id
    file_name = f"vid_{chat_id}.mp4"
    
    ydl_opts = {
        'format': f"{f_id}+bestaudio/best",
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
        # إضافة User-Agent لتجنب الحظر من انستقرام
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await context.bot.send_video(chat_id=chat_id, video=open(file_name, 'rb'), caption="تم التحميل بنجاح ✅")
        await context.bot.send_message(chat_id=chat_id, text=WELCOME_MSG, reply_markup=main_menu())
        os.remove(file_name)
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text="❌ حدث خطأ أثناء التحميل. قد يكون الفيديو محميًا أو الرابط غير مدعوم.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()
