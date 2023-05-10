import telebot
from telebot import types
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
from telebot.types import CallbackQuery 
from texttable import Texttable
import datetime
from PIL import Image, ImageFont, ImageDraw
import os
import time
import sqlite3
from random import randint
import threading
import ast
from datetime import timedelta
import traceback


from parser_main import DataParser


user_data = {}

class Adv:
    def __init__(self):
        self.text = None
        self.media = []     
        
        
bot = telebot.TeleBot("6040676784:AAFlFXW51Y6Xa1KllObX5nlNgC4Q5Rx69Dw",
                      parse_mode='HTML')

DAYS = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу',
        'воскресенье']
MOUNTS = ['января', 'февраля','мара', 'апреля', 'мая', 'июня', 'июля',
          'августа', 'сентября', 'октября', 'ноября', 'декабря']
calendar = Calendar(language=RUSSIAN_LANGUAGE)

calendar_1_callback = CallbackData("calendar_1", "action", "year",
                                   "month", "day", "function")
calendar_2_callback = CallbackData("calendar_2", "action", "year",
                                   "month", "day", "function")



def get_next_dayofweek_datetime(date_time, dayofweek):
    start_time_w = date_time.isoweekday()
    
    days  = ["monday","tuesday","wednesday",
             "thursday","friday","saturday","sunday"]
    
    target_w = days.index(dayofweek) + 1
    
    if start_time_w < target_w:
      day_diff = target_w - start_time_w
    else:
        day_diff = 7 - (start_time_w - target_w)

    return date_time + timedelta(days=day_diff)


def reminder_message(message, func=None):
    now = datetime.datetime.now()
    print(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())} --> ',
          message.chat.id, 'reminder')
    
    bot.edit_message_text("Выберите дату для напоминания ✍ㅤ",
                          message.chat.id, message.message_id,
                          reply_markup=calendar.create_calendar(
                              name=calendar_2_callback.prefix,
                              year=now.year,
                              month=now.month,
                              function=func,),)  


def reminder_set_time(message, date=None, func=None, flg=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Отмена', callback_data='mainmenu')
    markup.row(back) 
    bot.send_message(message.chat.id, 'Введите время (часы:минуты)',
                     reply_markup=markup)
        
    bot.register_next_step_handler(message, reminder_set_name, date, func,
                                   message.text, flg)


def reminder_set_name(message, date, func, time, flg=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Отмена',
                                      callback_data='mainmenu', reply_markup=markup)
    markup.row(back)     
    bot.send_message(message.chat.id,
                     'Введите текст для напоминания (или напишите "-" чтобы оставить поле пустым')
    text = message.text if message.text != '-' else ''
    
    if flg:
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                       (message.chat.id,))
        
        res = cursor.fetchone()
        x = ast.literal_eval(str(res[0]))
        curr_state = x[-1][2]
        curr_state.append(message.text)
        x[-1][2] = curr_state
        cursor.execute("UPDATE reminders SET reminds = ? WHERE user_id = ?",
                       (str(x), message.chat.id, ))
        conn.commit()
        conn.close()
     
    bot.register_next_step_handler(message, reminder_set, date, text, time, func)
 

def choose_day_or_time(message, func=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='Разовое',
                                     callback_data=f'one_time_reminder|{func}')
    markup.row(back)
    
    back = types.InlineKeyboardButton(text='Ежедневное (в разработке)',
                                      callback_data=f'many_time_reminder|{func}')
    markup.row(back)
    
    back = types.InlineKeyboardButton(text='⬅ Отмена',
                                      callback_data='mainmenu')
    markup.row(back)     
    bot.edit_message_text('Выберите тип напоминания', message.chat.id,
                          message.message_id,
                          reply_markup=markup)
    

def chose_current_days(message, days=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    data = ['⭕ Понедельник', '⭕ Вторник', '⭕ Среда', '⭕ Четверг',
            '⭕ Пятница', '⭕ Суббота', '⭕ Воскресенье', '⭕ Все дни']
    
    data_calls = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                  'saturday', 'sunday', 'all_days']

    if days != None:
        for i in days:
            changed = data[data_calls.index(i)].split(" ")
            data[data_calls.index(i)] = '❌' + changed[-1]

    c = 0
    for i in range(4):
        markup.row(types.InlineKeyboardButton(text=data[i + c],
                                            callback_data=data_calls[i + c],
                                            reply_markup=markup),
                   types.InlineKeyboardButton(text=data[i + 1 + c],
                                                       callback_data=data_calls[i + 1 + c],
                                                       reply_markup=markup))
        c += 1
    
    
    procced = types.InlineKeyboardButton(text='➡ Далее',
                                        callback_data='nxt_step_chooser',
                                        reply_markup=markup)
    markup.row(procced)
    
    exitt = types.InlineKeyboardButton(text='⬅ Отмена',
                                        callback_data='exitt',
                                        reply_markup=markup)
    markup.row(exitt)
    
    try:
        bot.edit_message_text('✍ Выберите дни (нажмите ещё раз, чтобы убрать день), после чего нажмите "Далее", при нажатии на день недели, подождите, пока он отметится :)', message.chat.id,
                              message.message_id,
                              reply_markup=markup)
    except Exception as e:
        pass

def choose_reminder_fuction(message, fix=None):
    if fix == 'take_grades':
        return 'take_grades'
    
    elif fix == 'pass':
        return 'pass'
        
    else:    
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        back = types.InlineKeyboardButton(text='📆 Расписание на выбранный день',
                                          callback_data='take_grades',
                                          reply_markup=markup)
        markup.row(back)
        back = types.InlineKeyboardButton(text='🚫 Без функции',
                                          callback_data='pass',
                                          reply_markup=markup)
        markup.row(back)
        back = types.InlineKeyboardButton(text='⬅ Отмена',
                                          callback_data='mainmenu',
                                          reply_markup=markup)
        markup.row(back)
        bot.edit_message_text('✍Выберите функцию:ㅤㅤㅤ', message.chat.id,
                              message.message_id,
                              reply_markup=markup)

    return None
    
    
def reminder_set(message, date, time, func, text, flg=False, rl_text=None):
    global user_data
    
    try: 
        markup = types.InlineKeyboardMarkup(row_width=1)
        tryagain = types.InlineKeyboardButton(text='🔄 Попробовать ещё раз',
                                              callback_data='checkTimes')
        markup.row(tryagain)     
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='mainmenu')
        markup.row(back)
        if rl_text == None:
            user_data[message.chat.id] = {'reminder_name': message.text}
        else:
            user_data[message.chat.id] = {'reminder_name': rl_text}
            
        reminder_name = user_data[message.chat.id]['reminder_name']
        
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                       (message.chat.id,))
        
        res = cursor.fetchone()
        x = ast.literal_eval(str(res[0]))
        if len(x[-1][-1]) == 0:
            x = ast.literal_eval(str(res[0]))
            curr_state = x[-1][-1]
            curr_state.append(reminder_name)
            x[-1][-1] = curr_state
            
            cursor.execute("UPDATE reminders SET reminds = ? WHERE user_id = ?",
                           (str(x), message.chat.id, ))
            conn.commit()
        conn.close()
        
        if type(date) != list:
            if '.' in date:
                date = date.split('.')
            else:
                date = date.split('-')
            if len(time) != 2:
                time = time.split(':')
                
            try:
                reminder_time = datetime.datetime(int(date[2]), int(date[1]),
                                                  int(date[0]), int(time[0]),
                                                  int(time[1]))
            except Exception:
                reminder_time = datetime.datetime(int(date[0]), int(date[1]),
                                                  int(date[2]), int(time[0]),
                                                  int(time[1]))
                
            now = datetime.datetime.now()
            delta = reminder_time - now
            if delta.total_seconds() <= 0:
                markup = types.InlineKeyboardMarkup(row_width=1)
                tryagain = types.InlineKeyboardButton(text='🔄 Попробовать ещё раз',
                                                      callback_data='checkTimes')
                markup.row(tryagain)     
                back = types.InlineKeyboardButton(text='⬅ Назад',
                                                  callback_data='mainmenu')
                markup.row(back)
                bot.send_message(message.chat.id,
                                 'Вы ввели прошедшую дату, попробуйте еще раз.',
                                 reply_markup=markup)
                
                
                
            else:

                if flg == False:
                    reminder_timer = threading.Timer(delta.total_seconds(),
                                                     send_reminder,
                                                     [message, reminder_name, text])
                    
                    
                else:
                    print(delta)
                    reminder_timer = threading.Timer(delta.total_seconds(),
                                                     send_reminder_multiple,
                                                     [message, reminder_name, text, date, time, rl_text])
                
                bot.send_message(message.chat.id,
                    'Напоминание "{}" установлено на {}.'.format(reminder_name,
                                                                 reminder_time))
                reminder_timer.start()
        else:
            for i in date:
                date = get_next_dayofweek_datetime(datetime.datetime.now(),
                                                   i)

                reminder_set(message, str(date.date()), time, func, text,
                             True, message.text)
                
            buildMainMenu(message)
        
        
            
        
        if rl_text != None:
            buildMainMenu(message)
        
    except Exception as e:    
        traceback.print_exc()
        bot.send_message(message.chat.id,
                'Вы ввели неверный формат даты и времени, попробуйте еще раз.',
                reply_markup=markup)


def send_reminder(message, reminder_name, func):
    
    text = '🏛 Напоминание' if reminder_name == '-' else '🏛 Напоминание "{}"!'.format(reminder_name)
    if func == 'take_grades':
        buildGradesToday(message, text)
    
    else:
        bot.send_message(message.chat.id,
                    text)


def send_reminder_multiple(message, reminder_name, func, date, time, rl_text):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()
    
    cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                   (message.chat.id,))
    
    res = cursor.fetchone()
    
    conn.close()
    print(reminder_name, func, date, time, rl_text)
    dats = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                  'saturday', 'sunday', 'all_days']
    x = ast.literal_eval(str(res[0]))
    for i in x:
        wk = str(dats[date.weekday()])
        t = str(time[0]) + ':' + str(time[1])
        print(i, func, wk, t, rl_text)
        if func == i[0] and wk in i[1] and t == i[2][0] and rl_text == i[-1][0]:
            text = '🏛 Напоминание' if rl_text == '-' else '🏛 Напоминание "{}"!'.format(rl_text)
            if func == 'take_grades':
                buildGradesToday(message, text)
            
            else:
                bot.send_message(message.chat.id, text)
            
            reminder_set(message, date, time, func, True, rl_text)
            print('found')
    
def add_table_values(user_id, name, login, password):
    
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ? AND login = ?',
                   (user_id, login, ))
    res = cursor.fetchall()
    if len(res) == 0:
        cursor.execute('INSERT INTO users (user_id, name, login, password) VALUES (?, ?, ?, ?)', (user_id, name, login, password))
        conn.commit()
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='mainmenu')
        markup.row(back)
        bot.send_message(user_id,
                         'Такой пользователь уже добавлен в ваш аккаунт ⚙',
                         reply_markup=markup)
    conn.close()
def upd_cookies(login, cookie):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET cookie = ? WHERE login = ?',
                   (cookie, login))
    conn.commit()
    conn.close()
def new_parser(login):
    b = DataParser()
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()
    pechenki, passw = cursor.execute('SELECT cookie, password FROM users WHERE login = ?',
                                     (login,)).fetchone()[0]
    conn.close()
    if pechenki:
        b.load_cookies(pechenki)
    else:
        b.login(login, passw)
    return b
  
        
@bot.message_handler(commands=['start', 'Войти'])
def on_start(message):
    if is_admin_check(message.chat.id):
        markup = show_admin_panel()
        bot.send_message(message.chat.id, 'Админ панель',
                         reply_markup=markup)
    
    else:
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?',
                       (message.chat.id,))
        res = cursor.fetchall()
        if len(res):
            buildMainMenu(message, name=message.chat.first_name)
        else:
            bot.send_message(message.chat.id, 'Сначала нужно войти в аккаунт')
            get_login(message)
        conn.close()

@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    if is_admin_check(message.chat.id):
        userid = message.text.split(" ")[1]
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO admins(user_id) VALUES (?)",
                       (str(userid), ))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, 'Админ добавлен')


@bot.message_handler(commands=['delete_admin'])
def delete_admin(message):
    if is_admin_check(message.chat.id):
        userid = message.text.split(" ")[1]
        if is_admin_check(userid):
            conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM admins WHERE user_id = ?",
                           (str(userid), ))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, 'Админ удалён')
        else:
            bot.send_message(message.chat.id, 'Такого админа нет')
        
        
def get_login(message):
    bot.send_message(message.chat.id,
                    'Введите логин на edu.tatar (только цифры, без пробелов):')
    bot.register_next_step_handler(message, get_password)
    
                                      
def get_password(message):
    login = message.text
    
    password = bot.send_message(message.chat.id,
                            'Введите пароль (учитывая регистр, без пробелов):')
	
    bot.register_next_step_handler(password, log_in, login)


def log_in(message, login):
    password = message.text
    parser_worker = DataParser()
    print('{}user ' + str(login) + ' ' + password +\
          ' joined:' + str(message.chat.id))
    parser_worker.login(login, password)
    if parser_worker.login_status:
        try:
            add_table_values(message.chat.id,
                             message.from_user.first_name, login, password)
            upd_cookies(login)
        except Exception as e: 
            pass
        
        buildMainMenu(message)        
    
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton('Попробовать ещё раз',
                                           callback_data='login_error')
        markup.add(item1)
        bot.send_message(message.chat.id,
                         'Неверный логин или пароль!',
                                 reply_markup=markup)
#601732567

def logging(message):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()
    cursor.execute("SELECT login, password FROM users WHERE user_id = ?",
                       [str(message.chat.id)])
    
    result = cursor.fetchall()
    conn.close()
    return result


def choose_user(call, res):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i in range(len(res)):
        parser_worker = DataParser()
        parser_worker.login(res[i][3], res[i][4])
        name = parser_worker.get_name()
        item = types.InlineKeyboardButton(f'{name}', callback_data=f'user{i}')
        markup.row(item)
    try:
        bot.edit_message_text('✅ Выберите пользователя:',
                              call.message.chat.id, call.message.message_id,
                              reply_markup=markup)
    except Exception as e:
        bot.send_message(call.message.chat.id,
                         '✅ Выберите пользователя:',
                         reply_markup=markup)
        
        
def get_add_id():
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    res = cursor.fetchall()
    conn.close()
    return res

def show_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton('Реклама',
                                       callback_data='Advertisment')
    markup.row(item1)

    return markup


def advertisment(message, adv):
    adv.text = message.text
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='mainmenu')
    markup.add(back)
    mes = bot.send_message(message.chat.id,
                           'Теперь присылайте картинки, по одной штуке, максимум 10,когда закончите нажмите на "Закончить с файлами"')
    bot.register_next_step_handler(mes, advert_add_media, adv)
    

def advert_add_media(message, adv):
    if message.text == 'Закончить с файлами':
        markup = types.InlineKeyboardMarkup(row_width=1)
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='mainmenu')
        markup.add(back)
        mm = bot.send_message(message.chat.id, 'a',
                              reply_markup=types.ReplyKeyboardRemove())
        bot.delete_message(mm.chat.id, mm.id)
        mes = bot.send_message(message.chat.id,
                               'A теперь всё проверим:', reply_markup=markup)
        agree_send_adv(message, adv)
    elif message.text == '⬅ Назад':
        kb = show_admin_panel()
        bot.send_message('Добро пожаловать!', message.chat.id, reply_markup=kb)
    elif message.content_type == 'photo' or message.content_type == 'video':
        if message.content_type == 'photo':
            adv.media.append([message.photo[0].file_id, 'photo'])
        elif message.content_type == 'video':
            adv.media.append([message.video.file_id, 'video'])
        else:
            msg = bot.send_message(message.chat.id,
                                   'Ошибка поддерживаются только фото/видео')
            bot.register_next_step_handler(msg, advert_add_media, adv)
        if len(adv.media) < 10:
            kb = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text='Закончить с файлами')
            btn2 = types.KeyboardButton(text='⬅ Назад')
            kb.add(btn1, btn2)
            msg = bot.send_message(message.chat.id,
                                   f'Принято {len(adv.media)} файл(ов)',
                                   reply_markup=kb)
            bot.register_next_step_handler(msg, advert_add_media, adv)
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            back = types.InlineKeyboardButton(text='⬅ Назад',
                                              callback_data='mainmenu')
            markup.add(back)
            bot.send_message(message.chat.id, 'A теперь всё проверим:',
                             reply_markup=markup)
            agree_send_adv(message, adv)

    else:
        msg = bot.send_message(message.chat.id,
                               'Ошибка поддерживаются только фото/видео')
        bot.register_next_step_handler(msg, advert_add_media, adv)
        

def agree_send_adv(message, adv):
    medialst = []
    for img in adv.media:
        file = bot.get_file(img[0])
        a = bot.download_file(file.file_path)
        if img[1] == 'photo':
            b = types.InputMediaPhoto(a)
        elif img[1] == 'video':
            b = types.InputMediaVideo(a)
        medialst.append(b)
    if len(medialst) == 1:
        if adv.media[0][1] == 'photo':
            bot.send_photo(message.chat.id,
                           medialst[0].media, caption=adv.text)
            formatt = 'photo'
        elif adv.media[0][1] == 'video':
            formatt = 'video'
            bot.send_video(message.chat.id,
                           medialst[0].media, caption=adv.text)
            medialst[0].caption = adv.text

    else:
        medialst[-1].caption = adv.text
        bot.send_media_group(message.chat.id, medialst)
        formatt = 'mediagroup'
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='mainmenu')
    markup.add(back)
    mes = bot.send_message(message.chat.id,
                           'Если вас все устраивает отправьте любое сообщеение, иначе выберите "назад" под эти сообщением', reply_markup=markup)
    bot.register_next_step_handler(mes, mailing_adv, medialst, formatt)    
        

def mailing_adv(message, medialst, formatt):
    bot.send_message(message.chat.id, 'ОТПРАВКА...')
    data = get_add_id()
    data = set(data)
    c = 0
    if formatt == 'photo':
        for id in data:
            try:
                bot.send_photo(id, medialst[0].media,
                               caption=medialst[0].caption)
                c+=1
            except:
                pass

    elif formatt == 'video':
        for id in data:
            try:
                bot.send_video(id, medialst[0].media,
                               caption=medialst[0].caption)
                c+=1
            except:
                pass
    elif formatt == 'mediagroup':
        for id in data:
            try:
                bot.send_media_group(id, medialst)
                c+=1
            except:
                pass
    kb = show_admin_panel()
    bot.send_message(message.chat.id,
                f'Отправка завершена, доставлено {c}/{len(data)} сообщений',
                reply_markup=kb)
    

@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_2_callback.prefix))	    
def callback_inline(call: CallbackQuery):
        name, action, year, month, day, funct = call.data.split(calendar_2_callback.sep)
        date = calendar.calendar_query_handler(
            bot=bot,
            call=call,
            name=name,
            action=action,
            year=year,
            month=month,
            day=day
        )
        if action == "DAY":
            options = types.InlineKeyboardMarkup(row_width=1)
            
            back = types.InlineKeyboardButton(text='⬅ Назад',
                                              callback_data='mainmenu')
            
            options.add(back)
            

            reminder_set_time(call.message, date.strftime('%d.%m.%Y'), funct)
                
                
        elif action == "CANCEL":
            buildMainMenu(call.message)
            
            
@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_1_callback.prefix))	    
def callback_inline(call: CallbackQuery):
        name, action, year, month, day, function = call.data.split(calendar_1_callback.sep)
        date = calendar.calendar_query_handler(
            bot=bot,
            call=call,
            name=name,
            action=action,
            year=year,
            month=month,
            day=day
        )
        if action == "DAY":
            options = types.InlineKeyboardMarkup(row_width=1)
            
            back = types.InlineKeyboardButton(text='⬅ Назад',
                                              callback_data='mainmenu')
            
            options.add(back)
            

            
            userdata = logging(call.message)
            login, password = userdata[0][0], userdata[0][1]
            parser_worker = DataParser()
            parser_worker.login(login, password)
            data = parser_worker.get_day_marks(str(int((time.mktime(date.timetuple())))))
            parser_worker.logout()
            
            t = Texttable()
            t.add_rows(data)
            
            table_width = max([ len(x) for x in t.draw().split('\n') ])
            
            table_height = 0
            for i in t.draw():
                if i == '\n':
                    table_height += 1
                    
            
            img = Image.new('RGB', (table_width * 20 - 50,
                                    table_height * 35 - 50),
                            color = (255, 255, 255))
            fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
            
            ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
           
            flname = str(randint(100000, 1000000))
            img.save(f'{flname}.png')   
            
            
            intDay = date.weekday()
            days = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
            months = ['января', 'февраля','мара', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
            bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'),
                           caption=f'Ваше расписание на {days[intDay]} ({date.day} {months[date.month - 1]}) ✅',
                               reply_markup=options)
        
            os.remove(f'{flname}.png')
            
        
        elif action == "CANCEL":
            buildMainMenu(call.message)
           



def buildMainMenu(message, name=''):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    item3 = types.InlineKeyboardButton('🎒 Расписание и оценки',
                                       callback_data='Grades')
    markup.row(item3)
    
    item1 = types.InlineKeyboardButton('🗓 Табель успеваемости',
                                       callback_data='year')
    markup.row(item1)
    
    item2 = types.InlineKeyboardButton('🏛 Прочие функции',
                                       callback_data='other')
    markup.row(item2)
    
    item4 = types.InlineKeyboardButton('⚙ Настройки',
                                       callback_data='Options')
    markup.row(item4)
    
    if name != '':
        res = f'✅ Рады видеть вас снова, {name.split(" ")[-1]}!'
    else:
        res = '✅ Рады видеть вас снова!'
    try:
        bot.edit_message_text(res, message.chat.id, message.message_id,
                              reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, res, reply_markup=markup)
    

def is_admin_check(chat_id):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()
    cursor.execute("SELECT EXISTS(SELECT * FROM admins WHERE user_id = ?)",
                   (str(chat_id),))
    result = cursor.fetchone()
    conn.close()
    return bool(result[0])    


@bot.message_handler(commands=['send_all'])
def send_to_all(message):
    if is_admin_check(message.chat.id):
        res = message.text.split("|")
        data = get_add_id()
        data = set(data)
        for i in data:
            bot.send_message(i[0], res[1])
    
        
@bot.message_handler(commands=['amount_of_users'])
def amount_of_users(message):
    if is_admin_check(message.chat.id):
        data = get_add_id()
        data = set(data)
        bot.send_message(message.chat.id,
                         f'На данный момент {len(data)} уникальных пользователей')
            
            
def makeSchcedule(call, period):
    options = types.InlineKeyboardMarkup(row_width=1)
        
    t = Texttable()
    
    userdata = logging(call.message)
    login, password = userdata[0][0], userdata[0][1]         
    parser_worker = DataParser()
    parser_worker.login(login, password)
    res = parser_worker.schcedule(period=period)
    parser_worker.logout()    
    
    if len(res[1][-1]) == 3 and len(res[1][0]) == 4:
        res[1][-1].insert(1, '')        
    
    data = res[1]    
    
    periods = res[0]
    
    print(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())} --> ',
          login, 'schcedule')
    
    for i in periods.items():
        option = types.InlineKeyboardButton(i[0], callback_data=i[1])
        options.add(option)
  
    t.add_rows(data)
        
    table_width = max([ len(x) for x in t.draw().split('\n') ])
        
    table_height = 0
    for i in t.draw():
        if i == '\n':
            table_height += 1
                
        
    img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50),
                    color = (255, 255, 255))
    fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
        
    ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
       
    flname = str(randint(100000, 1000000))
    img.save(f'{flname}.png')       
    
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='mainmenu')
    
    options.add(back)    
    
    per = list(periods.keys())[list(periods.values()).index(period)]
    
    bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'),
                   caption=f'✅ Ваш табель успеваемости за {per.lower()}',
                   reply_markup=options)
    
    os.remove(f'{flname}.png')    
 

def buidGradesMenu(call):
    grades = types.InlineKeyboardMarkup(row_width=1)
    
    grades_today = types.InlineKeyboardButton(text='🗓 Оценки за сегодня',
                                            callback_data='check_grades_today')
    grades_get = types.InlineKeyboardButton(text='📆 Выбрать дату',
                                            callback_data='check_grades_get')
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                            callback_data='mainmenu')
    
    grades.add(grades_today, grades_get, back)
    bot.edit_message_text('🎒 Просмотр оценок', call.message.chat.id,
                          call.message.message_id,
                          reply_markup=grades)
    
    
def buildGradesToday(message, textr=''):
    options = types.InlineKeyboardMarkup(row_width=3)
    
    previous = types.InlineKeyboardButton(text='⬅', callback_data='next-1')
    back = types.InlineKeyboardButton(text='Назад', callback_data='mainmenu')
    nextt = types.InlineKeyboardButton(text='➡', callback_data='next1')
    
    options.add(previous, back, nextt)
    
    
    userdata = logging(message)
    login, password = userdata[0][0], userdata[0][1]         
    parser_worker = DataParser()
    parser_worker.login(login, password)
    data = parser_worker.get_day_marks('')
    parser_worker.logout()
    
    print(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())} --> ',
          login, 'buildGradesToday')
    
    t = Texttable()
    t.add_rows(data)
        
    table_width = max([ len(x) for x in t.draw().split('\n') ])
        
    table_height = 0
    for i in t.draw():
        if i == '\n':
            table_height += 1
                
        
    img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50),
                    color = (255, 255, 255))
    fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
        
    ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
       
       
    flname = str(randint(100000, 1000000))
    img.save(f'{flname}.png')
    if textr == '':
        if len(data) != 1:   
            bot.send_photo(message.chat.id, open(f'{flname}.png', 'rb'),
                           caption='Ваше расписание на сегодня ✅',
                           reply_markup=options)
        else:
            bot.edit_message_text('😯 В этот день нет уроков!', message.chat.id,
                                  message.message_id,
                                  reply_markup=options) 
    else:
        if len(data) != 1:   
            bot.send_photo(message.chat.id, open(f'{flname}.png', 'rb'),
                           caption=f'{textr}',
                           reply_markup=options)
            
        else:
            bot.send_message(message.chat.id,
                             f'{textr}: в этот день нет уроков!',
                             reply_markup=options)
        
    os.remove(f'{flname}.png')
    
 
def changeDayOfGrades(call, sign):
    options = types.InlineKeyboardMarkup(row_width=3)
    
    previous = types.InlineKeyboardButton(text='⬅'
                                          , callback_data=f'next{sign-1}')
    back = types.InlineKeyboardButton(text='Назад',
                                      callback_data='mainmenu')
    nextt = types.InlineKeyboardButton(text='➡',
                                       callback_data=f'next{sign+1}')
    
    options.add(previous, back, nextt)
    
     
    
    t = Texttable()
    
    date = datetime.datetime.now()
    date = date + 1 * sign * datetime.timedelta(days=1)    #fixxxx
    
    userdata = logging(call.message)
    login, password = userdata[0][0], userdata[0][1]         
    parser_worker = DataParser()
    parser_worker.login(login, password)
    data = parser_worker.get_day_marks(str(int((time.mktime(date.timetuple())))))
    parser_worker.logout()
    print(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())} --> ',
          login, 'changeDayOfGrades')
    t.add_rows(data)
        
    table_width = max([ len(x) for x in t.draw().split('\n') ])
        
    table_height = 0
    for i in t.draw():
        if i == '\n':
            table_height += 1
                
        
    img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50),
                    color = (255, 255, 255))
    fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
        
    ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
       
       
    flname = str(randint(100000, 1000000))
    img.save(f'{flname}.png')
    intDay = date.weekday()
    if len(data) != 1:
        bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'),
                       caption=f'🎒 Ваше расписание на {DAYS[intDay]} ({date.day} {MOUNTS[date.month - 1]}) ✅',
                           reply_markup=options)
    else:
        try:
            bot.send_message(call.message.chat.id,
                             f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',
                             reply_markup=options)
        except Exception as e:
            bot.send_message(call.message.chat.id,
                             f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',
                             reply_markup=options)
    
    os.remove(f'{flname}.png')


def buildOtherMenu(call, name=''):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    item3 = types.InlineKeyboardButton('⏳ Напоминания (в разработке)',
                                       callback_data='checkTimes')
    markup.row(item3)
    
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='mainmenu')
    markup.row(back)
    
    if name != '':
        res = f'✅ Рады видеть вас снова, {name.split(" ")[-1]}!'
    else:
        res = '✅ Рады видеть вас снова!'
    try:
        bot.edit_message_text(res, call.message.chat.id,
                              call.message.message_id,
                              reply_markup=markup)
    except Exception as e:
        bot.send_message(call.message.chat.id, res, reply_markup=markup)    
    

@bot.callback_query_handler(func=lambda call: 'next' in call.data)
def callback_arrows(call):
    '''
        КНОПКА СЛЕД И ПРЕД. ДЕНЬ
    '''
    if 'next' in call.data:
        sign = int(call.data.split('next')[1])
        changeDayOfGrades(call, sign)



@bot.callback_query_handler(func=lambda call: 'next' not in  call.data)
def callback(call):
    if call.data == 'login_error':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        get_login(call.message)
    
    
    if 'user' in call.data:
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?",
                       (str(call.message.chat.id),))
        res = cursor.fetchall()
        
        cursor.execute("DELETE FROM users WHERE user_id = ?",
                       (str(call.message.chat.id), ))
        conn.commit()
        conn.close()
        index = call.data.split()
        
        index = int(index[0][-1])
        
        parser_worker = DataParser()
        parser_worker.login(res[index][3], res[index][4])
        name = parser_worker.get_name()
        
        add_table_values(res[index][1], res[index][2],
                         res[index][3], res[index][4])
        del res[index]
        
        for i in res:
            add_table_values(i[1], i[2], i[3], i[4])
        
        buildMainMenu(call.message, name)
            
        
    '''
    
    ПРОЧИЕ ФУНКЦИИ
    
    '''
    if call.data == 'other':
        buildOtherMenu(call)
        
        
    if call.data == 'checkTimes':
        choose_reminder_fuction(call.message)
        
            
    if call.data == 'one_time_reminder|pass':
        reminder_message(call.message, 'None')
    
    if call.data == 'one_time_reminder|take_grades':
        reminder_message(call.message, 'take_grades')
        
    if call.data == 'many_time_reminder|pass' or\
        call.data == 'many_time_reminder|take_grades':
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM reminders WHERE user_id = ?",
                       (call.message.chat.id,))
        
        res = cursor.fetchone()
        function = [call.data.split("|")[-1], [], [], []]
        if res == None:    #[fuction, [days], [time], [text]]     
            cursor.execute("INSERT INTO reminders(user_id, reminds) VALUES (?, ?)",
                           (call.message.chat.id, str([function]),))
            conn.commit()
        else:
            cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                           (call.message.chat.id,))
            
            res = cursor.fetchone()
            x = ast.literal_eval(str(res[0]))
            x.append(function)
            
            cursor.execute("UPDATE reminders SET reminds = ? WHERE user_id = ?",
                           (str(x), call.message.chat.id, ))
            conn.commit()
            
        conn.close()
        
        chose_current_days(call.message)
    
    if call.data in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',\
                  'saturday', 'sunday', 'all_days']:
        
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                       (call.message.chat.id,))
        
        res = cursor.fetchone()
        
        x = ast.literal_eval(str(res[0]))
        curr_state = x[-1][1]
        
        #[fuction, [days], [time], [text]] 
        if call.data not in curr_state: 
            if call.data == 'all_days' and len(curr_state) != 7:
                curr_state =  ['monday', 'tuesday', 'wednesday', 'thursday',
                               'friday', 'saturday', 'sunday']
            
            else:
                if call.data == 'all_days' and len(curr_state) != 0:
                    curr_state =  []
            
            if call.data != 'all_days':
                curr_state.append(call.data)
            
        else:
            del curr_state[curr_state.index(call.data)]
        
        x[-1][1] = curr_state
        
        cursor.execute("UPDATE reminders SET reminds = ? WHERE user_id = ?",
                       (str(x), call.message.chat.id, ))
        conn.commit()
        
        conn.close()
        
        chose_current_days(call.message, curr_state)
        
    if call.data == 'take_grades' or call.data == 'pass':
        response = choose_reminder_fuction(call.message, call.data)
        if response != None:
            choose_day_or_time(call.message, response)
           
    if call.data == 'nxt_step_chooser':
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                       (call.message.chat.id,))
        
        res = cursor.fetchone()
        x = ast.literal_eval(str(res[0]))
        curr_state = x[-1][1]
        function = x[-1][0]
        reminder_set_time(call.message, curr_state, function, flg=True)
    
    if call.data == 'exitt':
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                       (call.message.chat.id,))
        
        res = cursor.fetchone()
        x = ast.literal_eval(str(res[0]))
        del x[-1]
        if len(x) == 0:
            cursor.execute("DELETE FROM reminders WHERE user_id = ?",
                           (call.message.chat.id,))
        else:
            cursor.execute("UPDATE reminders SET reminds = ? WHERE user_id = ?",
                           (str(x), call.message.chat.id, ))
        
        conn.commit()
        conn.close()
        buildMainMenu(call.message)
    '''
   
    МЕНЮ ОЦЕНOK
   
    '''
      
    if call.data == 'Grades':
        buidGradesMenu(call) 
    
    '''
    
    ОЦЕНКИ ЗА СЕГОДНЯ
    
    '''
    if call.data == 'check_grades_today':
        buildGradesToday(call.message)
     

    
    '''
    
    ОЦЕНКА В КАЛЕНДАРЕ
    
    '''
        
    if call.data == 'check_grades_get':
        buildCalendar(call.message)
    

    '''
    
    ТАБЕЛЬ УСПЕВАЕМОСТИ
    
    '''

    if call.data == 'year' or call.data == '1' or call.data == '2' or\
       call.data == '3' or call.data == '4':
        makeSchcedule(call, call.data)

    
    '''
    
    ГЛАВНОЕ МЕНЮ
    
    '''
    if call.data == 'mainmenu':
        buildMainMenu(call.message)
                   
    
    
    '''
    
    НАСТРОЙКИ
    
    '''
    if call.data == 'add_new':
        get_login(call.message)
    
    if call.data == 'change_usr':
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id=?",
                       (str(call.message.chat.id),))
        res = cursor.fetchall()        
        conn.close()
        choose_user(call, res)
        
    if call.data == 'Options':
        options = types.InlineKeyboardMarkup(row_width=1)
        
        add_user = types.InlineKeyboardButton(text='ㅤㅤㅤ✏ Добавить пользователяㅤㅤㅤ', callback_data='add_new')
        options.row(add_user)
        
        conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id=?",
                       (str(call.message.chat.id),))
        res = cursor.fetchall()
        conn.close()
        
        if len(res) != 1:
            change = types.InlineKeyboardButton(text='👨‍💻 Поменять аккаунт',
                                                callback_data='change_usr')
            options.row(change)
        
        
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='mainmenu')
        options.add(back)
        bot.edit_message_text('⚙ Настройки', call.message.chat.id,
                              call.message.message_id,
                              reply_markup=options)    
    
    
    '''
    
    ВЕТКА ВЫХОДА В НАСТРОЙКАХ
    
    '''   
	
    if call.data == 'exit':
        #parser_worker.logout() #удалять ли юзера из бд?
        bot.edit_message_text('⚙ Вы вышли из аккаунта, напишите "/start" чтобы войти снова',
                              call.message.chat.id, call.message.message_id)
    
    
    
    if call.data == 'Advertisment':
        markup = types.InlineKeyboardMarkup(row_width=1)
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='mainmenu')
        markup.add(back)        
        if is_admin_check(call.message.chat.id):
            mes = bot.send_message(call.message.chat.id,
                                   'Пришлите текст для рекламы\n!!!картинки потом, сначало текст',
                                   reply_markup=markup)
            adv = Adv()
            bot.register_next_step_handler(mes, advertisment, adv)
        else:
            bot.send_message(call.message.chat.id, 'Доступ запрещён!',
                             reply_markup=markup)
       
        
def buildCalendar(message):
    print(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())} --> ',
          message.chat.id, 'buildCalendar')
    now = datetime.datetime.now()
    bot.edit_message_text('🗓 Выберите нужную датуㅤㅤ', message.chat.id,
                              message.message_id,
                              reply_markup=calendar.create_calendar(
                                  name=calendar_1_callback.prefix,
                                  year=now.year,
                                  month=now.month,
                                  function="non",),)  
    
if __name__ == '__main__':
    bot.polling(none_stop=True)
