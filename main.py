import telebot
from telebot import types
from telebot_calendat import Calendar, CallbackData, RUSSIAN_LANGUAGE
from telebot.types import CallbackQuery, ReplyKeyboardRemove
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
DAYS_SHORTEND = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
DAYS_ENG = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
            "sunday"]
MOUNTS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
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
'''
reminders db format:
    [{user_id: [{type: dates: [wednessday, friday, etc...], time, text}, remind()]}]
'''

def reminder_message(message, func=None, upd=0, eco=False):
    now = datetime.datetime.now()
    print(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())} --> ',
          message.chat.id, 'reminder')
    today = datetime.date.today()
    if abs(upd):
        days = datetime.timedelta(days=30 * abs(upd))
        if upd > 0:
            cur = today + days
        elif upd < 0:
            cur = today - days
    else:
        cur = today
    bot.edit_message_text("Выберите дату для напоминания ✍ㅤ",
                          message.chat.id, message.message_id,
                          reply_markup=calendar.create_calendar(
                              name=calendar_2_callback.prefix,
                              year=cur.year,
                              month=cur.month,
                              function=f'{func}.{upd}' if not eco else f'{func}.{upd}'+'_eco',),)


def reminder_set_time(message, date=None, func=None, flg=False, eco=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Отмена', callback_data='exitt' if not eco else 'exitt_eco')
    markup.row(back)
    bot.send_message(message.chat.id, 'Введите время (часы:минуты)',
                     reply_markup=markup)

    bot.register_next_step_handler(message, reminder_set_name, date, func,
                                   message.text, flg, eco=eco)

def reminder_set_name(message, date, func, time, flg=False, eco=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='exitt' if not eco else 'exitt_eco', reply_markup=markup)
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

    bot.register_next_step_handler(message, reminder_set, date, text, time, func, eco=eco)
 

def choose_day_or_time(message, func=None, eco=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='1⃣ Разовое',
                                      callback_data=f'one_time_reminder|{func}' if not eco else f'one_time_reminder|{func}_eco')
    markup.row(back)

    back = types.InlineKeyboardButton(text='🔂 Ежедневное',
                                      callback_data=f'many_time_reminder|{func}' if not eco else f'many_time_reminder|{func}_eco')
    markup.row(back)

    back = types.InlineKeyboardButton(text='⬅ Отмена',
                                      callback_data='mainmenu' if not eco else 'mainmenu_eco')
    markup.row(back)     
    bot.edit_message_text('✍ Выберите тип напоминания:', message.chat.id,
                          message.message_id,
                          reply_markup=markup)

def chose_current_days(message, days=None, eco=False):
    markup = types.InlineKeyboardMarkup(row_width=2)

    data = ['⭕ Понедельник', '⭕ Вторник', '⭕ Среда', '⭕ Четверг',
            '⭕ Пятница', '⭕ Суббота', '⭕ Воскресенье', '⭕ Все дни']

    data_calls = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                  'saturday', 'sunday', 'all_days']
    if eco:
        data_calls = [x + '_eco' for x in data_calls]

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
                                         callback_data='nxt_step_chooser' if not eco else 'nxt_step_chooser_eco', reply_markup=markup)
    markup.row(procced)
    exitt = types.InlineKeyboardButton(text='⬅ Отмена',
                                       callback_data='exitt' if not eco else 'exitt_eco', reply_markup=markup)
    markup.row(exitt)
    try:
        bot.edit_message_text(
            '✍ Выберите дни (нажмите ещё раз, чтобы убрать день), после чего нажмите "Далее", при нажатии на день недели, подождите, пока он отметится :)',
            message.chat.id,
            message.message_id,
            reply_markup=markup)
    except Exception as e:
        pass



def choose_reminder_fuction(message, fix=None, eco=False):
    if fix == 'take_grades':
        return 'take_grades' if not eco else 'take_grades_eco'
    elif fix == 'pass':
        return 'pass' if not eco else 'pass_eco'
    elif fix == 'take_grades_xtra':
        return 'take_grades_xtra' if not eco else 'take_grades_xtra_eco'
    elif fix == 'table_grades':
        return 'table_grades' if not eco else 'table_grades_eco'


    else:    
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        back = types.InlineKeyboardButton(text='📆 Расписание на выбранный день',
                                          callback_data='take_grades' if not eco else 'take_grades_eco',
                                          reply_markup=markup)
        markup.row(back)

        back = types.InlineKeyboardButton(text='📆 Расписание на следующий день',
                                          callback_data='take_grades_xtra' if not eco else 'take_grades_eco',
                                          reply_markup=markup)
        markup.row(back)

        back = types.InlineKeyboardButton(text='📆 Табель успеваемости',
                                          callback_data='table_grades' if not eco else 'take_grades_eco',
                                          reply_markup=markup)
        markup.row(back)

        back = types.InlineKeyboardButton(text='🚫 Без функции',
                                          callback_data='pass' if not eco else 'pass_eco',
                                          reply_markup=markup)
        markup.row(back)
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='choosePartReminder' if not eco else 'choosePartReminder_eco',
                                          reply_markup=markup)
        markup.row(back)
        bot.edit_message_text('✍ Выберите функцию:ㅤㅤㅤ', message.chat.id,
                              message.message_id,
                              reply_markup=markup)

    return None
    
    
def reminder_set(message, date, time, func, text, flg=False, rl_text=None, eco=False):
    global user_data

    try:
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        tryagain = types.InlineKeyboardButton(text='🔄 Попробовать ещё раз',
                                              callback_data='checkTimes' if not eco else 'checkTimes_eco')
        markup.row(tryagain)     
        
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='mainmenu' if not eco else 'mainmenu_eco')
        markup.row(back)
        if rl_text == None:
            user_data[message.chat.id] = {'reminder_name': message.text}
        else:
            user_data[message.chat.id] = {'reminder_name': rl_text}
        reminder_name = user_data[message.chat.id]['reminder_name']
        try:
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
                               (str(x), message.chat.id,))
                conn.commit()
                conn.close()
        except Exception:
            pass

        reminder_name = user_data[message.chat.id]['reminder_name']
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
                                                      callback_data='choosePartReminder' if not eco else 'choosePartReminder_eco')
                markup.row(tryagain)
                back = types.InlineKeyboardButton(text='⬅ Назад',
                                                  callback_data='mainmenu' if not eco else 'mainmenu_eco')
                markup.row(back)
                bot.send_message(message.chat.id,
                                 'Вы ввели прошедшую дату, попробуйте еще раз.',
                                 reply_markup=markup)
            else:
                if flg == False:
                    reminder_timer = threading.Timer(delta.total_seconds(),
                                                     send_reminder,
                                                     [message, reminder_name, text, eco])
                    text = f'🏛 Напоминание установлено на {int(date[0])} {MOUNTS[reminder_time.month]}, {time[0]}:{time[1]}!'
                    bot.send_message(message.chat.id, text)
                    buildMainMenu(message, eco=eco)
                else:
                    reminder_timer = threading.Timer(delta.total_seconds(),
                                                     send_reminder_multiple,
                                                     [message, reminder_name, text, date, time, rl_text, eco])


                reminder_timer.start()


        else:
            saved_dates = date
            for i in date:
                date = get_next_dayofweek_datetime(datetime.datetime.now(), i)
                days = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday", "sunday"]

                nowdate = datetime.datetime.now()
                if i == days[nowdate.weekday()]:
                    time = time.split(':')
                    another_date = datetime.datetime(nowdate.year, nowdate.month,
                                                     nowdate.day, int(time[0]), int(time[1]))
                    if (another_date - nowdate).total_seconds() > 0:
                        date = datetime.datetime.now()
                reminder_set(message, str(date.date()), time, func, text,
                             True, message.text)
            if len(saved_dates) > 1:
                days_to_print = ''
                for i in saved_dates:
                    days_to_print += f'{DAYS_SHORTEND[DAYS_ENG.index(i)]}, '
                text = f"🏛 Ваши еженедельные напоминания на {days_to_print[:-2]} установлены"
            else:
                text = f"🏛 Ваше еженедельное напоминание на {DAYS[DAYS_ENG.index(days[date.weekday()])]} установлено"

            bot.send_message(message.chat.id, text)
            buildMainMenu(message, eco=eco)

    except Exception:
        print(traceback.format_exc())
        bot.send_message(message.chat.id,
                'Вы ввели неверный формат даты и времени, попробуйте еще раз.',
                reply_markup=markup)


def send_reminder(message, reminder_name, func, eco=False):
    text = '🏛 Напоминание' if reminder_name == '-' else '🏛 Напоминание "{}"!'.format(reminder_name)
    if func == 'take_grades':
        buildGradesToday(message, text, eco=eco)

    elif func == 'pass':
        bot.send_message(message.chat.id,
                    text)
    elif func == 'take_grades_xtra':
        changeDayOfGrades(message, 1, eco=eco)

    elif func == 'table_grades':
        makeSchcedule('year', eco=eco)
    buildMainMenu(message, eco=eco)

def send_reminder_multiple(message, reminder_name, func, date, time, rl_text, eco):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()

    cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                   (message.chat.id,))

    res = cursor.fetchone()

    conn.close()
    dats = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                  'saturday', 'sunday', 'all_days']

    if res != None:
        x = ast.literal_eval(str(res[0]))
        for i in x:

            wk = dats[datetime.datetime(int(date[0]), int(date[1]), int(date[2])).weekday()]
            t = str(time[0]) + ':' + str(time[1])
            if func == i[0] and wk in i[1] and t == i[2][0] and rl_text == i[-1][0]:
                text = '🏛 Еженедельное напоминание' if rl_text == '-' else '🏛 Еженедельное напоминание "{}"!'.format(
                    rl_text)
                if func == 'take_grades':
                    buildGradesToday(message, text, eco=eco)

                elif func == 'take_grades_xtra':
                    changeDayOfGrades(message, 1, eco=eco)

                elif func == 'table_grades':
                    makeSchcedule('year', eco=eco)
                else:
                    bot.send_message(message.chat.id, text)
                date = str(datetime.datetime(int(date[0]), int(date[1]), int(date[2])).date() + timedelta(days=7))
                time = t
                reminder_set(message, date, time, func, rl_text, True, rl_text)
    buildMainMenu(message, eco=eco)


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
        except Exception:
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
    except Exception:
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
        data = call.data.split(':')
        if data[-1] == '!':
            funct = data[4]
        else:
            funct = data[5]
        action = data[1]
        eco = False
        if 'eco' in funct:
            eco = True
            funct = funct[:-4]
        funct, upd = funct.split('.')
        if action == "DAY":
            date = datetime.datetime(int(data[2]), int(data[3]), int(data[4]))


            options = types.InlineKeyboardMarkup(row_width=1)
            
            back = types.InlineKeyboardButton(text='⬅ Назад',
                                              callback_data='mainmenu'if not eco else 'mainmenu_eco')
            
            options.add(back)
            

            reminder_set_time(call.message, date.strftime('%d.%m.%Y'), funct, eco=eco)
                
                
        elif action == "CANCEL":
            buildMainMenu(call.message, eco=eco)
        elif action == 'PREVIOUS-MONTH':
            reminder_message(call.message, eco=eco, upd=int(upd)-1, func=funct)
        elif action == 'NEXT-MONTH':
            reminder_message(call.message, eco=eco, upd=int(upd)+1, func=funct)
            
            
@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_1_callback.prefix))	    
def callback_inline(call: CallbackQuery):

        action = call.data.split(calendar_1_callback.sep)[1]

        if action == "DAY":
            name, action, year, month, day, function = call.data.split(calendar_1_callback.sep)
            function = function.split('.')[0]
            date = calendar.calendar_query_handler(
                bot=bot,
                call=call,
                name=name,
                action=action,
                year=year,
                month=month,
                day=day
            )
            options = types.InlineKeyboardMarkup(row_width=1)
            
            back = types.InlineKeyboardButton(text='⬅ Назад',
                                              callback_data='mainmenu' if function!='eco' else 'mainmenu_eco')
            
            options.add(back)
            

            
            userdata = logging(call.message)
            login, password = userdata[0][0], userdata[0][1]
            parser_worker = DataParser()
            parser_worker.login(login, password)
            data = parser_worker.get_day_marks(str(int((time.mktime(date.timetuple())))))
            parser_worker.logout()
            intDay = date.weekday()
            if function != 'eco':
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
                if len(data) != 1:
                    bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'),
                                   caption=f'🎒 Ваше расписание на {DAYS[intDay]} ({date.day} {MOUNTS[date.month - 1]}) ✅',
                                   reply_markup=options)
                else:
                    try:
                        bot.send_message(call.message.chat.id,
                                         f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',
                                         reply_markup=options)
                    except Exception:
                        bot.send_message(call.message.chat.id,
                                         f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',

                                         reply_markup=options)

                os.remove(f'{flname}.png')
            else:
                if len(data) != 1:
                    tab = '<b>-----------------------------------------------</b>\n'
                    text = f'<i>🎒 Ваше расписание на {DAYS[intDay]} ({date.day} {MOUNTS[date.month - 1]}) ✅</i>'  + tab
                    for i in data[1:]:
                        t ='—'.join(i[0].split('\n-\n'))
                        text += f'<b>{t}\n</b>'
                        predmet = f'<i><b>{i[1]}\n</b></i>'
                        text += predmet
                        home = f'<a>{i[2]}\n</a>' if i[2] else '\n'
                        text += home
                        marks = f'<b>{i[-1]}\n</b>' if i[-1] else '\n'
                        text += marks
                        comm = f'<b>{i[-2]}\n</b>' if i[-2] else '\n'
                        text += comm
                        text += tab

                    bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=options)
                else:
                    bot.send_message(call.message.chat.id,
                                 f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',

                                 reply_markup=options)
            
        
        elif action == "CANCEL":
            buildMainMenu(call.message, eco=call.data.split(':')[4].split('.')[0]=='eco')
        elif action == 'PREVIOUS-MONTH':
            buildCalendar(call.message, eco=call.data.split(':')[4].split('.')[0]=='eco', upd=int(call.data.split(':')[4].split('.')[1])-1)
        elif action == 'NEXT-MONTH':
            buildCalendar(call.message, eco=call.data.split(':')[4].split('.')[0]=='eco', upd=int(call.data.split(':')[4].split('.')[1])+1)





def buildMainMenu(message, name='', eco=False, editt=True):
    markup = types.InlineKeyboardMarkup(row_width=1)

    item3 = types.InlineKeyboardButton('🎒 Расписание и оценки',
                                       callback_data='Grades'if not eco else 'Grades_eco')
    markup.row(item3)
    
    item1 = types.InlineKeyboardButton('🗓 Табель успеваемости',
                                       callback_data='year' if not eco else 'year_eco')
    markup.row(item1)
    
    item2 = types.InlineKeyboardButton('🏛 Прочие функции',
                                       callback_data='other' if not eco else 'other_eco')
    markup.row(item2)
    
    item4 = types.InlineKeyboardButton('⚙ Настройки',
                                       callback_data='Options' if not eco else 'Options_eco')
    markup.row(item4)

    if name != '':
        res = f'✅ Рады видеть вас снова, {name.split(" ")[-1]}!' + "\n(Включен режим экономии трафика 🔋)" if eco else '✅ Рады видеть вас снова!'
    else:
        res = '✅ Рады видеть вас снова!'  + "\n(Включен режим экономии трафика 🔋)" if eco else '✅ Рады видеть вас снова!'
    try:
        if editt:
            bot.edit_message_text(res, message.chat.id, message.message_id,
                              reply_markup=markup)
        else:
            bot.send_message(message.chat.id, res, reply_markup=markup)
    except Exception:
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
            
            
def makeSchcedule(call, period, eco=False):
    options = types.InlineKeyboardMarkup(row_width=1)
        

    
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
        option = types.InlineKeyboardButton(i[0], callback_data=i[1] if not eco else i[1]+'_eco')
        options.add(option)
    per = list(periods.keys())[list(periods.values()).index(period)]
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='mainmenur' if not eco else 'mainmenur_eco')

    options.add(back)
    if not eco:
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

        try:
            bot.edit_message_media(chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   media=types.InputMediaPhoto(open(f'{flname}.png', 'rb'),
                                                               caption=f'✅ Ваш табель успеваемости за {per.lower()}'),
                                   reply_markup=options)
        except Exception:
            bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'),
                           caption=f'✅ Ваш табель успеваемости за {per.lower()}',
                           reply_markup=options)

        os.remove(f'{flname}.png')
    else:
        if period != 'year':
            data = data[1:]
            tab = '<b>-----------------------------------------------</b>\n'
            text = f'<i>✅ Ваш табель успеваемости за {per.lower()}\n</i>' + tab
            for i in data:
                predmet = f'<i><b>{i[0]}\n</b></i>'
                text += predmet
                text += f'<a>{i[1]}\n</a>' if i[2] else ''
                sr = f'<b>{i[2]} ➡ {i[3]}\n</b>' if i[2] else '—\n'
                text+=sr
                text+=tab
                try:
                    bot.edit_message_text(text, call.message.chat.id,
                                          call.message.message_id, parse_mode='HTML',
                                          reply_markup=options)
                except Exception:
                    pass
        else:
            text = '\n'.join(list(map(lambda x: '\t'.join(x), data[1:])))

            text = f'✅ Ваш табель успеваемости за {per.lower()}\n' + text
            try:

                bot.edit_message_text(text, call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=options)
            except Exception:
                pass
 

def buidGradesMenu(call, eco=False):
    grades = types.InlineKeyboardMarkup(row_width=1)
    
    grades_today = types.InlineKeyboardButton(text='🗓 Оценки за сегодня',
                                            callback_data='check_grades_today' if not eco else 'check_grades_today_eco')
    grades_get = types.InlineKeyboardButton(text='📆 Выбрать дату',
                                            callback_data='check_grades_get' if not eco else 'check_grades_get_eco')
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                            callback_data='mainmenu' if not eco else 'mainmenu_eco')
    
    grades.add(grades_today, grades_get, back)
    if eco:
        bot.edit_message_text('🎒 Просмотр оценок'+ "\n(Включен режим экономии трафика 🔋)", call.message.chat.id,
                          call.message.message_id,
                          reply_markup=grades)
    else:
        bot.edit_message_text('🎒 Просмотр оценок', call.message.chat.id,
                              call.message.message_id,
                              reply_markup=grades)
    
    
def buildGradesToday(message, text='', eco=False):
    options = types.InlineKeyboardMarkup(row_width=3)
    
    previous = types.InlineKeyboardButton(text='⬅', callback_data='next-1' if not eco else 'next-1_eco')
    back = types.InlineKeyboardButton(text='Назад', callback_data='mainmenur' if not eco else 'mainmenur_eco')
    nextt = types.InlineKeyboardButton(text='➡', callback_data='next1' if not eco else 'next1_eco')
    
    options.add(previous, back, nextt)
    
    
    userdata = logging(message)
    login, password = userdata[0][0], userdata[0][1]         
    parser_worker = DataParser()
    parser_worker.login(login, password)
    data = parser_worker.get_day_marks('')
    parser_worker.logout()
    
    print(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())} --> ',
          login, 'buildGradesToday')
    if not eco:
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
        if text == '':
            if len(data) != 1:
                text = 'Ваше расписание на сегодня ✅'
            else:
                text = '😯 В этот день нет уроков!'

        bot.send_photo(message.chat.id, open(f'{flname}.png', 'rb'),
                       caption=f'{text}', reply_markup=options)

        os.remove(f'{flname}.png')
    else:
        if len(data) != 1:
            tab = '<b>-----------------------------------------------</b>\n'
            text = f'<i>🎒 Ваше расписание на сегодня ✅</i>' + tab
            for i in data[1:]:
                t = '—'.join(i[0].split('\n-\n'))
                text += f'<b>{t}\n</b>'
                predmet = f'<i><b>{i[1]}\n</b></i>'
                text += predmet
                home = f'<a>{i[2]}\n</a>' if i[2] else '\n'
                text += home
                marks = f'<b>{i[-1]}\n</b>' if i[-1] else '\n'
                text += marks
                comm = f'<b>{i[-2]}\n</b>' if i[-2] else '\n'
                text += comm
                text += tab

            bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=options)
        else:
            bot.send_message( message.chat.id, '😯 В этот день нет уроков!',

                                  reply_markup=options)
def changeDayOfGrades(message, sign, eco=False):
    options = types.InlineKeyboardMarkup(row_width=3)
    
    previous = types.InlineKeyboardButton(text='⬅'
                                          , callback_data=f'next{sign-1}' if not eco else f'next{sign-1}_eco')
    back = types.InlineKeyboardButton(text='Назад',
                                      callback_data='mainmenu' if not eco else 'mainmenu_eco')
    nextt = types.InlineKeyboardButton(text='➡',
                                       callback_data=f'next{sign+1}' if not eco else f'next{sign+1}_eco')

    options.add(previous, back, nextt)
    userdata = logging(message)
    login, password = userdata[0][0], userdata[0][1]
    parser_worker = DataParser()
    parser_worker.login(login, password)
    date = datetime.datetime.now()
    date = date + 1 * sign * datetime.timedelta(days=1)
    data = parser_worker.get_day_marks(str(int((time.mktime(date.timetuple())))))
    parser_worker.logout()
    intDay = date.weekday()
    if not eco:
        t = Texttable()

           #fixxxx


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

        if len(data) != 1:
            try:
                bot.edit_message_media(chat_id=message.chat.id,
                                       message_id=message.message_id,
                                       media=types.InputMediaPhoto(open(f'{flname}.png', 'rb'),
                                                                   caption=f'🎒 Ваше расписание на {DAYS[intDay]} ({date.day} {MOUNTS[date.month - 1]}) ✅'),
                                       reply_markup=options)

            except Exception:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_photo(message.chat.id,
                               open(f'{flname}.png', 'rb'),
                               caption=f'🎒 Ваше расписание на {DAYS[intDay]} ({date.day} {MOUNTS[date.month - 1]}) ✅',
                               reply_markup=options)
        else:
            try:
                bot.edit_message_text(
                    f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',
                    message.chat.id, message.message_id,
                    reply_markup=options)

            except Exception:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id,
                                 f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',

                                 reply_markup=options)

        os.remove(f'{flname}.png')
    else:
        if len(data) != 1:
            tab = '<b>-----------------------------------------------</b>\n'
            text = f'<i>🎒 Ваше расписание на {DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]} ✅</i>' + tab
            for i in data[1:]:
                t = '—'.join(i[0].split('\n-\n'))
                text += f'<b>{t}\n</b>'
                predmet = f'<i><b>{i[1]}\n</b></i>'
                text += predmet
                home = f'<a>{i[2]}\n</a>' if i[2] else '\n'
                text += home
                marks = f'<b>{i[-1]}\n</b>' if i[-1] else '\n'
                text += marks
                comm = f'<b>{i[-2]}\n</b>' if i[-2] else '\n'
                text += comm
                text += tab

            try:
                bot.edit_message_text(text, chat_id=message.chat.id,
                                       message_id=message.message_id, reply_markup=options)

            except Exception:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_photo(message.chat.id,
                               text,
                               reply_markup=options)
        else:
            try:
                bot.edit_message_text(f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!', chat_id=message.chat.id,
                                       message_id=message.message_id, reply_markup=options)

            except Exception:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_photo(message.chat.id,
                               f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',
                               reply_markup=options)


def buildOtherMenu(call, name='', eco=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    item3 = types.InlineKeyboardButton('⏳ Напоминания',
                                       callback_data='choosePartReminder' if not eco else 'choosePartReminder_eco')
    markup.row(item3)
    
    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='mainmenu' if not eco else 'mainmenu_eco')
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
        print(e)
        bot.send_message(call.message.chat.id, res, reply_markup=markup)    

def buildDaysData(message, data, eco=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    if data != None:
        for i in range(len(data)):
            row_data = getRowData(data[i])
            dat = types.InlineKeyboardButton(text=f'{row_data}',
                                                  callback_data=f'deldat|{i}' if not eco else f'deldat|{i}_eco',
                                                  reply_markup=markup)
            markup.row(dat)


    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='choosePartReminder' if not eco else 'choosePartReminder_eco',
                                      reply_markup=markup)
    markup.row(back)

    try:
        bot.edit_message_text('✍ Нажмите на напоминане, чтобы удалить его',
                              message.chat.id, message.message_id,
                              reply_markup=markup)
    except Exception:
        bot.edit_message_text('✍ Нaжмите на напоминане, чтобы удалить его',
                              message.chat.id, message.message_id,
                              reply_markup=markup)

def getRowData(row):
    row_data = ''
    if row[0] == 'take_grades':
        row_data += 'Оценки; '
    elif row[0] == 'table_grades':
        row_data += 'Табель усп.; '

    elif row[0] == 'take_grades_xtra':
        row_data += 'Оценки-сл.день; '
    else:
        row_data += 'Нет функц. '

    for i in row[1]:
        row_data += f'{DAYS_SHORTEND[DAYS_ENG.index(i)]}, '

    row_data = row_data[:-2]

    row_data += f'; {row[2][0]}; '

    if row[3] != '-':
        row_data += f'"{row[3][0]}"'

    return row_data


def deleteRemindByIndex(call, eco=False):
    ind = call.data.split("|")

    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()

    cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                   (call.message.chat.id,))

    res = cursor.fetchone()
    x = ast.literal_eval(str(res[0]))
    del x[int(ind[-1])]

    if len(x) == 0:
        cursor.execute("DELETE FROM reminders WHERE user_id = ?",
                           (call.message.chat.id,))
    else:
        cursor.execute("UPDATE reminders SET reminds = ? WHERE user_id = ?",
                          (str(x), call.message.chat.id, ))

    conn.commit()
    conn.close()
    buildDaysData(call.message, x, eco=eco)


def buildRemindersDeleteMenu(call, eco=False):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()

    cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                   (call.message.chat.id,))

    res = cursor.fetchone()
    conn.close()

    if res != None:
        x = ast.literal_eval(str(res[0]))
        buildDaysData(call.message, x, eco=eco)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='choosePartReminder' if not eco else 'mainmenu_eco')  # Тут внимательно дату смотри
        markup.row(back)

        bot.edit_message_text('Кажется, у вас нет активных напоминаний',
                              call.message.chat.id, call.message.message_id,
                              reply_markup=markup)


def addDaysToCurrentReminder(call):
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

    return curr_state

def chooseFunc(call, eco=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton('🎆 Добавить напоминания',
                                       callback_data='checkTimes' if not eco else 'checkTimes_eco')
    markup.row(item1)

    item1 = types.InlineKeyboardButton('🎇 Удалить напоминания',
                                       callback_data='deldat' if not eco else 'deldat_eco')
    markup.row(item1)

    item1 = types.InlineKeyboardButton('⬅ Назад',
                                       callback_data='other' if not eco else 'other_eco')
    markup.row(item1)

    bot.edit_message_text('Выберите действие  ✍',
                          call.message.chat.id, call.message.message_id,
                          reply_markup=markup)

def createCurrReminder(call):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reminders WHERE user_id = ?",
                   (call.message.chat.id,))

    res = cursor.fetchone()
    function = [call.data.split("|")[-1], [], [], []]

    if res == None:
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


def getNextStepData(call):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()

    cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                   (call.message.chat.id,))

    res = cursor.fetchone()
    x = ast.literal_eval(str(res[0]))
    curr_state = x[-1][1]
    function = x[-1][0]

    return curr_state, function


def deleteCurrReminder(call):
    conn = sqlite3.connect('db/telebot_users', check_same_thread=False, timeout=15)
    cursor = conn.cursor()

    cursor.execute("SELECT reminds FROM reminders WHERE user_id = ?",
                   (call.message.chat.id,))

    res = cursor.fetchone()
    if res != None:
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


def addNewUser(call):
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

    return name




@bot.callback_query_handler(func=lambda call: 'next' in call.data)
def callback_arrows(call):
    '''
        КНОПКА СЛЕД И ПРЕД. ДЕНЬ
    '''
    eco = False
    if 'eco' in call.data:
        eco = True
        call.data = call.data[:-4]
    if 'next' in call.data:
        sign = int(call.data.split('next')[1])
        changeDayOfGrades(call.message, sign, eco=eco)



@bot.callback_query_handler(func=lambda call: 'next' not in  call.data)
def callback(call):
    eco = False
    if 'eco' in call.data:
        eco = True
        call.data = call.data[:-4]

    if call.data == 'login_error':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        get_login(call.message)
    
    
    if 'user' in call.data:
        name = addNewUser(call)
        buildMainMenu(call.message, name)
            
        
    '''
    
    ПРОЧИЕ ФУНКЦИИ
    
    '''
    if call.data == 'other':
        buildOtherMenu(call, eco=eco)

    if 'deldat|' in call.data:
        deleteRemindByIndex(call, eco=eco)

    if call.data == 'deldat':
        buildRemindersDeleteMenu(call, eco)
        
    if call.data == 'checkTimes':
        choose_reminder_fuction(call.message, eco=eco)

    if 'one_time_reminder|' in call.data:
        function_to_pass = call.data.split("|")[-1]
        reminder_message(call.message, function_to_pass, eco=eco)

    if 'many_time_reminder|' in call.data:
        createCurrReminder(call)
        chose_current_days(call.message, eco=eco)

    if call.data in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'all_days']:

        curr_state = addDaysToCurrentReminder(call)
        if eco:
            curr_state = [x+'_eco' for x in curr_state]
        chose_current_days(call.message, curr_state, eco=eco)

    if call.data in ['take_grades', 'pass', 'take_grades_xtra', 'table_grades']:
        response = choose_reminder_fuction(call.message, call.data)
        if 'eco' in response:
            eco = True
            response = response[:-4]
        if response != None:
            choose_day_or_time(call.message, response, eco=eco)

    if call.data == 'nxt_step_chooser':
        curr_state, function = getNextStepData(call)
        reminder_set_time(call.message, curr_state, function, flg=True, eco=eco)

    if call.data == 'exitt':
        deleteCurrReminder(call)
        buildMainMenu(call.message, eco=eco)

    if call.data == 'choosePartReminder':
        chooseFunc(call, eco=eco)

    '''
   
    МЕНЮ ОЦЕНOK
   
    '''
      
    if call.data == 'Grades':
        buidGradesMenu(call, eco=eco)
    
    '''
    
    ОЦЕНКИ ЗА СЕГОДНЯ
    
    '''
    if call.data == 'check_grades_today':
        buildGradesToday(call.message, eco=eco)
     

    
    '''
    
    ОЦЕНКА В КАЛЕНДАРЕ
    
    '''
        
    if call.data == 'check_grades_get':
        buildCalendar(call.message, eco=eco)
    

    '''
    
    ТАБЕЛЬ УСПЕВАЕМОСТИ
    
    '''

    if call.data == 'year' or call.data == '1' or call.data == '2' or\
       call.data == '3' or call.data == '4':
        makeSchcedule(call, call.data, eco=eco)

    
    '''
    
    ГЛАВНОЕ МЕНЮ
    
    '''
    if call.data == 'mainmenu':
        buildMainMenu(call.message, eco=eco)
    if call.data == 'mainmenur':
        buildMainMenu(call.message, eco=eco, editt=False)
                   

    
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
        
        choose_user(call, res)
        conn.close()

    if call.data == 'Options':
        buildOptionsmenu(call, eco=eco)

    if call.data == 'traffic':
        if eco:
            buildMainMenu(call.message, eco=False)
        else:
            buildMainMenu(call.message, eco=True)

    
    
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

def buildOptionsmenu(call, eco=False):
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
    eco_tr = types.InlineKeyboardButton(
        text='🔋 Вкл. режим экономии трафика' if not eco else '🪫 Выкл. режим экономии трафика',
        callback_data='traffic' if not eco else 'traffic_eco')
    options.add(eco_tr)

    back = types.InlineKeyboardButton(text='⬅ Назад',
                                      callback_data='mainmenu' if not eco else 'mainmenu_eco')
    options.add(back)
    bot.edit_message_text('⚙ Настройки', call.message.chat.id,
                          call.message.message_id,
                          reply_markup=options)


def buildCalendar(message, eco=False, upd=0):
    print(f'{time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())} --> ',
          message.chat.id, 'buildCalendar')
    today = datetime.date.today()
    if abs(upd):
        days = datetime.timedelta(days=30*abs(upd))
        if upd > 0:
            cur = today + days
        elif upd < 0:
            cur = today - days
    else:
        cur = today
    bot.edit_message_text('🗓 Выберите нужную датуㅤㅤ', message.chat.id,
                              message.message_id,
                              reply_markup=calendar.create_calendar(
                                  name=calendar_1_callback.prefix,
                                  year=cur.year,
                                  month=cur.month,
                                  function=f"non.{upd}" if not eco else f'eco.{upd}',),)


if __name__ == '__main__':
    bot.infinity_polling()
