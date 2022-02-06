# -*- coding: utf-8 -*-
import logging, random
import telegram
from utils import send_message
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram import ParseMode, ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ParseMode
from game import Game
import settings

rating_dict = {}

logger = None

games = {}

bot = telegram.Bot(settings.TOKEN)

def get_or_create_game(chat_id: int) -> Game:
    global games
    game = games.get(chat_id, None)
    if game is None:
        game = Game()
        games[chat_id] = game

    return game

def setup_logger():
    global logger
    file_handler = logging.FileHandler('crocodile.log', 'w', 'utf-8')
    stream_handler = logging.StreamHandler()
    logger = logging.getLogger("main_log")
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def help(update, context):
    update.message.reply_text('MEVCUT KOMUTLAR:\n' +
                              '/basla => oyunu başlatır\n\n' +
                              '/rating => Derecelendirme\n\n' +
                              '/cancel => Oyunu sonlandırma\n\n' +
                              '/sunucu => sunucu değiştirir\n\n' +
                              ' özel bot yapımı =>  , @magandasahip\n\n' +
                              ' Reklam ve Bilgilendirme => @DeezerMusicFilm\n\n' +
                              ' music botu => @DeezerMusicFilmbot\n\n' +
                              ' Tag botu @DeezerTaggerbot', reply_to_message_id=True)


def button(update, context):
    user_id = update.callback_query.from_user.id
    chat_id = update.callback_query.message.chat_id
    bot = telegram.Bot(token=settings.TOKEN)

    game = get_or_create_game(chat_id)

    query = update.callback_query

    if query.data == 'show_word':
        word = game.get_word(user_id)
        if game.is_master(query.from_user.id):
            bot.answer_callback_query(callback_query_id=query.id, text=word, show_alert=True)

    if query.data == 'change_word':
        word = game.change_word(user_id)
        if game.is_master(query.from_user.id):
            bot.answer_callback_query(callback_query_id=query.id, text=word, show_alert=True)
  

def cancel(update, context):
    global games

    if get_or_create_game(update.effective_chat.id):
        del games[update.effective_chat.id]
        send_message(update, "❌ Oyun başarılı bir şekilde sonlandırıldı Özel reklam için => @magandasahip .")

    else:
        send_message(update, "Kelime oyunu aktif değil /basla komutu ile oyun başlatın.")

def command_start(update, context: CallbackContext):
    if update.effective_chat.type == "private":

        addme = InlineKeyboardButton(text="🧚 GRUPLARA EKLE!", url="https://t.me/DeezerKelimebot?startgroup=a")
        sohbet = InlineKeyboardButton(text="💬 tag botu ", url="https://t.me/DeezerTaggerbot")
        oyun = InlineKeyboardButton(text="👾 Reklam ve Bilgilendirme", url="https://t.me/DeezerMusicFilm")
        admin = InlineKeyboardButton(text="👨🏻‍💻 Müzik botu", url="https://t.me/DeezerMusicFilmbot")

        keyboard = [[addme],[sohbet],[oyun],[admin]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('ÖZEL SOHBETTE OYUN OYNANMIYOR!\n'+
                                  'Merhaba! Botumuz @DeezerKelimebot oyunun telegrama uyarlanmış hali.Gruba ekleyip yetki verdikten sonra geriye oynamak kalıyor 😉 destek için @magandasahip.Komutlar için /help yazınız!\n' +
                                  'Not =>  ❌ kanala abone olmayı unutmayınız @DeezerMusicFilm ❌\n', reply_to_message_id=True, reply_markup=reply_markup)

def command_basla(update, context):
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        username = update.message.from_user.full_name

        logger.info('Got command /basla,'
                    'chat_id={},'
                    'user_id'.format(chat_id,
                                     user_id))
 
        game = get_or_create_game(chat_id)
        game.start()
        update.message.reply_text('Kelime Oyunu Başladı ✨'.format(username), reply_to_message_id=True)

        set_master(update, context)
 
        
def set_master(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.full_name
    logger.info('chat_id={}, New master is "{}"({})'.format(chat_id,
                                                            username,
                                                            update.message.from_user.id))

    game = get_or_create_game(chat_id)

    game.set_master(update.message.from_user.id)

    keyboard = [
                [InlineKeyboardButton("👻KELİMEYİ GÖSTER", callback_data='show_word'),
                 InlineKeyboardButton("♻️KELİME GEÇ", callback_data='change_word')],
             ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('[{}](tg://user?id={}) KELİMEYİ ANLATIYOR'.format(username,user_id), reply_to_message_id=True, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


def command_master(update: Update, context):
    chat_id = update.message.chat.id
    game = get_or_create_game(chat_id)
    username = update.message.from_user.full_name
    user_id = update.message.from_user.id

    if not game.is_game_started():
        return

    if not game.is_master_time_left():
        update.message.reply_text('sunucu olmak için {} saniye kaldı'.format(game.get_master_time_left()),
                                  reply_to_message_id=True)
        return

    logger.info('Got command /sunucu,'
                'chat_id={},'
                'user="{}"({}),'
                'timedelta={}'.format(chat_id,
                                      username,
                                      user_id,
                                      game.get_master_time_left()))

    set_master(update, context)


def command_show_word(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id

    game = get_or_create_game(chat_id)
    word = game.get_word(user_id)

    logger.info('Got command /show_word, ' 
                'chat_id={}, '
                'user="{}"({}),'
                'is_user_master={},'
                'word={}'.format(chat_id,
                                 update.message.from_user.full_name,
                                 update.message.from_user.id,
                                 game.is_master(user_id),
                                 word))

    update.message.reply_text(word, reply_to_message_id=True)


def command_change_word(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    game = get_or_create_game(chat_id)

    word = game.change_word(user_id)

    logger.info('Got command /change_word,'
                'chat_id={},'
                'user="{}"({}),'
                'is_user_master={},'
                'word={}'.format(chat_id,
                                 update.message.from_user.full_name,
                                 user_id,
                                 game.is_master(user_id),
                                 word))

    update.message.reply_text(word, reply_to_message_id=True)


def command_rating(update, context):
    chat_id = update.message.chat.id

    game = get_or_create_game(chat_id)

    rating_str = game.get_str_rating()

    logger.info('Got command /rating,'
                'chat_id={},'
                'rating={}'.format(update.message.chat.id,
                                   rating_str))

    update.message.reply_text(rating_str, reply_to_message_id=True)

def kaos(update, context):
    chat_id = update.message.chat.id
    update.message.reply_photo("https://te.legra.ph/file/4227fc45f2315b479b82c.jpg")

def is_word_answered(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    username = update.message.from_user.full_name
    text = update.message.text

    game = get_or_create_game(chat_id)

    word = game.get_current_word()

    if game.is_word_answered(user_id, text):
        update.message.reply_text('*{}* KELİMESİNİ [{}](tg://user?id={}) BULDU✅'.format(word, username,user_id), reply_to_message_id=True, parse_mode=ParseMode.MARKDOWN)    
        game.update_rating(user_id, username)  
        set_master(update, context)
    logger.info('Guessing word,'
                'chad_id={},'
                'user="{}"({}),'
                'is_master={},'
                'text="{}",'
                'word="{}"'.format(update.message.chat.id,
                                   update.message.from_user.full_name,
                                   update.message.from_user.id,
                                   game.is_master(user_id),
                                   text,
                                   word))


def main():
    setup_logger()

    updater = Updater(settings.TOKEN, use_context=True)

    bot = updater.bot

    dp = updater.dispatcher
    

    dp.add_handler(CommandHandler("sunucu", command_master))
    dp.add_handler(CommandHandler ("basla", command_basla))
    dp.add_handler(CommandHandler("show_word", command_show_word))
    dp.add_handler(CommandHandler("change_word", command_change_word))
    dp.add_handler(CommandHandler("rating", command_rating))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("kaos", kaos))
    dp.add_handler(CommandHandler("start", command_start))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CallbackQueryHandler(button))

    dp.add_handler(MessageHandler(Filters.text, is_word_answered))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
