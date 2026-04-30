import os
import re
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات (استبدلها بمعلوماتك) ---
TOKEN = "8413954282:AAFLK9JkREO_F0bNwAZx1SrdXIIaiNvtYnA"
CHANNEL_ID = "@your_channel"  # معرف قناتك
WELCOME_TEXT = "مرحباً بك! أنا بوت تنزيل الفيديوهات بجودة عالية 1080 ، فقط ارسل رابط مباشر أختار تحت المنصة."
URL_RE = re.compile(r'https?://[^\s]+')

# --- لوحة المفاتيح الرئيسية ---
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("YouTube", callback_data="yt"), InlineKeyboardButton("TikTok", callback_data="tt")],
        [InlineKeyboardButton("Facebook", callback_data="fb")],
        [InlineKeyboardButton("Owner / التواصل", url="https://t.me")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- دالة التحقق من الاشتراك ---
async def check_sub(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- أمر البدء ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_sub(user_id, context.bot):
        kb = [[InlineKeyboardButton("📢 اشترك في القناة أولاً", url=f"https://t.me{CHANNEL_ID[1:]}")]]
        kb.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="verify")])
        await update.message.reply_text("🚫 يجب عليك الاشتراك في القناة لاستخدام البوت:", reply_markup=InlineKeyboardMarkup(kb))
        return

    # إذا كان مشتركاً، تظهر الرسالة الترحيبية
    target = update.message if update.message else update.callback_query.message
    await target.reply_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())

# --- معالجة الروابط والتحميل ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not URL_RE.match(url):
        await update.message.reply_text("الرجاء إرسال رابط صحيح 🔗")
        return

    msg = await update.message.reply_text("⏳ جاري معالجة الفيديو... قد يستغرق ذلك دقيقة.")
    
    try:
        # إعدادات yt-dlp للتحميل (سيختار أفضل جودة متاحة تلقائياً)
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True,
            'merge_output_format': 'mp4'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp4') # تحويل التنسيق إذا لزم
        
        # إرسال الفيديو
        await update.message.reply_video(video=open(filename, 'rb'), caption="تم التحميل بجودة عالية ✅")
        os.remove(filename) # حذف الملف لتوفير مساحة في Railway
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}")

# --- تشغيل البوت ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^verify$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت يعمل الآن...")
    app.run_polling()
