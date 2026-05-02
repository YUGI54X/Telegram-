import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413954282:AAFefAG3CE19kiA1po7Ha5muTudZ1oOrnQA"
OWNER_ID = "5868896814"

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🐬", callback_data="P"), InlineKeyboardButton("TikTok 🕰️", callback_data="P")],
        [InlineKeyboardButton("YouTube 🪼", callback_data="P"), InlineKeyboardButton("Instagram 🦋", callback_data="P")],
        [InlineKeyboardButton("X (Twitter) 🐦‍⬛", callback_data="P")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- الأوامر والتعامل مع الرسائل ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"مرحبًابك {update.effective_user.first_name} في بوت ATLAS 🍷\nالبوت يعمل الآن بدون اشتراك إجباري. أرسل الرابط مباشرة للبدء:",
        reply_markup=main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "http" in text:
        await process_video_link(update, context, text)
    else:
        await update.message.reply_text("أرسل رابط الفيديو المباشر لتحميله 📥")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "P":
        await query.message.reply_text("أرسل رابط الفيديو الآن 🔗")
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        # تعديل الرسالة لإبلاغ المستخدم ببدء التحميل
        await query.edit_message_text("📥 جاري التحميل والمعالجة... انتظر قليلاً.")
        await download_video(query, context, url, f_id)

# --- منطق التحميل ---
async def process_video_link(update, context, url):
    msg = await update.message.reply_text("⏳ جاري استخراج الجودات المتاحة...")
    try:
        ydl_opts = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            heights_seen = set()
            
            # ترتيب الجودات من الأعلى للأقل
            for f in sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True):
                h = f.get('height')
                if h and h >= 144 and h not in heights_seen:
                    buttons.append([InlineKeyboardButton(f"{h}p", callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)
            
            if not buttons:
                await msg.edit_text("جاري التحميل بأفضل جودة متاحة تلقائياً...")
                await download_video(update, context, url, "best")
            else:
                await msg.edit_text("اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons[:10]))
    except Exception as e:
        await msg.edit_text(f"❌ فشل تحليل الرابط. تأكد من صحته.")

async def download_video(target, context, url, f_id):
    # تحديد ID المحادثة
    chat_id = target.message.chat_id if hasattr(target, 'message') else target.chat_id
    file_name = f"vid_{chat_id}.mp4"
    
    try:
        ydl_opts = {
            'format': f"{f_id}+bestaudio/best",
            'outtmpl': file_name,
            'merge_output_format': 'mp4',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو المحمل
        with open(file_name, 'rb') as video:
            await context.bot.send_video(
                chat_id=chat_id, 
                video=video, 
                caption="✅ تم التحميل بواسطة ATLAS"
            )
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ حدث خطأ أثناء التحميل: {str(e)[:100]}")
    finally:
        # حذف الملف من السيرفر لتوفير المساحة
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت يعمل الآن على Render بدون اشتراك إجباري...")
    app.run_polling()
