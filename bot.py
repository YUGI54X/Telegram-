import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest

# --- الإعدادات ---
TOKEN = "8413954282:AAHYHcu1HM_wyN-iVGd4i-qJZPXiLPY8QGs"
OWNER_ID = "5868896814"
CHANNEL_ID = "@ATLAS_TECH"  # قم بتغييره ليوزر قناتك (يجب أن يكون البوت مشرفاً فيها)

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🐬", callback_data="P"), InlineKeyboardButton("TikTok 🕰️", callback_data="P")],
        [InlineKeyboardButton("YouTube 🪼", callback_data="P"), InlineKeyboardButton("Instagram 🦋", callback_data="P")],
        [InlineKeyboardButton("X (Twitter) 🐦‍⬛", callback_data="P")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- لوحة الاشتراك الإجباري ---
def subscription_menu():
    keyboard = [
        [InlineKeyboardButton("انضم للقناة أولاً 📢", url=f"https://t.me{CHANNEL_ID.replace('@','')}")],
        [InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="verify_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- دالة التحقق من الاشتراك ---
async def is_subscribed(context, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except BadRequest:
        return False
    return False

# --- الأوامر والتعامل مع الرسائل ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_subscribed(context, user_id):
        await update.message.reply_text(
            f"مرحبًابك {update.effective_user.first_name} في بوت ATLAS 🍷\nاختر المنصة أو أرسل الرابط مباشرة:",
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            "عذراً! يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه.",
            reply_markup=subscription_menu()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscribed(context, user_id):
        await update.message.reply_text("يرجى الاشتراك أولاً ثم الضغط على 'تحقق' ⚠️", reply_markup=subscription_menu())
        return

    text = update.message.text.strip()
    if "http" in text:
        await process_video_link(update, context, text)
    else:
        await update.message.reply_text("أرسل رابط الفيديو المباشر لتحميله 📥")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data == "verify_sub":
        if await is_subscribed(context, user_id):
            await query.message.edit_text(
                "تم التحقق بنجاح ✅! يمكنك الآن استخدام البوت.\nاختر المنصة المطلوبة:",
                reply_markup=main_menu()
            )
        else:
            await query.message.reply_text("❌ لم تشترك بعد، يرجى الانضمام للقناة والمحاولة مرة أخرى.")
    
    elif query.data == "P":
        await query.message.reply_text("أرسل رابط الفيديو المباشر الآن 🔗")
    
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.edit_message_text("📥 جاري التحميل والدمج... انتظر قليلاً.")
        await download_video(query, context, url, f_id)

# --- منطق التحميل (نفس الكود السابق) ---
async def process_video_link(update, context, url):
    msg = await update.message.reply_text("⏳ جاري استخراج الجودات...")
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
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
    except:
        await msg.edit_text("❌ خطأ في الرابط.")

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id if hasattr(target, 'message') else target.chat_id
    file_name = f"video_{chat_id}.mp4"
    try:
        with yt_dlp.YoutubeDL({'format': f"{f_id}+bestaudio/best", 'outtmpl': file_name, 'merge_output_format': 'mp4'}) as ydl:
            ydl.download([url])
        await context.bot.send_video(chat_id=chat_id, video=open(file_name, 'rb'), caption="✅ تم بواسطة ATLAS")
    finally:
        if os.path.exists(file_name): os.remove(file_name)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
