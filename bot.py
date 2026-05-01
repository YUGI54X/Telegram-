import os
import yt_dlp
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = "8413954282:AAHx_w5JNjCs7watnJaAfR_6bmgxiBmcBYo"
OWNER_ID = "5868896814"

# --- قاموس الرد الآلي ---
AI_RESPONSES = {
    "من انت": "أنا بوت مخصص لتحميل الفيديوهات من مواقع التواصل الاجتماعي بجودة عالية.",
    "كيف احمل": "فقط أرسل رابط الفيديو المباشر وسأعطيك خيارات الجودة المتاحة.",
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته! كيف يمكنني مساعدتك؟",
    "شكرا": "العفو! أنا هنا لخدمتك دائماً.",
}

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🐬", callback_data="P"), InlineKeyboardButton("TikTok 🕰️", callback_data="P")],
        [InlineKeyboardButton("YouTube 🪼", callback_data="P"), InlineKeyboardButton("Instagram 🦋", callback_data="P")],
        [InlineKeyboardButton("X (Twitter) 🐦‍⬛", callback_data="P")],
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
    await update.message.reply_text(
        "مرحبًابك، أنا بوت ATLAS 🍷\nتم تصميمي للتنزيل من مواقع التواصل، أرسل رابطاً مباشراً أو اختر منصة:",
        reply_markup=main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "http" in text:
        if len(text.split()) > 1:
            await update.message.reply_text("رجاءً أرسل رابطاً وحيداً بدون كلمات إضافية.")
            return
        await process_video_link(update, context, text)
    else:
        response = next((v for k, v in AI_RESPONSES.items() if k in text), None)
        if response:
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("عذراً، لم أفهمك. أرسل رابط الفيديو مباشرة 🦦")

async def process_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url):
    msg = await update.message.reply_text("⏳ جاري استخراج الجودات المتاحة...")
    try:
        # إعدادات الفحص فقط
        ydl_opts = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            buttons = []
            heights_seen = set()
            
            # ترتيب وتصفية الجودات
            for f in sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True):
                h = f.get('height')
                # نختار الصيغ التي تحتوي فيديو وصوت أو فيديو فقط ليتم دمجها لاحقاً
                if h and h >= 144 and h not in heights_seen:
                    label = get_quality_label(h)
                    buttons.append([InlineKeyboardButton(label, callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)
            
            if not buttons:
                await msg.edit_text("لم أتمكن من العثور على جودات محددة، جاري التحميل التلقائي...")
                await download_video(update, context, url, "best")
            else:
                await msg.edit_text("اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons[:10]))
    except Exception as e:
        print(f"Error: {e}")
        await msg.edit_text("❌ فشل تحليل الرابط. تأكد من صحة الرابط أو خصوصية الفيديو.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "P":
        await query.message.reply_text("أرسل رابط الفيديو المباشر الآن 🔗")
    elif query.data.startswith("dl"):
        _, url, f_id = query.data.split("|")
        await query.edit_message_text("📥 جاري تحميل الفيديو ومعالجته... قد يستغرق ذلك دقيقة.")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    # تحديد ID الشات سواء من رسالة أو من زر
    chat_id = target.message.chat_id if hasattr(target, 'message') else target.chat_id
    file_name = f"video_{chat_id}_{f_id}.mp4"
    
    ydl_opts = {
        'format': f"{f_id}+bestaudio/best",
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو
        with open(file_name, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=chat_id, 
                video=video_file, 
                caption="تم التحميل بنجاح ✅ بواسطة ATLAS"
            )
        
        # حذف الملف بعد الإرسال لتوفير المساحة
        if os.path.exists(file_name):
            os.remove(file_name)

    except Exception as e:
        print(f"Download Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ حدث خطأ أثناء التحميل أو الدمج.")
    finally:
        # التأكد من حذف الملف في حال حدوث خطأ
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    print("البوت يعمل الآن...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
