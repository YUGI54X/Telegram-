import telebot
from telebot import types
import yt_dlp
import os

# ضع التوكن الخاص بك هنا
API_TOKEN = '8413954282:AAFFhbrVyipntxz08eymgoF6O1ePTJznZL4'
bot = telebot.TeleBot(API_TOKEN)

# تخزين مؤقت لروابط المستخدمين
user_data = {}

def get_video_info(url):
    ydl_opts = {'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def start_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [
        types.InlineKeyboardButton("Facebook", url="https://facebook.com"),
        types.InlineKeyboardButton("Instagram", url="https://instagram.com"),
        types.InlineKeyboardButton("YouTube", url="https://youtube.com"),
        types.InlineKeyboardButton("TikTok", url="https://tiktok.com"),
        types.InlineKeyboardButton("X (Twitter)", url="https://x.com")
    ]
    markup.add(*btns)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "مرحبًا بك، في بوت دراكولا ، لقد تم تصميم لتنزيل فيديوهات من مواقع التواصل ، أرسل رابط مباشر أو أختر احدى منصات من أزرار ،"
    bot.send_message(message.chat.id, welcome_text, reply_markup=start_markup())

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def handle_link(message):
    url = message.text
    msg = bot.reply_to(message, "⏳ جاري جلب الجودات المتاحة...")
    
    try:
        info = get_video_info(url)
        user_data[message.chat.id] = url
        
        markup = types.InlineKeyboardMarkup()
        # اختيار جودات محددة (عالية، متوسطة)
        markup.add(types.InlineKeyboardButton("High Quality (أعلى جودة)", callback_data="hq"))
        markup.add(types.InlineKeyboardButton("Low Quality (جودة منخفضة)", callback_data="lq"))
        
        bot.edit_message_text("اختر الجودة المطلوبة قبل التحميل:", message.chat.id, msg.message_id, reply_markup=markup)
    except Exception as e:
        bot.edit_message_text("❌ عذراً، الرابط غير مدعوم أو خاص.", message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ["hq", "lq"])
def download_video(call):
    url = user_data.get(call.message.chat.id)
    if not url: return

    bot.edit_message_text("🚀 جاري التحميل والإرسال... قد يستغرق ذلك دقيقة.", call.message.chat.id, call.message.message_id)
    
    # إعدادات التحميل بناءً على الجودة
    format_opt = 'bestvideo+bestaudio/best' if call.data == "hq" else 'worstvideo+worstaudio/worst'
    file_path = f"{call.message.chat.id}.mp4"
    
    ydl_opts = {
        'format': format_opt,
        'outtmpl': file_path,
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو
        with open(file_path, 'rb') as video:
            bot.send_video(call.message.chat.id, video, caption="✅ تم التحميل بواسطة بوت دراكولا")
        
        # العودة للقائمة الرئيسية
        send_welcome(call.message)
        
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ حدث خطأ أثناء التحميل.")
    
    # تنظيف الملفات
    if os.path.exists(file_path):
        os.remove(file_path)

bot.polling()
