import os
import yt_dlp
import g4f
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
import os
from dotenv import load_dotenv

# تحميل البيانات من ملف .env
load_dotenv()

# قراءة التوكن والـ ID
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = os.getenv('OWNER_ID') # سيقوم بقراءة الرقم من الملف


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
    if height >= 1440: return "2K (1440p) 💎"
    if height >= 1080: return "1080p (FHD) ✨"
    if height >= 720: return "720p (HD) ⚡"
    if height >= 480: return "480p (SD) 📱"
    return f"{height}p"

# --- محرك الذكاء الاصطناعي ---
async def ai_response(user_text):
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_35_turbo,
            messages=[{"role": "user", "content": f"أنت بوت ذكي اسمك ATOM. أجب باختصار: {user_text}"}],
        )
        return response
    except:
        return "أنا هنا لمساعدتك! أرسل رابط الفيديو وسأقوم بتحميله فوراً. 🦦"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "مرحباً! أنا ATOM بوت التحميل الذكي 🧠. أرسل رابطاً من أي منصة وسأعرض لك كل الجودات المتاحة."
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "http" in text:
        if len(text.split()) > 1:
            await update.message.reply_text("⚠️ يرجى إرسال الرابط فقط بدون كلام إضافي.")
            return
        await process_video_link(update, context, text)
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        answer = await ai_response(text)
        await update.message.reply_text(answer)

async def process_video_link(update, context, url):
    msg = await update.message.reply_text("⏳ جاري فحص الجودات المتوفرة...")
    ydl_opts = {
        'quiet': True, 
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            heights_seen = set()
            
            # ترتيب من الأعلى للأقل
            available_formats = sorted([f for f in formats if f.get('height')], key=lambda x: x['height'], reverse=True)

            for f in available_formats:
                h = f['height']
                if h >= 360 and h not in heights_seen:
                    label = get_quality_label(h)
                    size = f.get('filesize') or f.get('filesize_approx')
                    if size:
                        label += f" [{round(size / 1024 / 1024, 1)}MB]"
                    
                    buttons.append([InlineKeyboardButton(label, callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)

            # خيار "أعلى جودة تلقائية" لحل مشاكل فيسبوك وتويتر
            buttons.append([InlineKeyboardButton("🚀 تحميل بأعلى جودة متوفرة (تلقائي)", callback_data=f"dl|{url}|bestvideo+bestaudio/best")])

            await msg.edit_text("📺 اختر الجودة المطلوبة للتحميل:", reply_markup=InlineKeyboardMarkup(buttons))
                
    except Exception as e:
        await msg.edit_text("❌ فشل التحليل. قد يكون الفيديو خاصاً أو الرابط غير مدعوم حالياً.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "P":
        await query.message.reply_text("أرسل الرابط المباشر الآن وسأقوم بمعالجته 🔗")
    elif query.data.startswith("dl"):
        data = query.data.split("|")
        url, f_id = data[1], data[2]
        await query.edit_message_text("📥 جاري التحميل والمعالجة... انتظر قليلاً.")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id
    file_name = f"ATOM_{chat_id}.mp4"
    
    ydl_opts = {
        'format': f_id if f_id != "best" else 'bestvideo+bestaudio/best',
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
                    caption="✅ تم التحميل بنجاح بواسطة ATOM الذكي",
                    reply_markup=main_menu()
                )
        else:
            raise Exception("File Error")
            
    except:
        await context.bot.send_message(chat_id=chat_id, text="❌ عذراً، تعذر تحميل الفيديو. حاول اختيار جودة أقل أو رابط آخر.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    print("ATOM AI Bot is Active...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
