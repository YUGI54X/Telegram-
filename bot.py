import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413954282:AAFLK9JkREO_F0bNwAZx1SrdXIIaiNvtYnA"
OWNER_ID = 8177120280
CHANNEL_ID = "@your_channel"  # استبدله بمعرف قناتك للاشتراك الإجباري
FREE_LIMIT = 25
PAID_LIMIT = 50

# تخزين البيانات (يفضل قاعدة بيانات لاحقاً)
users = {}

# --- الوظائف المساعدة ---
async def check_sub(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def get_user_limit(user_id):
    if user_id == OWNER_ID: return 999999
    return users.get(user_id, FREE_LIMIT)

def decrease_limit(user_id):
    if user_id == OWNER_ID: return
    users[user_id] = users.get(user_id, FREE_LIMIT) - 1

# --- الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # التحقق من الاشتراك الإجباري
    if not await check_sub(user_id, context.bot):
        kb = [
            [InlineKeyboardButton("📢 اشترك في القناة أولاً", url=f"https://t.me{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="verify")]
        ]
        await update.message.reply_text("🚫 يجب عليك الاشتراك في القناة لاستخدام البوت:", reply_markup=InlineKeyboardMarkup(kb))
        return

    # الرسالة الترحيبية والأزرار
    welcome_text = "مرحبًا أنا بوت مخصص للتنزيل فيديوهات من مواقع التواصل الاجتماعي، أرسل رابط مباشر أو اختر إحدى المنصات تحت:"
    keyboard = [
        [InlineKeyboardButton("YouTube", callback_data="youtube"), InlineKeyboardButton("TikTok", callback_data="tiktok")],
        [InlineKeyboardButton("Instagram", callback_data="instagram"), InlineKeyboardButton("Facebook", callback_data="facebook")],
        [InlineKeyboardButton("Owner / التواصل 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    link = update.message.text

    if get_user_limit(user_id) <= 0:
        await update.message.reply_text("انتهت محاولاتك المجانية (25) ❌\nاشترك بالنجوم للحصول على 50 محاولة إضافية ⭐")
        return

    await update.message.reply_text("⏳ جاري جلب الجودات المتاحة...")

    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            formats = info.get('formats', [])
            
            buttons = []
            # عرض أفضل 5 جودات متوفرة
            seen_heights = set()
            for f in formats:
                height = f.get("height")
                if height and height not in seen_heights:
                    buttons.append([InlineKeyboardButton(f"{height}p", callback_data=f"dl|{link}|{f['format_id']}")])
                    seen_heights.add(height)
            
            await update.message.reply_text("اختر الجودة المطلوبة للتحميل:", reply_markup=InlineKeyboardMarkup(buttons[:8]))

    except Exception as e:
        await update.message.reply_text("حدث خطأ في الرابط أو المنصة غير مدعومة ❌")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري التحميل... انتظر قليلاً")

    data = query.data.split("|")
    link, format_id = data[1], data[2]
    user_id = query.from_user.id

    file_name = f"video_{user_id}.mp4"
    ydl_opts = {'format': f"{format_id}+bestaudio/best", 'outtmpl': file_name, 'merge_output_format': 'mp4'}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        await query.message.reply_video(video=open(file_name, 'rb'), caption="تم التحميل بواسطة بوتك ✅")
        os.remove(file_name)
        decrease_limit(user_id)
    except:
        await query.message.reply_text("فشل التحميل، جرب جودة أخرى ❌")

# --- التشغيل ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(start, pattern="^verify$"))
app.add_handler(CallbackQueryHandler(download, pattern="^dl"))
# لتجنب تداخل الأزرار مع الروابط
app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("أرسل الرابط الآن 🔗"), pattern="^(youtube|instagram|facebook|tiktok)$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

print("البوت يعمل الآن...")
app.run_polling()
