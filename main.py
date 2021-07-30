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



@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    b1 = types.InlineKeyboardButton(text='Список мероприятий', callback_data='ActionsList')
    b2 = types.InlineKeyboardButton(text='Мои мероприятия', callback_data='MyActions')
    keyboard.add(b1, b2)
    bot.send_message(message.chat.id, 'Мероприятия Федеральной территории Сириус', reply_markup=keyboard)
    dbworker.set_state(message.chat.id, States.Nothing.value)


@bot.message_handler(commands=['adminstart'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
    keyboard.add(b1)
    bot.send_message(message.chat.id, 'Введите пароль\nПароль: khochyvitcollege', reply_markup=keyboard)
    dbworker.set_state(message.chat.id, States.CheckPass.value)



@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == States.HowManySeats.value)
def apply_finish(message):
    try:
        tickets = int(message.text)
        if tickets >= 1:
            cursor.execute(f'''SELECT seats FROM Actions WHERE name = '{cur_apply}';''')
            row = cursor.fetchone()
            if tickets <= row[0]:
                cursor.execute(f'''UPDATE u{message.chat.id} SET tickets = {tickets} WHERE name = '{cur_apply}';''')
                connect.commit()
                cursor.execute(f'''SELECT * from u{message.chat.id} WHERE name = '{cur_apply}';''')
                row = cursor.fetchone()
                qr_text = f'{row[0]}\n{row[1]}\n{row[2]}\nКоличество забронированных мест: {row[3]}'
                img = qrcode.make(qr_text)
                img.save("qrcode.png")
                file = open('qrcode.png', 'rb')
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='StartNoEdit')
                keyboard.add(b1)
                bot.send_photo(message.chat.id, file, 'Билет успешно создан', reply_markup=keyboard)
                dbworker.set_state(message.chat.id, States.Nothing.value)
                cursor.execute(f'''SELECT seats from Actions WHERE name = '{cur_apply}';''')
                row = cursor.fetchone()
                newseats = row[0] - tickets
                cursor.execute(f'''UPDATE Actions SET seats = {newseats} WHERE name = '{cur_apply}';''')
                connect.commit()
            else:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                b1 = types.InlineKeyboardButton(text='Отмена', callback_data='Start')
                keyboard.add(b1)
                cursor.execute(f'''SELECT * from Actions WHERE name = '{cur_apply}';''')
                row = cursor.fetchone()
                bot.send_message(message.chat.id, f'К сожалению, не хватает свободных мест. Их всего {row[3]}. \
                                                    Введите заново', reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, 'Введите корректное количество мест, которые вы хотите забронировать')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите количество мест, которые вы хотите забронировать, используя ТОЛЬКО цифры')


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
        b1 = types.InlineKeyboardButton(text='Список мероприятий', callback_data='ActionsList')
        b2 = types.InlineKeyboardButton(text='Мои мероприятия', callback_data='MyActions')
        keyboard.add(b1, b2)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Мероприятия Федеральной территории Сириус', reply_markup=keyboard)
        dbworker.set_state(call.message.chat.id, States.Nothing.value)


    if call.data == 'StartNoEdit':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        b1 = types.InlineKeyboardButton(text='Список мероприятий', callback_data='ActionsList')
        b2 = types.InlineKeyboardButton(text='Мои мероприятия', callback_data='MyActions')
        keyboard.add(b1, b2)
        bot.send_message(call.message.chat.id, 'Мероприятия Федеральной территории Сириус', reply_markup=keyboard)
        dbworker.set_state(call.message.chat.id, States.Nothing.value)


    if call.data == 'AdminReg':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
        keyboard.add(b1)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Введите пароль\nПароль: khochyvitcollege', reply_markup=keyboard)
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
        cursor.execute('''SELECT COUNT(name) FROM Actions;''')
        row = cursor.fetchone()
        if row[0] != 0:
            cursor.execute('''SELECT name, time FROM Actions''')
            rows = cursor.fetchall()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for row in rows:
                keyboard.add(types.InlineKeyboardButton(text=f'{row[0]}\n{row[1]}', callback_data=f'Admin {row[0]}'))
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='AdminStart')
            keyboard.add(b1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Нажмите на мероприятие, чтобы увидеть больше информации',
                                  reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='Добавить мероприятие', callback_data='NewAction')
            b2 = types.InlineKeyboardButton(text='Выйти из режима адмиистратора', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Мероприятий пока нет... ',
                                  reply_markup=keyboard)


    if call.data == 'ActionsList':
        cursor.execute('''CREATE TABLE IF NOT EXISTS Actions  
             (name TEXT PRIMARY KEY,
              time TEXT,
              place TEXT,
              seats INT,
              description TEXT);''')
        connect.commit()
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS u{call.message.chat.id}  
                             (name TEXT PRIMARY KEY,
                              time TEXT,
                              place TEXT,
                              tickets INT);''')
        connect.commit()
        cursor.execute('''SELECT COUNT(name) FROM Actions;''')
        row = cursor.fetchone()
        if row[0] != 0:
            cursor.execute('''SELECT name, time FROM Actions''')
            rows = cursor.fetchall()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for row in rows:
                keyboard.add(types.InlineKeyboardButton(text=f'{row[0]}\n{row[1]}', callback_data=row[0]))
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Нажмите на мероприятие, чтобы увидеть больше информации',
                                  reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='Режим администратора', callback_data='AdminReg')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Мероприятий пока нет... Их могут добавлять только администраторы',
                                  reply_markup=keyboard)


    if call.data == 'MyActions':
        cursor.execute('''CREATE TABLE IF NOT EXISTS Actions  
                     (name TEXT PRIMARY KEY,
                      time TEXT,
                      place TEXT,
                      seats INT,
                      description TEXT);''')
        connect.commit()
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS u{call.message.chat.id}  
                                     (name TEXT PRIMARY KEY,
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
                keyboard.add(types.InlineKeyboardButton(text=f'{row[0]}\n{row[1]}', callback_data=f'My {row[0]}'))
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Нажмите на заявку, чтобы повторно получить QR-код или удалить ее',
                                  reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='Перейти к мероприятиям', callback_data='ActionsList')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Вы пока не оставляли заявок на мероприятия',
                                  reply_markup=keyboard)


    if call.data == 'MyActionsNoEdit':
        cursor.execute('''CREATE TABLE IF NOT EXISTS Actions  
                     (name TEXT PRIMARY KEY,
                      time TEXT,
                      place TEXT,
                      seats INT,
                      description TEXT);''')
        connect.commit()
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS u{call.message.chat.id}  
                                     (name TEXT PRIMARY KEY,
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
            bot.send_message(call.message.chat.id, 'Нажмите на заявку, чтобы повторно получить QR-код или удалить ее',
                                  reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='Перейти к мероприятиям', callback_data='ActionsList')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='Start')
            keyboard.add(b1, b2)
            bot.send_message(call.message.chat.id, 'Вы пока не оставляли заявок на мероприятия',
                                  reply_markup=keyboard)



    cursor.execute('''SELECT * FROM Actions''')
    rows = cursor.fetchall()
    for row in rows:

        if call.data == f'{row[0]}':
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='Записаться', callback_data=f'Apply {row[0]}')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='ActionsList')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'{row[0]}\nКогда: {row[1]}\nГде: {row[2]}\nСвободных мест: {row[3]}\n{row[4]}',
                                  reply_markup=keyboard)


        if call.data == f'Admin {row[0]}':
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='Удалить мероприятие', callback_data=f'Delete {row[0]}')
            b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='ActionsListAdmin')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'{row[0]}\nКогда: {row[1]}\nГде: {row[2]}\nСвободных мест: {row[3]}\n{row[4]}',
                                  reply_markup=keyboard)


        if call.data == f'Apply {row[0]}':
            cursor.execute(f'''CREATE TABLE IF NOT EXISTS u{call.message.chat.id}  
                 (name TEXT PRIMARY KEY,
                 time TEXT,
                 place TEXT,
                 tickets INT);''')
            connect.commit()
            cursor.execute(f'''INSERT INTO u{call.message.chat.id} (name, time, place) VALUES 
                            ('{row[0]}', '{row[1]}', '{row[2]}');''')
            connect.commit()
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Сколько мест вы хотите забронировать?')
            dbworker.set_state(call.message.chat.id, States.HowManySeats.value)
            global cur_apply
            cur_apply = row[0]
            #try:
            #    cursor.execute(f'''SELECT * FROM u{call.message.chat.id} WHERE name = {row[0]}''')
            #    keyboard = types.InlineKeyboardMarkup(row_width=1)
            #    b1 = types.InlineKeyboardButton(text='Перейти к моим заявкам', callback_data='MyActions')
            #    b2 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='ActionsList')
            #    keyboard.add(b1, b2)
            #    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            #                          text='Вы уже подали заявку на это мероприятие. Если вы хотите изменить заявку - \
            #                          вам нужно сначала ее удалить', reply_markup=keyboard)
            #except psycopg2.Error:
            #    cursor.execute(f'''INSERT INTO u{call.message.chat.id} (name, time, place) VALUES
            #    ('{row[0]}', '{row[1]}', '{row[2]}');''')
            #    connect.commit()
            #    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            #                          text='Сколько мест вы хотите забронировать?')
            #    dbworker.set_state(call.message.chat.id, States.HowManySeats.value)
            #    global cur_apply
            #    cur_apply = row[0]


        if call.data == f'Delete {row[0]}':
            cursor.execute(f'''DELETE FROM Actions WHERE name = '{row[0]}';''')
            connect.commit()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='ActionsListAdmin')
            b2 = types.InlineKeyboardButton(text='Меню администратора', callback_data='AdminStart')
            keyboard.add(b1, b2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Мероприятие удалено', reply_markup=keyboard)



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


        if call.data == f'DeleteApply {row[0]}':
            cursor.execute(f'''SELECT seats FROM Actions WHERE name = '{row[0]}';''')
            tick = cursor.fetchone()
            tickets = tick[0]
            cursor.execute(f'''SELECT * FROM Actions WHERE name = '{row[0]}';''')
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


        if call.data == f'QR {row[0]}':
            qr_text = f'{row[0]}\n{row[1]}\n{row[2]}\nКоличество забронированных мест: {row[3]}'
            img = qrcode.make(qr_text)
            img.save("qrcode.png")
            file = open('qrcode.png', 'rb')
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            b1 = types.InlineKeyboardButton(text='<< Вернуться', callback_data='MyActionsNoEdit')
            b2 = types.InlineKeyboardButton(text='Главное меню', callback_data='StartNoEdit')
            keyboard.add(b1, b2)
            bot.send_photo(call.message.chat.id, file, 'Билет успешно воссоздан', reply_markup=keyboard)




bot.polling(none_stop=True, interval=0)