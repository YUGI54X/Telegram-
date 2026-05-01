import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413954282:AAFiyYEYaBGTX5tUQ7-U0KLsfKW6Kdl_2HE" # استبدله بتوكن جديد دائماً
OWNER_ID = "5868896814"

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🐬", callback_data="PLATFORM"), InlineKeyboardButton("TikTok 🕰️", callback_data="PLATFORM")],
        [InlineKeyboardButton("YouTube 🪼", callback_data="PLATFORM"), InlineKeyboardButton("Instagram 🦋", callback_data="PLATFORM")],
        [InlineKeyboardButton("X (Twitter) 🐦‍⬛", callback_data="PLATFORM")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- دالة تسمية الجودة بناءً على طلبك ---
def get_quality_label(height):
    if height >= 2160: return "4K (2160p - UHD) 🔥"
    if height >= 1080: return "1080p (FHD - Full HD) ✨"
    if height >= 720: return "720p (HD) ⚡"
    if height >= 480: return "480p (SD) 📱"
    return f"{height}p"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحبا بك آنا بوت ATOM، لقد تم تصميمي للتنزيل فيديوهات من مواقع التواصل الأجتماعي "
        "بجودة عالية 4k، فقط أرسل لي رابط أو أختر أزرار تحت وسأقوم بتحميل 📥"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "http" in text:
        # التحقق إذا كان هناك كلمات مع الرابط
        if len(text.split()) > 1:
            await update.message.reply_text("❌ رجاءً أرسل الرابط بمفرده بدون أي كلمات إضافية.")
            return
        await process_video_link(update, context, text)
    else:
        await update.message.reply_text("عذراً، أرسل رابط الفيديو المباشر 🔗 أو اختر منصة من الأسفل:", reply_markup=main_menu())

async def process_video_link(update, context, url):
    msg = await update.message.reply_text("⏳ جاري فحص الرابط واستخراج الجودات...")
    try:
        ydl_opts = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            heights_seen = set()
            
            # ترتيب الجودات المطلوبة (2160, 1080, 720, 480)
            target_heights = [2160, 1080, 720, 480]
            
            # فلترة الجودات المتاحة فعلياً في الفيديو
            for f in sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True):
                h = f.get('height')
                if h in target_heights and h not in heights_seen:
                    label = get_quality_label(h)
                    buttons.append([InlineKeyboardButton(label, callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)
            
            if not buttons:
                # إذا لم يجد الجودات المحددة، يعرض أفضل جودة متاحة
                await msg.edit_text("لم أجد الجودات القياسية، جاري التحميل بأفضل جودة متاحة...")
                await download_video(update, context, url, "best")
            else:
                await msg.edit_text("✅ اختر الجودة المطلوبة للبدء:", reply_markup=InlineKeyboardMarkup(buttons))
                
    except Exception as e:
        await msg.edit_text("❌ فشل تحليل الرابط. تأكد من أن الحساب عام وليس خاصاً.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "PLATFORM":
        await query.message.reply_text("حسناً، أرسل الرابط المباشر للفيديو الآن 🔗")
    
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.edit_message_text("📥 جاري التحميل والمعالجة... قد يستغرق ذلك وقتاً حسب الحجم.")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id if hasattr(target, 'message') else target.chat_id
    file_name = f"ATOM_{chat_id}.mp4"
    
    # إعدادات التحميل الاحترافية للدمج
    ydl_opts = {
        'format': f"{f_id}+bestaudio/best/best",
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو
        with open(file_name, 'rb') as video:
            await context.bot.send_video(
                chat_id=chat_id, 
                video=video, 
                caption="✅ تم التحميل بنجاح بواسطة ATOM\n\nأرسل رابطاً آخر أو اختر منصة:",
                reply_markup=main_menu()
            )
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ حدث خطأ أثناء التحميل: الرابط قد يكون غير مدعوم حالياً.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ATOM Bot is Running...")
    app.run_polling()
