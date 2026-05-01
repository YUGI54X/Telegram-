import os
import yt_dlp
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413954282:AAHx_w5JNjCs7watnJaAfR_6bmgxiBmcBYo"
OWNER_ID = "5868896814"

# --- قاموس الرد الآلي (للأسئلة البسيطة) ---
AI_RESPONSES = {
    "من انت": "أنا بوت مخصص لتحميل الفيديوهات من مواقع التواصل الاجتماعي بجودة عالية.",
    "كيف احمل": "فقط أرسل رابط الفيديو المباشر وسأعطيك خيارات الجودة المتاحة.",
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته! كيف يمكنني مساعدتك؟",
    "شكرا": "العفو! أنا هنا لخدمتك دائماً.",
}

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🟦", callback_data="P"), InlineKeyboardButton("TikTok 🖤", callback_data="P")],
        [InlineKeyboardButton("YouTube 🟥", callback_data="P"), InlineKeyboardButton("Instagram 🟪", callback_data="P")],
        [InlineKeyboardButton("X (Twitter) ⬛", callback_data="P")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- دالة تسمية الجودة ---
def get_quality_label(height):
    if height >= 2160: return "4K / UHD"
    if height >= 1440: return "1440p / 2K"
    if height >= 1080: return "1080p / FHD"
    if height >= 720: return "720p / HD"
    return f"{height}p"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا أنا بوت مخصص للتنزيل فيديوهات من مواقع التواصل الاجتماعي، أرسل رابط مباشر أو اختر إحدى المنصات تحت:", reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # 1. التحقق إذا كان الرابط يحتوي على كلمات أخرى
    if "http" in text:
        # إذا كان النص يحتوي على أكثر من مجرد الرابط
        if len(text.split()) > 1:
            await update.message.reply_text("رجاءً أرسل رابط بدون أي كلمات معه.")
            return
        
        # إذا كان الرابط صحيحاً ومفرداً، نبدأ المعالجة
        await process_video_link(update, context, text)
    
    # 2. الرد على الأسئلة (نظام AI بسيط)
    else:
        response = next((v for k, v in AI_RESPONSES.items() if k in text), None)
        if response:
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("عذراً، لم أفهمك. هل تريد تحميل فيديو؟ أرسل الرابط مباشرة.")

async def process_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url):
    msg = await update.message.reply_text("⏳ جاري جلب الجودات المتاحة...")
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            buttons = []
            heights_seen = set()
            # ترتيب الجودات من الأعلى للأقل
            for f in sorted(formats, key=lambda x: x.get('height', 0), reverse=True):
                h = f.get('height')
                if h and h >= 360 and h not in heights_seen and f.get('vcodec') != 'none':
                    label = get_quality_label(h)
                    buttons.append([InlineKeyboardButton(label, callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)
            
            if not buttons:
                await msg.edit_text("جاري التحميل بأفضل جودة تلقائياً...")
                await download_video(update, context, url, "best")
            else:
                await msg.edit_text("اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons[:10]))
    except:
        await msg.edit_text("❌ فشل تحليل الرابط. تأكد من أن الفيديو عام.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "P":
        await query.message.reply_text("أرسل رابط الفيديو المباشر الآن 🔗")
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.message.edit_text("📥 جاري تحميل الفيديو ومعالجته...")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    chat_id = target.message.chat_id if hasattr(target, 'message') else target.chat_id
    file_name = f"video_{chat_id}.mp4"
    ydl_opts = {
        'format': f"{f_id}+bestaudio/best",
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await context.bot.send_video(chat_id=chat_id, video=open(file_name, 'rb'), caption="تم التحميل بنجاح ✅")
        os.remove(file_name)
        await context.bot.send_message(chat_id=chat_id, text="هل تريد تحميل شيء آخر؟ أرسل الرابط أو اختر منصة:", reply_markup=main_menu())
    except:
        await context.bot.send_message(chat_id=chat_id, text="❌ حدث خطأ أثناء التحميل.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
