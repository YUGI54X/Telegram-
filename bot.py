import os
import logging
import yt_dlp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- إعداد Flask للعمل في الخلفية (Keep Alive) ---
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "I am alive"

def run_flask():
    # سيحاول Flask العمل على المنفذ المخصص من المنصة أو 8080 افتراضياً
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- إعدادات البوت ---
TOKEN = "8413954282:AAGuXUlZs9C_F9DY7avn9-d0zjWGPDYlfIg" # ⚠️ ضع التوكن الجديد هنا
OWNER_ID = 8177120280
FREE_LIMIT = 10
PAID_LIMIT = 50
users = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_user_limit(user_id):
    if user_id == OWNER_ID:
        return 999999
    return users.get(user_id, FREE_LIMIT)

def decrease_limit(user_id):
    if user_id != OWNER_ID:
        current = users.get(user_id, FREE_LIMIT)
        users[user_id] = max(0, current - 1)

# --- دوال المعالجة ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    keyboard = [
        [InlineKeyboardButton("يوتيوب 📺", callback_data="youtube")],
        [InlineKeyboardButton("إنستغرام 📸", callback_data="instagram")],
        [InlineKeyboardButton("فيسبوك 👤", callback_data="facebook")]
    ]
    await update.message.reply_text(
        f"مرحباً بك! رصيدك الحالي: {get_user_limit(user_id)} فيديو.\nاختر المنصة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def platform_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data
    await query.edit_message_text(f"لقد اخترت {platform.capitalize()}. أرسل رابط الفيديو الآن 🔗")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    link = update.message.text

    if get_user_limit(user_id) <= 0:
        await update.message.reply_text("انتهت محاولاتك ❌\nاشترك بالنجوم للحصول على محاولات إضافية.")
        return

    status_msg = await update.message.reply_text("جاري فحص الرابط... 🔍")

    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            formats = info.get('formats', [])
            
            # فلترة الجودات التي تحتوي على صوت وفيديو معاً
            available = [f for f in formats if f.get('height') and f.get('acodec') != 'none' and f.get('vcodec') != 'none']
            
            buttons = []
            for f in available[:6]: # عرض أول 6 جودات فقط لتجنب كبر حجم القائمة
                res = f.get('height')
                ext = f.get('ext')
                fid = f.get('format_id')
                buttons.append([InlineKeyboardButton(f"{res}p - {ext}", callback_data=f"dl|{fid}|{link}")])

            if not buttons:
                buttons.append([InlineKeyboardButton("أفضل جودة متاحة", callback_data=f"dl|best|{link}")])

            await status_msg.edit_text("اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        await status_msg.edit_text("حدث خطأ: الرابط غير مدعوم أو غير صحيح ❌")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data_split = query.data.split("|")
    format_id = data_split[1]
    link = data_split[2]
    user_id = query.from_user.id
    
    await query.edit_message_text("جاري التحميل والمعالجة... ⏳")
    
    file_path = f"video_{user_id}.mp4"
    ydl_opts = {
        'format': format_id,
        'outtmpl': file_path,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        
        with open(file_path, 'rb') as video_file:
            await query.message.reply_video(video=video_file, caption="تم التحميل بنجاح ✅")
        
        decrease_limit(user_id)
        await query.message.delete()
    except Exception as e:
        await query.message.reply_text(f"فشل التحميل ❌")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    users[user_id] = PAID_LIMIT
    await update.message.reply_text(f"تم تفعيل الخطة المدفوعة! رصيدك: {PAID_LIMIT} فيديو ⭐")

# --- تشغيل البوت ---
if __name__ == '__main__':
    # تشغيل Flask أولاً
    keep_alive()

    # تشغيل بوت تلغرام
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pay", pay))
    application.add_handler(CallbackQueryHandler(platform_button, pattern="^(youtube|instagram|facebook)$"))
    application.add_handler(CallbackQueryHandler(download_video, pattern=r"^dl\|"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("تم تشغيل Flask والبوت بنجاح...")
    application.run_polling()
