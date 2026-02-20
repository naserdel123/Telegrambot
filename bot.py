import os
import logging
import re
import aiohttp
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الحصول على المتغيرات من البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # مثال: https://your-bot.onrender.com
PORT = int(os.getenv("PORT", 10000))

# قائمة الشتائم للحماية (يمكنك توسيعها)
BAD_WORDS = [
    "كلب", "حمار", "غبي", " stupid", "idiot", " احا", "عرص", "خول",
    "متناك", "شرموط", "قحب", "منيك", "fuck", "shit", "bitch"
]

# ============== الأوامر الأساسية ==============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب مع زر إضافة البوت للقروب"""
    keyboard = [
        [InlineKeyboardButton("➕ أضفني لقروبك", url=f"https://t.me/{context.bot.username}?startgroup=true")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
👋 أهلاً بك في بوت المتعدد المهام!

📋 المميزات المتاحة:

🎵 *بحث يوتيوب*
اكتب: `بحث [اسم الأغنية]`
مثال: `بحث مقامات موسيقية`

🖼️ *بحث صور*
اكتب: `صورة [الاسم]`
مثال: `صورة طبيعة`

💬 *همسات سرية*
رد على رسالة شخص واكتب: `همس [رسالتك]`

🛡️ *الحماية*
يحذف رسائل الشتم تلقائياً في القروبات

➕ أضفني لقروبك لتفعيل الحماية والمميزات!
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# ============== بحث يوتيوب ==============

async def search_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البحث في يوتيوب وإرسال النتائج"""
    query = ' '.join(context.args)
    
    if not query:
        await update.message.reply_text("❌ استخدم: بحث [اسم الأغنية]")
        return
    
    try:
        # استخدام API بديل للبحث في يوتيوب (ytsearch)
        search_url = f"https://yt.lemnoslife.com/search?part=snippet&q={query.replace(' ', '+')}&maxResults=1&type=video"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                data = await response.json()
                
                if not data.get('items'):
                    await update.message.reply_text("❌ لم يتم العثور على نتائج")
                    return
                
                video = data['items'][0]
                video_id = video['id']['videoId']
                title = video['snippet']['title']
                channel = video['snippet']['channelTitle']
                
                # الحصول على تفاصيل الفيديو (المشاهدات والمدة)
                details_url = f"https://yt.lemnoslife.com/videos?part=snippet,statistics,contentDetails&id={video_id}"
                
                async with session.get(details_url) as details_response:
                    details_data = await details_response.json()
                    
                    if details_data.get('items'):
                        video_details = details_data['items'][0]
                        stats = video_details.get('statistics', {})
                        content = video_details.get('contentDetails', {})
                        
                        views = stats.get('viewCount', '0')
                        duration = content.get('duration', 'PT0M0S')
                        
                        # تنسيق المشاهدات
                        views_formatted = f"{int(views):,}" if views.isdigit() else views
                        
                        # تنسيق المدة (ISO 8601)
                        duration_str = duration.replace('PT', '').replace('H', ':').replace('M', ':').replace('S', '')
                        
                        thumbnail = video['snippet']['thumbnails']['high']['url']
                        video_url = f"https://youtu.be/{video_id}"
                        
                        message = f"""
🎵 *{title}*

👤 القناة: {channel}
⏱️ المدة: {duration_str}
👁️ المشاهدات: {views_formatted}

🔗 [مشاهدة الفيديو]({video_url})
                        """
                        
                        await update.message.reply_photo(
                            photo=thumbnail,
                            caption=message,
                            parse_mode='Markdown'
                        )
                    else:
                        # إذا فشل الحصول على التفاصيل
                        video_url = f"https://youtu.be/{video_id}"
                        await update.message.reply_text(
                            f"🎵 *{title}*\n👤 {channel}\n🔗 [المشاهدة]({video_url})",
                            parse_mode='Markdown'
                        )
                        
    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")
        await update.message.reply_text("❌ حدث خطأ في البحث. حاول مرة أخرى.")

# ============== بحث الصور ==============

async def search_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال 3 صور عشوائية من picsum"""
    query = ' '.join(context.args)
    
    if not query:
        await update.message.reply_text("❌ استخدم: صورة [الاسم]")
        return
    
    # picsum.photos يعطي صور عشوائية، نستخدم seed مختلف للحصول على 3 صور
    await update.message.reply_text("🔍 جاري البحث عن الصور...")
    
    try:
        # إنشاء 3 روابط صور مختلفة باستخدام random seed
        import random
        seeds = [random.randint(1, 1000) for _ in range(3)]
        
        for i, seed in enumerate(seeds, 1):
            image_url = f"https://picsum.photos/seed/{seed}/800/600"
            await update.message.reply_photo(
                photo=image_url,
                caption=f"🖼️ صورة {i} - البحث: {query}"
            )
            
    except Exception as e:
        logger.error(f"خطأ في إرسال الصور: {e}")
        await update.message.reply_text("❌ حدث خطأ في جلب الصور")

# ============== الهمسات السرية ==============

async def whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال همسة سرية للشخص المردود عليه"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يجب الرد على رسالة الشخص الذي تريد إرسال الهمسة له")
        return
    
    whisper_text = ' '.join(context.args)
    
    if not whisper_text:
        await update.message.reply_text("❌ استخدم: همس [رسالتك] (بعد الرد على الشخص)")
        return
    
    target_user = update.message.reply_to_message.from_user
    sender = update.message.from_user
    
    try:
        # إرسال الهمسة للشخص المستهدف
        await context.bot.send_message(
            chat_id=target_user.id,
            text=f"""
🔒 *همسة سرية من {sender.first_name}*

{whisper_text}

📍 من مجموعة: {update.message.chat.title if update.message.chat.title else "خاص"}
            """,
            parse_mode='Markdown'
        )
        
        # إشعار المرسل بنجاح الإرسال
        await update.message.reply_text(f"✅ تم إرسال الهمسة سراً لـ {target_user.first_name}")
        
        # حذف رسالة الهمسة الأصلية لإخفاء الأمر
        await update.message.delete()
        
    except Exception as e:
        logger.error(f"خطأ في إرسال الهمسة: {e}")
        await update.message.reply_text("❌ لا يمكن إرسال الهمسة. تأكد أن الشخص بدأ محادثة مع البوت.")

# ============== حماية القروب ==============

async def delete_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف رسائل الشتائم تلقائياً"""
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text.lower()
    
    # التحقق من وجود شتائم
    for word in BAD_WORDS:
        if word.lower() in message_text:
            try:
                await update.message.delete()
                
                # إرسال تحذير (اختياري)
                warning = await update.message.reply_text(
                    f"⚠️ @{update.message.from_user.username or update.message.from_user.first_name} "
                    "تم حذف رسالتك لاحتوائها على كلمات غير لائقة!"
                )
                
                # حذف التحذير بعد 5 ثواني
                import asyncio
                await asyncio.sleep(5)
                await warning.delete()
                
                return
            except Exception as e:
                logger.error(f"خطأ في حذف الرسالة: {e}")
            break

# ============== معالجة الرسائل النصية ==============

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية والتوجيه للوظائف المناسبة"""
    text = update.message.text
    
    # البحث في يوتيوب
    if text.startswith("بحث "):
        context.args = text.split()[1:]
        await search_youtube(update, context)
    
    # البحث عن صور
    elif text.startswith("صورة "):
        context.args = text.split()[1:]
        await search_images(update, context)
    
    # الهمسات السرية
    elif text.startswith("همس "):
        context.args = text.split()[1:]
        await whisper(update, context)

# ============== إعداد Webhook ==============

async def webhook_handler(request):
    """معالج Webhook من تلجرام"""
    application = request.app['application']
    
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"خطأ في معالجة Webhook: {e}")
        return web.Response(text="Error", status=500)

async def setup_webhook(application: Application):
    """إعداد Webhook"""
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logger.info(f"Webhook تم إعداده على: {WEBHOOK_URL}/webhook")

async def main():
    """الدالة الرئيسية"""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN غير موجود!")
    if not WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL غير موجود!")
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # معالج الحماية (في القروبات فقط)
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS, 
            delete_bad_words
        ),
        group=1  # أولوية عالية
    )
    
    # إعداد aiohttp
    app = web.Application()
    app['application'] = application
    app.router.add_post('/webhook', webhook_handler)
    app.router.add_get('/', lambda r: web.Response(text="Bot is running!"))
    
    # إعداد Webhook
    await application.initialize()
    await setup_webhook(application)
    await application.start()
    
    # تشغيل الخادم
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    
    logger.info(f"البوت يعمل على المنفذ {PORT}")
    await site.start()
    
    # إبقاء التطبيق يعمل
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
