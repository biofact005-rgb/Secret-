import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from stegano import lsb
import os
import random
from PIL import Image, ImageDraw
from flask import Flask
import threading

# ==========================================
# 👇 CONFIGURATION 👇
# ==========================================
API_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
CHANNEL_ID = "@errorkidk_05" 
SUPPORT_BOT = "https://t.me/errorkidk_bot"

bot = telebot.TeleBot(API_TOKEN)
user_data = {}
registered_users = set() 
TUTORIAL_VIDEO_ID = None

# ==========================================
# 🌐 FLASK SERVER (Render Keep-Alive Ke Liye)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Secure Messenger Bot V4.0 is Live on Render!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 🖼️ IMAGE GENERATOR & UI
# ==========================================
DEFAULT_IMAGE_PATH = "default.png"
if not os.path.exists(DEFAULT_IMAGE_PATH):
    img = Image.new('RGB', (800, 800), color=(15, 15, 15))
    img.save(DEFAULT_IMAGE_PATH)

def get_random_banner():
    banner_path = "banner.png"
    bg_colors = [(26, 30, 36), (22, 26, 29), (11, 15, 25), (15, 23, 42), (24, 24, 27)]
    acc_colors = [(217, 4, 41), (56, 176, 0), (0, 119, 182), (138, 43, 226), (255, 159, 28)]
    
    img = Image.new('RGB', (800, 400), color=random.choice(bg_colors))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 385, 800, 400], fill=random.choice(acc_colors))
    img.save(banner_path)
    return banner_path

class ColorBtn(InlineKeyboardButton):
    def __init__(self, text, style=None, **kwargs):
        super().__init__(text, **kwargs)
        self.style = style
    def to_dict(self):
        d = super().to_dict()
        if self.style: d['style'] = self.style
        return d

def log_to_admin(report_text):
    if ADMIN_ID:
        try: bot.send_message(ADMIN_ID, f"🛡️ <b>ADMIN LOG REPORT</b>\n━━━━━━━━━━━━━━\n{report_text}", parse_mode="HTML")
        except: pass

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

def get_sub_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_ID.replace('@','')}"))
    markup.add(InlineKeyboardButton("🔄 Joined / Refresh", callback_data="main_menu"))
    return markup

def get_main_menu(user_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        ColorBtn("Send Secret Message", callback_data="mode_hide", style="danger"),
        ColorBtn("Receive Secret Message", callback_data="mode_scan", style="success"),
        ColorBtn("Watch Tutorial", callback_data="watch_tutorial", style="primary"),
        InlineKeyboardButton("🆘 Help / Support", url=SUPPORT_BOT)
    )
    if user_id == ADMIN_ID:
        markup.add(ColorBtn("⚙️ Upload Tutorial", callback_data="set_tutorial", style="primary"))
    return markup

def send_home_page(cid):
    text = "<blockquote><b>🤖 SECURE MESSENGER V4.0</b>\n\n⚠️ <b>IMPORTANT:</b> Please watch the tutorial before use to ensure security.\n\nSelect an operation below:</blockquote>"
    try:
        with open(get_random_banner(), 'rb') as photo:
            msg = bot.send_photo(cid, photo, caption=text, reply_markup=get_main_menu(cid), parse_mode="HTML")
            user_data[cid]['last_msg_id'] = msg.message_id
    except Exception:
        msg = bot.send_message(cid, text, reply_markup=get_main_menu(cid), parse_mode="HTML")
        user_data[cid]['last_msg_id'] = msg.message_id

# ==========================================
# 🤖 BOT LOGIC
# ==========================================
@bot.message_handler(commands=['start'])
def welcome(message):
    cid = message.chat.id
    if not is_subscribed(cid):
        bot.send_message(cid, "<blockquote>⚠️ <b>ACCESS DENIED</b>\n\nYou must join our official channel to use this service.</blockquote>", parse_mode="HTML", reply_markup=get_sub_markup())
        return

    if cid not in registered_users:
        registered_users.add(cid)
        log_to_admin(f"👤 <b>NEW USER</b>\nName: {message.from_user.first_name}\nID: <code>{cid}</code>\nUser: @{message.from_user.username}")

    if cid not in user_data: user_data[cid] = {}
    send_home_page(cid)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid = call.message.chat.id
    if not is_subscribed(cid): 
        bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
        return

    if call.data == "main_menu":
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        send_home_page(cid)
    
    elif call.data == "mode_hide":
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        text = "<blockquote><b>📝 ENCRYPTION SERVICE</b>\n\nPlease send the secret text message you wish to hide.</blockquote>"
        with open(get_random_banner(), 'rb') as photo:
            msg = bot.send_photo(cid, photo, caption=text, reply_markup=InlineKeyboardMarkup().add(ColorBtn("🔙 Back", callback_data="main_menu", style="primary")), parse_mode="HTML")
        user_data[cid]['last_msg_id'] = msg.message_id
        user_data[cid]['mode'] = 'hide'
        
    elif call.data == "mode_scan":
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        text = "<blockquote><b>🕵️ DECRYPTION SERVICE</b>\n\nUpload the image file <b>(As Document)</b> to reveal the hidden message.</blockquote>"
        with open(get_random_banner(), 'rb') as photo:
            msg = bot.send_photo(cid, photo, caption=text, reply_markup=InlineKeyboardMarkup().add(ColorBtn("🔙 Back", callback_data="main_menu", style="primary")), parse_mode="HTML")
        user_data[cid]['last_msg_id'] = msg.message_id
        user_data[cid]['mode'] = 'scan'

    elif call.data == "watch_tutorial":
        global TUTORIAL_VIDEO_ID
        if TUTORIAL_VIDEO_ID:
            try: bot.delete_message(cid, call.message.message_id)
            except: pass
            bot.send_video(cid, TUTORIAL_VIDEO_ID, caption="<blockquote>📺 <b>OFFICIAL TUTORIAL</b></blockquote>", reply_markup=InlineKeyboardMarkup().add(ColorBtn("🔙 Back", callback_data="main_menu", style="primary")), parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "⚠️ Tutorial not available!", show_alert=True)

    elif call.data == "set_tutorial" and cid == ADMIN_ID:
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        bot.send_message(cid, "<blockquote>⚙️ <b>ADMIN:</b> Upload the video file for the tutorial.</blockquote>", parse_mode="HTML")
        user_data[cid]['mode'] = 'set_tutorial'

@bot.message_handler(content_types=['text', 'photo', 'document', 'video'])
def handle_inputs(message):
    cid = message.chat.id
    if not is_subscribed(cid): return
    if cid not in user_data: user_data[cid] = {}
    
    mode = user_data[cid].get('mode')
    
    if mode == 'hide':
        if message.content_type != 'text': return
        out_path = f"secret_{cid}.png"
        try:
            secret = lsb.hide(DEFAULT_IMAGE_PATH, message.text)
            secret.save(out_path)
            log_to_admin(f"🔐 <b>ENCRYPTION</b>\nUser: {message.from_user.first_name}\nID: <code>{cid}</code>\nData: <code>{message.text}</code>")
            
            with open(out_path, 'rb') as f:
                bot.send_document(cid, f, caption="<blockquote>✅ <b>SUCCESS:</b> Your message has been encrypted. Send this file as a document.</blockquote>", parse_mode="HTML")
            
            user_data[cid]['mode'] = None
            send_home_page(cid)
        except Exception:
            bot.send_message(cid, f"<blockquote>❌ <b>ERROR:</b> Encryption failed. Try again.</blockquote>", parse_mode="HTML")
        finally:
            if os.path.exists(out_path): os.remove(out_path)

    elif mode == 'scan':
        path = f"temp_{cid}.png"
        try:
            file_id = message.document.file_id if message.document else message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)
            with open(path, 'wb') as f: f.write(downloaded)
            
            hidden_text = lsb.reveal(path)
            log_to_admin(f"🔓 <b>DECRYPTION</b>\nUser: {message.from_user.first_name}\nID: <code>{cid}</code>\nFound: <code>{hidden_text if hidden_text else 'NOTHING'}</code>")
            
            res_text = f"<blockquote>🔓 <b>MESSAGE FOUND:</b>\n\n<code>{hidden_text}</code></blockquote>" if hidden_text else "<blockquote>⚠️ <b>ERROR:</b> No hidden message found.</blockquote>"
            bot.send_message(cid, res_text, parse_mode="HTML")
            
            user_data[cid]['mode'] = None
            send_home_page(cid)
        except Exception:
            bot.send_message(cid, "<blockquote>❌ <b>ERROR:</b> Failed to read image. Make sure it was sent as a Document.</blockquote>", parse_mode="HTML")
        finally:
            if os.path.exists(path): os.remove(path)

    elif mode == 'set_tutorial' and cid == ADMIN_ID:
        if message.content_type == 'video':
            global TUTORIAL_VIDEO_ID
            TUTORIAL_VIDEO_ID = message.video.file_id
            bot.send_message(cid, "<blockquote>✅ <b>SUCCESS:</b> Tutorial updated.</blockquote>", parse_mode="HTML")
            user_data[cid]['mode'] = None
            send_home_page(cid)

if __name__ == "__main__":
    print("🚀 Bot Started on Render!")
    # Start the Flask web server in a background thread
    threading.Thread(target=run_server).start()
    # Start the Telegram bot polling
    bot.infinity_polling(timeout=20, long_polling_timeout=15, skip_pending=True)
