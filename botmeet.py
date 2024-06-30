import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Token API bot Anda
TOKEN = '7480652741:AAFwSwLZT_6aoNjWzZpaxF6vM47CIEC12Fs'

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Daftar pengguna yang menunggu pasangan
waiting_users = []

# Daftar pasangan yang sedang chatting
active_chats = {}

# Menu keyboard
main_menu_keyboard = [['/find', '/end'], ['/end_and_find']]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, one_time_keyboard=True, resize_keyboard=True)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Selamat datang! Gunakan menu untuk mengontrol bot.', reply_markup=main_menu_markup)

async def find(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in active_chats:
        await confirm_find(update, context)
    elif user_id in waiting_users:
        await update.message.reply_text('Anda sudah berada dalam antrian. Harap tunggu pertandingan.')
    else:
        if waiting_users:
            partner = waiting_users.pop(0)
            active_chats[user_id] = partner
            active_chats[partner] = user_id
            await context.bot.send_message(chat_id=user_id, text='Anda telah dicocokkan! Sampaikan salam kepada rekan ngobrol baru Anda.')
            await context.bot.send_message(chat_id=partner, text='Anda telah dicocokkan! Sampaikan salam kepada rekan ngobrol baru Anda.')
        else:
            waiting_users.append(user_id)
            await update.message.reply_text('Anda telah masuk ke dalam antrian. Harap tunggu pertandingan.')

async def message_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in active_chats:
        partner = active_chats[user_id]
        if update.message.photo:
            await context.bot.send_photo(chat_id=partner, photo=update.message.photo[-1].file_id)
        elif update.message.video:
            await context.bot.send_video(chat_id=partner, video=update.message.video.file_id)
        elif update.message.document:
            await context.bot.send_document(chat_id=partner, document=update.message.document.file_id)
        elif update.message.audio:
            await context.bot.send_audio(chat_id=partner, audio=update.message.audio.file_id)
        elif update.message.voice:
            await context.bot.send_voice(chat_id=partner, voice=update.message.voice.file_id)
        elif update.message.video_note:
            await context.bot.send_video_note(chat_id=partner, video_note=update.message.video_note.file_id)
        elif update.message.location:
            await context.bot.send_location(chat_id=partner, latitude=update.message.location.latitude, longitude=update.message.location.longitude)
        elif update.message.contact:
            await context.bot.send_contact(chat_id=partner, phone_number=update.message.contact.phone_number, first_name=update.message.contact.first_name)
        elif update.message.sticker:
            await context.bot.send_sticker(chat_id=partner, sticker=update.message.sticker.file_id)
        else:
            await context.bot.send_message(chat_id=partner, text=update.message.text)
    else:
        await update.message.reply_text('Anda tidak sedang mengobrol. Gunakan /find untuk mencari mitra ngobrol.')

async def end_chat(user_id: int, context: CallbackContext) -> bool:
    if user_id in active_chats:
        partner = active_chats.pop(user_id)
        if partner in active_chats:
            active_chats.pop(partner)
            await context.bot.send_message(chat_id=partner, text='Mitra obrolan Anda telah meninggalkan obrolan.')
        return True
    return False

async def end(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if await end_chat(user_id, context):
        await update.message.reply_text('Anda telah meninggalkan obrolan.')
    else:
        await update.message.reply_text('Anda tidak sedang mengobrol.')

async def end_and_find(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if await end_chat(user_id, context):
        await find(update, context)  # Setelah itu cari pasangan obrolan baru
    else:
        await update.message.reply_text('Anda tidak sedang mengobrol. Menghentikan pencarian.')

async def confirm_find(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Ya, cari obrolan baru", callback_data='confirm_find')],
        [InlineKeyboardButton("Tidak", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Anda sedang dalam obrolan. Apakah Anda ingin mencari obrolan baru?', reply_markup=reply_markup)

async def confirm_end(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Ya, akhiri obrolan", callback_data='confirm_end')],
        [InlineKeyboardButton("Tidak", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Apakah Anda yakin ingin mengakhiri obrolan?', reply_markup=reply_markup)

async def confirm_end_and_find(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Ya, akhiri dan cari baru", callback_data='confirm_end_and_find')],
        [InlineKeyboardButton("Tidak", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Apakah Anda yakin ingin mengakhiri obrolan dan mencari mitra baru?', reply_markup=reply_markup)

async def callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == 'confirm_end':
        if await end_chat(user_id, context):
            await query.message.reply_text('Anda telah meninggalkan obrolan.')
        else:
            await query.message.reply_text('Anda tidak sedang mengobrol.')
    elif query.data == 'confirm_end_and_find':
        await end_chat(user_id, context)
        await find(query, context)
    elif query.data == 'confirm_find':
        if user_id in active_chats:
            await end_chat(user_id, context)
        await find(query, context)
    elif query.data == 'cancel':
        await query.message.reply_text('Dibatalkan.')

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Tambahkan handler untuk perintah-perintah bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("find", find))
    application.add_handler(CommandHandler("end", confirm_end))
    application.add_handler(CommandHandler("end_and_find", confirm_end_and_find))

    # Tambahkan handler untuk pesan teks (bukan perintah)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Tambahkan handler untuk media (foto, video, dokumen, audio, voice, video note, stiker)
    application.add_handler(MessageHandler(filters.PHOTO, message_handler))
    application.add_handler(MessageHandler(filters.VIDEO, message_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, message_handler))
    application.add_handler(MessageHandler(filters.AUDIO, message_handler))
    application.add_handler(MessageHandler(filters.VOICE, message_handler))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, message_handler))
    application.add_handler(MessageHandler(filters.Sticker.ALL, message_handler))

    # Tambahkan handler untuk berbagi lokasi dan kontak
    application.add_handler(MessageHandler(filters.LOCATION, message_handler))
    application.add_handler(MessageHandler(filters.CONTACT, message_handler))

    # Tambahkan handler untuk callback query
    application.add_handler(CallbackQueryHandler(callback_handler))

    # Mulai polling untuk mendengarkan perintah dari Telegram
    application.run_polling()

if __name__ == '__main__':
    main()
