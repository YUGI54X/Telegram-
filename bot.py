import telebot
from telebot import types
import yt_dlp
import os
from config import TOKEN, CHANNELS

bot = telebot.TeleBot(8734069991:AAHgDiwyeSzuGCMcEZ6UO6vcDK2SSraSDfA
)

def check_membership(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

def get_platform_buttons():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("YouTube ▶️", callback_data="plat_youtube"),
        types.InlineKeyboardButton("Instagram 📸", callback_data="plat_instagram"),
        types.InlineKeyboardButton("TikTok 🎵", callback_data="plat_tiktok"),
        types.InlineKeyboardButton("Facebook 🟦", callback_data="plat_facebook"),
    )
    return markup

@bot.message_handler(commands=['start'])
def start_msg(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        for c in CHANNELS:
            markup.add(types.InlineKeyboardButton(f"اشترك في {c}", url=f"https://t.me/{c.replace('@','')}" ))
        markup.add(types.InlineKeyboardButton("✅ تحقق", callback_data="verif"))
        sent = bot.send_message(message.chat.id,
            "الرجاء الإشتراك في القنوات التالية لاستخدام البوت ثم اضغط تحقق 👇", reply_markup=markup)
        return

    markup = get_platform_buttons()
    bot.send_message(
        message.chat.id, 
        "مرحبًا أنا بوت تم تصميمي من أجل تنزيل فيديوهات من مواقع التواصل الاجتماعي بجودة عالية.\n\nأرسل رابط أو اختر أزرار المنصات 👇", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verif")
def verify(call):
    user_id = call.from_user.id
    if check_membership(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        markup = get_platform_buttons()
        bot.send_message(
            call.message.chat.id, 
            "تم التحقق بنجاح ✅\n\nمرحبًا أنا بوت تم تصميمي من أجل تنزيل فيديوهات من مواقع التواصل الاجتماعي بجودة عالية.\n\nأرسل رابط أو اختر أزرار المنصات 👇", 
            reply_markup=markup
        )
    else:
        bot.answer_callback_query(call.id, "لم تكمل متطلبات الإشتراك.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("plat_"))
def platform_selected(call):
    platform = call.data.replace("plat_", "")
    msg = {
        "youtube": "أرسل رابط فيديو YouTube.",
        "instagram": "أرسل رابط فيديو Instagram Reel.",
        "tiktok": "أرسل رابط فيديو TikTok.",
        "facebook": "أرسل رابط فيديو Facebook.",
    }.get(platform, "أرسل الرابط.")
    markup = get_platform_buttons()
    bot.send_message(call.message.chat.id, msg, reply_markup=markup)

@bot.message_handler(content_types=['text'])
def text_msg(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        for c in CHANNELS:
            markup.add(types.InlineKeyboardButton(f"اشترك في {c}", url=f"https://t.me/{c.replace('@','')}" ))
        markup.add(types.InlineKeyboardButton("✅ تحقق", callback_data="verif"))
        bot.send_message(message.chat.id, "الرجاء الاشتراك في القنوات أولاً ثم اضغط تحقق 👇", reply_markup=markup)
        return

    url = message.text.strip()
    if not any(domain in url for domain in ['youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com', 'facebook.com']):
        markup = get_platform_buttons()
        bot.reply_to(message, "الرجاء إرسال رابط صحيح من YouTube, Instagram, Facebook, TikTok.", reply_markup=markup)
        return

    # جلب الجودات
    try:
        ydl_opts = {'quiet': True, 'listformats': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            videos = [f for f in formats if f.get('vcodec','none') != 'none' and f.get('acodec','none') != 'none']
            buttons=[]
            for v in videos:
                if v.get("filesize", 0) and v['filesize'] > 2000*1024*1024: continue
                desc = f"{v['format_note']} - {v.get('height','?')}p - {v.get('filesize',0)//1024//1024}MB"
                cb = f"dl|{url}|{v['format_id']}"
                buttons.append(types.InlineKeyboardButton(desc, callback_data=cb))
            if not buttons:
                raise Exception("لا توجد جودات مناسبة لهذا الفيديو.")
        markup = types.InlineKeyboardMarkup(row_width=2)
        for bt in buttons: markup.add(bt)
        bot.send_message(message.chat.id, "اختر الجودة المطلوبة:", reply_markup=markup)
    except Exception as e:
        print(e)
        bot.reply_to(message, "لم أستطع جلب الجودات أو هذا الرابط غير مدعوم.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("dl|"))
def send_video(call):
    parts = call.data.split('|')
    url = parts[1]
    fmt = parts[2]

    msg = bot.send_message(call.message.chat.id, "جاري تنزيل الفيديو...⏳")
    try:
        ydl_opts = {
            "format": fmt,
            "outtmpl": "%(id)s.%(ext)s",
            "quiet": True,
            "merge_output_format": "mp4"
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if os.path.getsize(filename) > 1900 * 1024 * 1024:
            bot.edit_message_text("الفيديو أكبر من الحد المسموح به في تيليجرام (2GB)!", call.message.chat.id, msg.id)
            os.remove(filename)
            return

        with open(filename, "rb") as f:
            bot.send_video(call.message.chat.id, f, caption="تم تنزيل الفيديو ✅", reply_markup=get_platform_buttons())
        os.remove(filename)
        bot.delete_message(call.message.chat.id, msg.id)
    except Exception as e:
        print(e)
        bot.edit_message_text("حدث خطأ أثناء التحميل أو لا يمكن تحميل هذا الرابط.", call.message.chat.id, msg.id)

bot.infinity_polling()
