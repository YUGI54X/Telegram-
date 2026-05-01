import os
import yt_dlp
import g4f  # مكتبة الذكاء الاصطناعي المجانية
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- تحميل الإعدادات من ملف .env ---
# بدلاً من load_dotenv() و os.getenv
TOKEN = "8513954282:AAFiyYEYaBGTX5tUQ7-U0KLsfKW6Kdl_2HE"
OWNER_ID = "6868896814"


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
    if height >= 2160: return "4K (2160p - UHD) 🔥"
    if height >= 1080: return "1080p (FHD - Full HD) ✨"
    if height >= 720: return "720p (HD) ⚡"
    if height >= 480: return "480p (SD) 📱"
    return f"{height}p"

# --- محرك الذكاء الاصطناعي ---
async def ai_response(user_text):
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_35_turbo,
            messages=[{"role": "user", "content": f"أنت بوت ذكي اسمك ATOM، خبير في تحميل الفيديوهات وتجيب بذكاء وأناقة. أجب على هذا: {user_text}"}],
        )
        return response
    except:
        return "عذراً، أنا أتعلم حالياً. هل يمكنني مساعدتك برابط فيديو لتحميله؟ 🦦"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحبا بك آنا بوت ATOM الذكي 🧠، لقد تم تصميمي للتنزيل من مواقع التواصل "
        "بجودة تصل إلى 4k. يمكنني أيضاً الإجابة على أسئلتك! أرسل رابطاً أو اسألني شيئاً 👇"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "http" in text:
        if len(text.split()) > 1:
            await update.message.reply_text("⚠️ يرجى إرسال الرابط فقط بدون أي كلمات إضافية.")
            return
        await process_video_link(update, context, text)
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        answer = await ai_response(text)
        await update.message.reply_text(answer, reply_markup=main_menu())

async def process_video_link(update, context, url):
    msg = await update.message.reply_text("⏳ جاري تحليل الرابط بذكاء...")
    try:
        ydl_opts = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            heights_seen = set()
            target_heights = [2160, 1080, 720, 480]
            
            available_formats = sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True)

            for target in target_heights:
                for f in available_formats:
                    h = f.get('height')
                    if h == target and h not in heights_seen:
                        label = get_quality_label(h)
                        buttons.append([InlineKeyboardButton(label, callback_data=f"dl|{url}|{f['format_id']}")])
                        heights_seen.add(h)
                        break

            if not buttons:
                for f in available_formats[:5]:
                    h = f.get('height')
                    if h and h not in heights_seen:
                        buttons.append([InlineKeyboardButton(f"{h}p", callback_data=f"dl|{url}|{f['format_id']}")])
                        heights_seen.add(h)

            if not buttons:
                await msg.edit_text("❌ لم أجد جودات مدعومة، جرب رابطاً آخر.")
            else:
                await msg.edit_text("✅ اختر الجودة التي تفضلها لبدء التنزيل:", reply_markup=InlineKeyboardMarkup(buttons))
    except:
        await msg.edit_text("❌ فشل التحليل. قد يكون الفيديو خاصاً أو الرابط غير صالح.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "P":
        await query.message.reply_text("أرسل الرابط المباشر الآن وسأقوم بمعالجته 🔗")
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.edit_message_text("📥 جاري تحميل الفيديو ودمجه... انتظر قليلاً.")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id
    file_name = f"ATOM_{chat_id}.mp4"
    ydl_opts = {
        'format': f"{f_id}+bestaudio/best",
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open(file_name, 'rb') as video:
            await context.bot.send_video(
                chat_id=chat_id, 
                video=video, 
                caption="✅ تم التحميل بنجاح بواسطة ATOM الذكي",
                reply_markup=main_menu()
            )
    except:
        await context.bot.send_message(chat_id=chat_id, text="❌ حدث خطأ غير متوقع أثناء التحميل.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: BOT_TOKEN not found in .env file!")
    else:
        print("ATOM AI Bot is Active...")
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling()
