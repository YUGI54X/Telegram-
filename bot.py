import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest

# --- الإعدادات ---
TOKEN = "8413954282:AAENbA2AENPWtowJUkLXDuJR4wvhXxVATSc"
OWNER_ID = "5868896814"
CHANNEL_ID = "@ATLAS_TECH" 

def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🐬", callback_data="P"), InlineKeyboardButton("TikTok 🕰️", callback_data="P")],
        [InlineKeyboardButton("YouTube 🪼", callback_data="P"), InlineKeyboardButton("Instagram 🦋", callback_data="P")],
        [InlineKeyboardButton("X (Twitter) 🐦‍⬛", callback_data="P")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def subscription_menu():
    # إصلاح السلاش المفقود هنا
    url = f"https://t.me{CHANNEL_ID.replace('@','')}"
    keyboard = [
        [InlineKeyboardButton("انضم للقناة أولاً 📢", url=url)],
        [InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="verify_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def is_subscribed(context, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking sub: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_subscribed(context, user_id):
        await update.message.reply_text(f"مرحبًابك في بوت ATLAS 🍷\nأرسل الرابط مباشرة:", reply_markup=main_menu())
    else:
        await update.message.reply_text("يجب الاشتراك في القناة أولاً لاستخدام البوت.", reply_markup=subscription_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscribed(context, user_id):
        await update.message.reply_text("اشترك أولاً ثم اضغط تحقق ⚠️", reply_markup=subscription_menu())
        return
    text = update.message.text.strip()
    if "http" in text:
        await process_video_link(update, context, text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data == "verify_sub":
        if await is_subscribed(context, user_id):
            await query.message.edit_text("تم التحقق! أرسل الرابط الآن.", reply_markup=main_menu())
        else:
            await query.message.reply_text("❌ لم تشترك بعد.")
    elif query.data == "P":
        await query.message.reply_text("أرسل رابط الفيديو الآن 🔗")
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.message.reply_text("📥 جاري التحميل...")
        await download_video(query, context, url, f_id)

async def process_video_link(update, context, url):
    msg = await update.message.reply_text("⏳ جاري جلب الجودات...")
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            heights_seen = set()
            for f in sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True):
                h = f.get('height')
                if h and h >= 144 and h not in heights_seen:
                    buttons.append([InlineKeyboardButton(f"{h}p", callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)
            await msg.edit_text("اختر الجودة:", reply_markup=InlineKeyboardMarkup(buttons[:10]))
    except Exception as e:
        await msg.edit_text(f"❌ فشل الرابط: {str(e)[:50]}")

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id
    file_name = f"vid_{chat_id}.mp4"
    try:
        # تأكد من تثبيت FFmpeg على Render كما شرحنا سابقاً
        ydl_opts = {
            'format': f"{f_id}+bestaudio/best",
            'outtmpl': file_name,
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await context.bot.send_video(chat_id=chat_id, video=open(file_name, 'rb'))
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ خطأ تحميل: {e}")
    finally:
        if os.path.exists(file_name): os.remove(file_name)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت بدأ العمل...")
    app.run_polling()
