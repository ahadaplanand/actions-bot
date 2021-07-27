import telebot
from telebot import types, TeleBot
from config import token
import psycopg2


bot = TeleBot(token)


@bot.message_handler(commands=['start', 'menu'])
def start(message):
    keyboard = types.InlineKeyboardMarkup()
    b1 = types.InlineKeyboardButton(text='Список мероприятий и запись на них', callback_data='ActionsList')
    b2 = types.InlineKeyboardButton(text='Мои мероприятия', callback_data='MyActions')
    keyboard.add(b1, b2)
    bot.send_message(message.from_user.id, '', reply_markup=keyboard)



@bot.callback_query_handler(func=lambda call: True)
def buttons(call):

    if call.data == 'ActionsList':

    if call.data == 'MyActions':


bot.polling(none_stop = True, interval = 0)