import os
import yt_dlp
import g4f
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
# استبدل التوكن هنا بتوكن جديد من BotFather
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

def get_quality_label(height):
    if height >= 2160: return "4K (2160p) 🔥"
    if height >= 1080: return "1080p (FHD) ✨"
    if height >= 720: return "720p (HD) ⚡"
    if height >= 480: return "480p (SD) 📱"
    return f"{height}p"

# --- محرك الذكاء الاصطناعي ---
async def ai_response(user_text):
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_35_turbo,
            messages=[{"role": "user", "content": f"أنت بوت ذكي اسمك ATOM، خبير في التحميل. أجب باختصار: {user_text}"}],
        )
        return response
    except:
        return "أنا هنا لمساعدتك! أرسل رابط الفيديو وسأقوم بتحميله فوراً. 🦦"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "مرحباً! أنا ATOM بوت التحميل الذكي 🧠. أرسل رابطاً من (YouTube, FB, X, TikTok, IG) وسأقوم بالواجب."
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "http" in text:
        if len(text.split()) > 1:
            await update.message.reply_text("⚠️ يرجى إرسال الرابط فقط.")
            return
        await process_video_link(update, context, text)
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        answer = await ai_response(text)
        await update.message.reply_text(answer)

async def process_video_link(update, context, url):
    msg = await update.message.reply_text("⏳ جاري تحليل الرابط...")
    # إعدادات الاستخراج (بدون تحميل)
    ydl_opts = {
        'quiet': True, 
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            heights_seen = set()
            
            # محاولة جلب الجودات الشائعة
            available_formats = sorted([f for f in formats if f.get('height')], key=lambda x: x['height'], reverse=True)

            for f in available_formats:
                h = f['height']
                if h in [2160, 1080, 720, 480, 360] and h not in heights_seen:
                    label = get_quality_label(h)
                    buttons.append([InlineKeyboardButton(label, callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)

            # إضافة خيار "أفضل جودة" دائماً كخيار احتياطي لفيسبوك وتويتر
            buttons.append([InlineKeyboardButton("أفضل جودة متاحة 🚀 (تلقائي)", callback_data=f"dl|{url}|bestvideo+bestaudio/best")])

            await msg.edit_text("✅ اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons))
                
    except Exception as e:
        print(f"Error: {e}")
        await msg.edit_text("❌ فشل التحليل. تأكد من أن الرابط عام وليس خاصاً.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "P":
        await query.message.reply_text("أرسل الرابط المباشر الآن 🔗")
    elif query.data.startswith("dl"):
        data = query.data.split("|")
        url = data[1]
        f_id = data[2]
        await query.edit_message_text("📥 جاري التحميل والمعالجة... قد يستغرق ذلك دقيقة.")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id
    file_name = f"ATOM_{chat_id}.mp4"
    
    # إعدادات التحميل القوية للمنصات الصعبة
    ydl_opts = {
        'format': f_id if f_id != "best" else 'bestvideo+bestaudio/best',
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'referer': 'https://google.com',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(file_name):
            with open(file_name, 'rb') as video:
                await context.bot.send_video(
                    chat_id=chat_id, 
                    video=video, 
                    caption="✅ تم التحميل بنجاح بواسطة ATOM",
                    reply_markup=main_menu()
                )
        else:
            raise Exception("File not found")
            
    except Exception as e:
        print(f"Download Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ نعتذر، تعذر تحميل هذا الفيديو. قد يكون محمياً أو يتطلب تسجيل دخول.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    print("ATOM AI Bot is running...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
