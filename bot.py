import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413954282:AAHx_w5JNjCs7watnJaAfR_6bmgxiBmcBYo"

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook", callback_data="PLAT"), InlineKeyboardButton("TikTok", callback_data="PLAT")],
        [InlineKeyboardButton("YouTube", callback_data="PLAT"), InlineKeyboardButton("Instagram", callback_data="PLAT")],
        [InlineKeyboardButton("X (Twitter)", callback_data="PLAT")]
    ]
    return InlineKeyboardMarkup(keyboard)

WELCOME_MSG = "مرحبًا أنا بوت مخصص للتنزيل فيديوهات من مواقع التواصل الاجتماعي، أرسل رابط مباشر أو اختر إحدى المنصات تحت:"

# --- الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG, reply_markup=main_menu())

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("الرجاء إرسال رابط صحيح 🔗")
        return

    msg = await update.message.reply_text("⏳ جاري جلب الجودات المتاحة...")

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            buttons = []
            # جلب جودات الفيديو المختلفة (بدون تكرار)
            heights = set()
            for f in formats:
                h = f.get('height')
                if h and h not in heights and f.get('vcodec') != 'none':
                    heights.add(h)
                    buttons.append([InlineKeyboardButton(f"🎬 {h}p", callback_data=f"dl|{url}|{f['format_id']}")])
            
            if not buttons:
                await msg.edit_text("لم يتم العثور على جودات مختلفة، جاري التحميل بأفضل جودة...")
                await download_video(update, context, url, "best")
            else:
                await msg.edit_text("اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons[:8]))
    except Exception as e:
        await msg.edit_text(f"❌ خطأ في الرابط: {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "PLAT":
        await query.message.reply_text("أرسل رابط الفيديو الآن 🔗")
        return

    if query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.message.edit_text("📥 جاري التحميل... انتظر لحظة")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    file_name = f"video_{target.from_user.id}.mp4"
    ydl_opts = {
        'format': f"{f_id}+bestaudio/best",
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو
        chat_id = target.message.chat_id if hasattr(target, 'message') else target.chat_id
        await context.bot.send_video(chat_id=chat_id, video=open(file_name, 'rb'), caption="تم التحميل بنجاح ✅")
        
        # إرسال الرسالة الترحيبية مجدداً
        await context.bot.send_message(chat_id=chat_id, text=WELCOME_MSG, reply_markup=main_menu())
        
        os.remove(file_name) # حذف الملف لتوفير مساحة
    except Exception as e:
        await context.bot.send_message(chat_id=target.from_user.id, text="❌ فشل في معالجة الفيديو.")

# --- التشغيل ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()
