from telebot import types, TeleBot
from config import token, States
import dbworker
import psycopg2
import qrcode


bot = TeleBot(token)


connect = psycopg2.connect(
    database="SiriusActions",
    user="postgres",
    password="ivan.121314",
    host="localhost",
    port="2323")
cursor = connect.cursor()



@bot.message_handler(commands=['start', 'menu'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    b1 = types.InlineKeyboardButton(text='Список мероприятий и запись на них', callback_data='ActionsList')
    b2 = types.InlineKeyboardButton(text='Мои мероприятия', callback_data='MyActions')
    keyboard.add(b1, b2)
    bot.send_message(message.chat.id, 'Мероприятия Федеральной территории Сириус', reply_markup=keyboard)
    dbworker.set_state(message.chat.id, States.Nothing.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == States.HowManySeats.value)
def apply_finish(message):
    try:
        tickets = int(message.text)
        if tickets >= 1:
            cursor.execute(f'''SELECT seats from Actions WHERE name = '{cur_apply}';''')
            row = cursor.fetchone()
            connect.close()
            if tickets <= row[3]:
                cursor.execute(f'''UPDATE u{message.chat.id} SET tickets = {tickets} WHERE name = '{cur_apply}';''')
                connect.commit()
                cursor.execute(f'''SELECT * from u{message.chat.id} WHERE name = '{cur_apply}';''')
                row = cursor.fetchone()
                connect.close()
                qr_text = f'{row[0]}\n{row[1]}\n{row[2]}\nКоличество забронированных мест: {row[3]}'
                img = qrcode.make(qr_text)
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
                keyboard.add(b1)
                bot.send_photo(message.chat.id, img, 'Билет успешно создан', reply_markup=keyboard)
                dbworker.set_state(message.chat.id, States.Nothing.value)
                cursor.execute(f'''SELECT seats from Actions WHERE name = '{cur_apply}';''')
                row = cursor.fetchone()
                newseats = row[3] - tickets
                cursor.execute(f'''UPDATE Actions SET seats = {newseats} WHERE name = '{cur_apply}';''')
                connect.commit()
                if newseats == 0:
                    cursor.execute(f'''DELETE FROM Actions WHERE name = '{cur_apply}';''')
                    connect.commit()
                connect.close()
            else:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
                keyboard.add(b1)
                bot.send_message(message.chat.id, f'К сожалению, не хватает свободных мест. Их всего {row[3]}. \
                                                    Введите заново', reply_markup=keyboard)
                dbworker.set_state(message.chat.id, States.Nothing.value)
        else:
            bot.send_message(message.chat.id, 'Введите корректное количество мест, которые вы хотите забронировать')
    except:
        bot.send_message(message.chat.id, 'Введите корректное количество мест, которые вы хотите забронировать')


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == States.CheckPass.value)
def check_pass(message):
    if message.text == 'khochyvitcollege':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        b1 = types.InlineKeyboardButton(text='Создать мероприятие', callback_data='NewAction')
        b2 = types.InlineKeyboardButton(text='Просмотр и удаление мероприятий', callback_data='ActionsListAdmin')
        b3 = types.InlineKeyboardButton(text='Выйти из режима администратора', callback_data='Start')
        keyboard.add(b1, b2, b3)
        bot.send_message(message.chat.id, 'Отлично! Вы в режиме администратора. Что будем делать?',
                         reply_markup=keyboard)
        dbworker.set_state(message.chat.id, States.Nothing.value)
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
        keyboard.add(b1)
        bot.send_message(message.chat.id,
                         'Неверный пароль! Введите пароль заново, подскажу еще раз. Пароль:\nkhochyvitcollege',
                         reply_markup=keyboard)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == States.CreateActionName.value)
def create_action_name(message):
    global action_name
    action_name = message.text
    bot.send_message(message.chat.id, 'Введите время мероприятия в текстовом формате, например "27 июля 18:00-20:00" \
                                                                                            или "13.08.2021 17:30"')
    dbworker.set_state(message.chat.id, States.CreateActionTime.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == States.CreateActionTime.value)
def create_action_time(message):
    global action_time
    action_time = message.text
    bot.send_message(message.chat.id, 'Место проведения меропрятия:')
    dbworker.set_state(message.chat.id, States.CreateActionPlace.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == States.CreateActionPlace.value)
def create_action_place(message):
    global action_place
    action_place = message.text
    bot.send_message(message.chat.id, 'Введите количество мест на это мероприятие (цифрами)')
    dbworker.set_state(message.chat.id, States.CreateActionSeats.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == States.CreateActionSeats.value)
def create_action_seats(message):
    global action_seats
    try:
        action_seats = int(message.text)
        bot.send_message(message.chat.id, 'А теперь напишите описание этого мероприятия')
        dbworker.set_state(message.chat.id, States.CreateActionDescription.value)
    except:
        bot.send_message(message.chat.id, 'Ошибка! Введите количество мест ЦИФРАМИ, например:\n34')

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == States.CreateActionDescription.value)
def create_action_description(message):
    global action_description
    action_description = message.text
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    cursor.execute(f'''INSERT INTO Actions (name, time, place, seats, description) VALUES 
                   ('{action_name}', '{action_time}', '{action_place}', {action_seats}, '{action_description}')''')
    connect.commit()
    b1 = types.InlineKeyboardButton(text='Создать мероприятие', callback_data='NewAction')
    b2 = types.InlineKeyboardButton(text='Просмотр и удаление мероприятий', callback_data='ActionsListAdmin')
    b3 = types.InlineKeyboardButton(text='Выйти из режима администратора', callback_data='Start')
    keyboard.add(b1, b2, b3)
    bot.send_message(message.chat.id, 'Мероприятие успешно создано!', reply_markup=keyboard)
    dbworker.set_state(message.chat.id, States.Nothing.value)



@bot.callback_query_handler(func=lambda call: True)
def buttons(call):

    if call.data == 'Start':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        b1 = types.InlineKeyboardButton(text='Список мероприятий и запись на них', callback_data='ActionsList')
        b2 = types.InlineKeyboardButton(text='Мои мероприятия', callback_data='MyActions')
        keyboard.add(b1, b2)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Мероприятия Федеральной территории Сириус', reply_markup=keyboard)
        dbworker.set_state(call.message.chat.id, States.Nothing.value)

    if call.data == 'AdminReg':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
        keyboard.add(b1)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Введите пароль (Пароль: khochyvitcollege)', reply_markup=keyboard)
        dbworker.set_state(call.message.chat.id, States.CheckPass.value)

    if call.data == 'AdminStart':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        b1 = types.InlineKeyboardButton(text='Создать мероприятие', callback_data='NewAction')
        b2 = types.InlineKeyboardButton(text='Просмотр и удаление мероприятий', callback_data='ActionsListAdmin')
        b3 = types.InlineKeyboardButton(text='Выйти из режима администратора', callback_data='Start')
        keyboard.add(b1, b2, b3)
        bot.send_message(call.message.chat.id, 'Отлично! Вы в режиме администратора. Что будем делать?', reply_markup=keyboard)
        dbworker.set_state(call.message.chat.id, States.Nothing.value)


    if call.data == 'NewAction':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Введите название мероприятия:')
        dbworker.set_state(call.message.chat.id, States.CreateActionName.value)


    if call.data == 'ActionsListAdmin':
        if cursor.execute('''SELECT count(*) FROM Actions;''') >= 1:
            cursor.execute('''SELECT * from Actions''')
            rows = cursor.fetchall()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for row in rows:
                keyboard.add(types.InlineKeyboardButton(text=f'{row[0]}\n{row[1]}\n{row[2]}\n'
                                                        f'Количество свободных мест: {row[3]}', callback_data=f'Admin {row[0]}'))
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='AdminStart')
            b2 = types.InlineKeyboardButton(text='Выйти из режима администратора', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Нажмите на мероприятие, чтобы посмотреть описание',
                                  reply_markup=keyboard)
            connect.close()
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='В режим администратора', callback_data='AdminStart')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Мероприятий пока нет... Их могут добавлять только администраторы',
                                  reply_markup=keyboard)


    if call.data == 'ActionsList':
        cursor.execute('''CREATE TABLE IF NOT EXISTS Actions  
             (name INT PRIMARY KEY NOT NULL,
              time TEXT,
              place TEXT,
              seats INT,
              description TEXT);''')
        connect.commit()
        cursor.execute('''SELECT count(name) FROM Actions;''')
        row = cursor.fetchone()
        if row[0] != 0:
            cursor.execute('''SELECT * from Actions''')
            rows = cursor.fetchall()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for row in rows:
                keyboard.add(types.InlineKeyboardButton(text=f'{row[0]}\n{row[1]}\n{row[2]}\n'
                                                        f'Количество свободных мест: {row[3]}', callback_data=row[0]))
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Нажмите на мероприятие, чтобы посмотреть описание или записаться',
                                  reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='В режим администратора', callback_data='AdminReg')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Мероприятий пока нет... Их могут добавлять только администраторы',
                                  reply_markup=keyboard)

    if call.data == 'MyActions':
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS u{call.message.chat.id}  
                     (name INT PRIMARY KEY NOT NULL,
                      time TEXT,
                      place TEXT,
                      tickets INT);''')
        connect.commit()
        cursor.execute(f'''SELECT count(name) FROM u{call.message.chat.id};''')
        row = cursor.fetchone()
        if row[0] != 0:
            cursor.execute(f'''SELECT * from u{call.message.chat.id}''')
            rows = cursor.fetchall()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for row in rows:
                keyboard.add(types.InlineKeyboardButton(text=f'{row[0]}\n{row[1]}\n{row[2]}\nКоличество \
                                    забронированных мест: {row[3]}', callback_data=f'My {row[0]}'))
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Нажмите на заявку, чтобы повторно получить QR-код или удалить ее',
                                  reply_markup=keyboard)
            connect.close()
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='В режим администратора', callback_data='AdminReg')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Мероприятий пока нет... Их могут добавлять только администраторы',
                                  reply_markup=keyboard)


    cursor.execute('''SELECT * from Actions''')
    rows = cursor.fetchall()
    for row in rows:

        if call.data == f'{row[0]}':
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='Записаться', callback_data=f'Apply {row[0]}')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='ActionsList')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'{row[4]}', reply_markup=keyboard)

        elif call.data == f'Admin {row[0]}':
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='ActionsListAdmin')
            b2 = types.InlineKeyboardButton(text='Выйти из режима администрара', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'{row[4]}', reply_markup=keyboard)

        elif call.data == f'Apply {row[0]}':
            cursor.execute(f'''CREATE TABLE IF NOT EXISTS u{call.message.chat.id}  
                 (name TEXT PRIMARY KEY NOT NULL,
                 time TEXT,
                 place TEXT,
                 tickets INT);''')
            connect.commit()
            cursor.execute(f'''INSERT INTO u{call.message.chat.id} (name, time, place) VALUES ({row[0]}, {row[1]}, {row[2]})''')
            connect.commit()
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Сколько мест вы хотите забронировать?')
            dbworker.set_state(call.message.chat.id, States.HowManySeats.value)
            global cur_apply
            cur_apply = row[0]


    cursor.execute(f'''SELECT * from u{call.message.chat.id}''')
    rows = cursor.fetchall()
    for row in rows:

        if call.data == f'My {row[0]}':
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='Показать QR-код', callback_data=f'QR {row[0]}')
            b2 = types.InlineKeyboardButton(text='Удалить заявку', callback_data=f'DeleteApply {row[0]}')
            b3 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='MyActions')
            keyboard.add(b1, b2, b3)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'{row[0]}\n{row[1]}\n{row[2]}\nКоличество забронированных \
                                  мест: {row[3]}', reply_markup=keyboard)

        elif call.data == f'DeleteApply {row[0]}':
            cursor.execute(f'''SELECT seats FROM Actions WHERE name = '{row[0]}';''')
            tickets = cursor.fletchone()
            newseats2 = row[3] + tickets
            cursor.execute(f'''UPDATE Actions SET seats = {newseats2} WHERE name = '{row[0]}';''')
            connect.commit()
            cursor.execute(f'''DELETE FROM u{call.message.chat.id} WHERE name = '{row[0]}';''')
            connect.commit()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='К моим заявкам', callback_data='MyActions')
            b2 = types.InlineKeyboardButton(text='Стартовое меню', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Заявка удалена', reply_markup=keyboard)

        elif call.data == f'QR {row[0]}':
            qr_text = f'{row[0]}\n{row[1]}\n{row[2]}\nКоличество забронированных мест: {row[3]}'
            img = qrcode.make(qr_text)
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            b2 = types.InlineKeyboardButton(text='Главное меню', callback_data='Start')
            keyboard.add(b1, b2)
            bot.send_photo(call.message.chat.id, img, 'Билет успешно воссоздан', reply_markup=keyboard)



bot.polling(none_stop=True, interval=0)