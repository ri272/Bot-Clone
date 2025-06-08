import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# YouTube download function
def download_media(url, audio=False):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    if audio:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url)
        return ydl.prepare_filename(info)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send me a YouTube link to download.')

# Handle YouTube link
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    keyboard = [
        [
            InlineKeyboardButton("Download Video 🎥", callback_data=f'video|{url}'),
            InlineKeyboardButton("Download Audio 🎵", callback_data=f'audio|{url}'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose format:', reply_markup=reply_markup)

# Handle button click
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice, url = query.data.split('|')
    await query.edit_message_text(text="Downloading... please wait ⏳")

    try:
        if choice == 'audio':
            file_path = download_media(url, audio=True)
            await query.message.reply_audio(audio=open(file_path, 'rb'))
        else:
            file_path = download_media(url, audio=False)
            await query.message.reply_video(video=open(file_path, 'rb'))

        os.remove(file_path)

    except Exception as e:
        await query.message.reply_text(f'Error occurred: {e}')

# Main function
if __name__ == '__main__':
    BOT_TOKEN = '8199925072:AAEWF7hR6WqxMK8W9UdRwTNdY_3pHu8GpSU'  # Replace with your token
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    app.run_polling()
