import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
import yt_dlp
from dotenv import load_dotenv

# Configuration
load_dotenv()
TOKEN = os.getenv('TELE6803942054:AAF4IiIPlMVFhmk78Jz7lGYaqh8bK86NWF4GRAM_BOT_TOKEN')
MAX_FILE_SIZE = 2000  # MB (Telegram's limit)
SUPPORTED_PLATFORMS = [
    'youtube', 'youtu.be', 'twitter', 'x.com',
    'tiktok', 'instagram', 'facebook'
]

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and instructions"""
    welcome_msg = """🎬 *Professional Video Downloader Bot*
    
Supported platforms:
- YouTube
- Twitter/X
- TikTok
- Instagram
- Facebook

Send me a video URL to begin!"""
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_msg,
        parse_mode='Markdown'
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process video URLs and provide download options"""
    url = update.message.text
    chat_id = update.effective_chat.id
    
    try:
        # Get video info
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
        
        # Filter available formats
        video_formats = [
            f for f in formats 
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none'
        ]
        
        # Create format selection keyboard
        buttons = [
            [
                InlineKeyboardButton(
                    f"{f['ext']} ({f['format_note']})",
                    callback_data=f"download_{f['format_id']}"
                )
            ] for f in sorted(video_formats, key=lambda x: x['height'], reverse=True)
        ]
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="Select preferred video quality:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error processing this URL. Please check the link and try again."
        )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video download based on selected format"""
    query = update.callback_query
    await query.answer()
    
    format_id = query.data.split('_')[1]
    url = query.message.reply_to_message.text
    
    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [lambda d: progress_hook(d, context, query)],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            file_path = ydl.prepare_filename(info)
            
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=open(file_path, 'rb'),
            caption=info['title']
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Failed to download video. Please try again."
        )

async def progress_hook(d, context, query):
    """Send download progress updates"""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%')
        speed = d.get('_speed_str', 'N/A')
        await query.edit_message_text(
            text=f"⬇️ Downloading...\nProgress: {percent}\nSpeed: {speed}"
        )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(download_video, pattern='^download_'))
    
    # Start bot
    application.run_polling()
