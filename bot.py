import os
import json
import yt_dlp
import g4f
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, PreCheckoutQueryHandler

# --- الإعدادات ---
TOKEN = "8413954282:AAFefAG3CE19kiA1po7Ha5muTudZ1oOrnQA"
OWNER_ID = "5868896814"
STARS_PRICE = int(os.getenv('STARS_PRICE', '100'))
FREE_LIMIT = 15
DATA_FILE = "users_data.json"

# --- إدارة البيانات ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Facebook 🐬", callback_data="P"), InlineKeyboardButton("TikTok 🕰️", callback_data="P")],
        [InlineKeyboardButton("YouTube 🪼", callback_data="P"), InlineKeyboardButton("Instagram 🦋", callback_data="P")],
        [InlineKeyboardButton("تواصل مع المالك 👨‍💻", url=f"tg://user?id={OWNER_ID}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quality_label(height):
    if height >= 2160: return "4K (2160p) 🔥"
    if height >= 1080: return "1080p (FHD) ✨"
    if height >= 720: return "720p (HD) ⚡"
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
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"remaining": FREE_LIMIT, "used": 0}
        save_data(data)
    
    welcome_text = (f"مرحباً! أنا ATOM بوت التحميل الذكي 🧠.\n\n"
                    f"🎁 رصيدك الحالي: {data[user_id]['remaining']} فيديو مجاني.\n"
                    "أرسل رابطاً وسأعرض لك كل الجودات المتاحة.")
    await update.message.reply_text(welcome_text, reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user = data.get(user_id, {"remaining": FREE_LIMIT, "used": 0})
    
    text = update.message.text.strip()
    if "http" in text:
        # التحقق من الرصيد قبل المعالجة
        if user["remaining"] <= 0:
            keyboard = [[InlineKeyboardButton(f"شحن 15 محاولة (100 ⭐)", callback_data="buy_stars")]]
            await update.message.reply_text("⚠️ نفدت محاولاتك المجانية! اشحن لمتابعة التحميل:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        await process_video_link(update, context, text)
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        answer = await ai_response(text)
        await update.message.reply_text(answer)

async def process_video_link(update, context, url):
    msg = await update.message.reply_text("⏳ جاري فحص الجودات المتوفرة...")
    ydl_opts = {'quiet': True, 'noplaylist': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            buttons = []
            heights_seen = set()
            available_formats = sorted([f for f in formats if f.get('height')], key=lambda x: x['height'], reverse=True)

            for f in available_formats:
                h = f['height']
                if h >= 360 and h not in heights_seen:
                    label = get_quality_label(h)
                    buttons.append([InlineKeyboardButton(label, callback_data=f"dl|{url}|{f['format_id']}")])
                    heights_seen.add(h)

            buttons.append([InlineKeyboardButton("🚀 أعلى جودة (تلقائي)", callback_data=f"dl|{url}|best")])
            await msg.edit_text("📺 اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons))
                
    except:
        await msg.edit_text("❌ فشل التحليل. تأكد من الرابط.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "P":
        await query.message.reply_text("أرسل الرابط المباشر الآن 🔗")
    
    elif query.data == "buy_stars":
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="شحن محاولات ATOM",
            description="إضافة 15 محاولة تحميل جديدة",
            payload="extra_15",
            provider_token="", currency="XTR",
            prices=[LabeledPrice("15 محاولة", STARS_PRICE)]
        )

    elif query.data.startswith("dl"):
        data_parts = query.data.split("|")
        url, f_id = data_parts[1], data_parts[2]
        await query.edit_message_text("📥 جاري التحميل والمعالجة...")
        await download_video(query, context, url, f_id)

async def download_video(target, context, url, f_id):
    user_id = str(target.from_user.id)
    chat_id = target.message.chat_id
    file_name = f"ATOM_{chat_id}.mp4"
    
    ydl_opts = {
        'format': f_id if f_id != "best" else 'bestvideo+bestaudio/best',
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(file_name):
            with open(file_name, 'rb') as video:
                await context.bot.send_video(chat_id=chat_id, video=video, caption="✅ تم التحميل بواسطة ATOM")
                
                # خصم المحاولة بعد النجاح فقط
                data = load_data()
                data[user_id]["remaining"] -= 1
                data[user_id]["used"] += 1
                save_data(data)
        else:
            raise Exception()
    except:
        await context.bot.send_message(chat_id=chat_id, text="❌ عذراً، فشل التحميل.")
    finally:
        if os.path.exists(file_name): os.remove(file_name)

# --- معالجة الدفع بالنجوم ---
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    data[user_id]["remaining"] += 15
    save_data(data)
    await update.message.reply_text(f"🎉 تم الشحن! رصيدك الجديد: {data[user_id]['remaining']}")

if __name__ == "__main__":
    print("ATOM AI Bot is Active with Star Payments...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
