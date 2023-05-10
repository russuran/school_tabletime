import telebot
from telebot import types
from telebot_calendat import Calendar, CallbackData, RUSSIAN_LANGUAGE
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


from parser_main import DataParser

user_data = {}

class Adv:
    def __init__(self):
        self.text = None
        self.media = []



        
        
bot = telebot.TeleBot("5840280561:AAHIAYI_ubnbZFWITMNvxv1RScpfhBtz8dE", parse_mode='HTML')

DAYS = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
MOUNTS = ['января', 'февраля','мара', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
calendar = Calendar(language=RUSSIAN_LANGUAGE)

calendar_1_callback = CallbackData("calendar_1", "action", "year", "month", "day", "function")
calendar_2_callback = CallbackData("calendar_2", "action", "year", "month", "day", "function")

conn = sqlite3.connect('db/telebot_users', check_same_thread=False)
cursor = conn.cursor()

'''
reminders db format:
    [{user_id: [{type: dates: [wednessday, friday, etc...], time, text}, remind()]}]
'''


def reminder_message(message, func=None):
    now = datetime.datetime.now()
    print(func)
    bot.edit_message_text("Выберите дату для напоминания ✍ㅤ",
                          message.chat.id, message.message_id,
                          reply_markup=calendar.create_calendar(
                              name=calendar_2_callback.prefix,
                              year=now.year,
                              month=now.month,
                              function=func,),)  


def reminder_set_time(message, date, func):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Отмена', callback_data='mainmenu')
    markup.row(back) 
    bot.send_message(message.chat.id, 'Введите время (часы:минуты)', reply_markup=markup)
    bot.register_next_step_handler(message, reminder_set_name, date, func, message.text)


def reminder_set_name(message, date, func, time):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Отмена', callback_data='mainmenu', reply_markup=markup)
    markup.row(back)     
    bot.send_message(message.chat.id, 'Введите текст для напоминания (или напишите "-" чтобы оставить поле пустым')
    text = message.text if message.text != '-' else ''
    print(date, func, time, text)
    bot.register_next_step_handler(message, reminder_set, date, text, time, func)
 

def choose_day_or_time(message, func=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    print(f'one_time_reminder|{func}')
    back = types.InlineKeyboardButton(text='Разовое', callback_data=f'one_time_reminder|{func}')
    markup.row(back)
    
    back = types.InlineKeyboardButton(text='Ежедневное (в разработке)', callback_data='many_time_reminder1')
    markup.row(back)
    
    back = types.InlineKeyboardButton(text='⬅ Отмена', callback_data='mainmenu')
    markup.row(back)     
    bot.edit_message_text('Выберите тип напоминания', message.chat.id,
                          message.message_id,
                          reply_markup=markup)
    
    
def randomshit():
    markup = types.InlineKeyboardMarkup(row_width=1)
    monday = types.InlineKeyboardButton(text='Понедельник',
                                        callback_data='monday',
                                        reply_markup=markup)
    markup.row(monday)
    
    Tuesday  = types.InlineKeyboardButton(text='Вторник',
                                          callback_data='tuesday',
                                          reply_markup=markup)
    markup.row(Tuesday)
    
    Wednesday = types.InlineKeyboardButton(text='Среда',
                                           callback_data='wednesday',
                                           reply_markup=markup)
    markup.row(Wednesday)
    
    Thursday = types.InlineKeyboardButton(text='Четверг',
                                          callback_data='thursday',
                                          reply_markup=markup)
    markup.row(Thursday)
    
    Friday = types.InlineKeyboardButton(text='Пятница',
                                        callback_data='friday',
                                        reply_markup=markup)
    markup.row(Friday)
    
    Saturday = types.InlineKeyboardButton(text='Суббота',
                                          callback_data='saturday',
                                          reply_markup=markup)
    markup.row(Saturday)
    
    Sunday = types.InlineKeyboardButton(text='Воскресенье',
                                        callback_data='sunday',
                                        reply_markup=markup)
    markup.row(Sunday) 


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
    
    
def reminder_set(message, date, time, func, text):
    global user_data
    print(date, time, func, text)
    try:
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        tryagain = types.InlineKeyboardButton(text='🔄 Попробовать ещё раз',
                                              callback_data='checkTimes')
        markup.row(tryagain)     
        
        back = types.InlineKeyboardButton(text='⬅ Назад',
                                          callback_data='mainmenu')
        markup.row(back) 
        
        user_data[message.chat.id] = {'reminder_name': message.text}
        print(user_data)
        date = date.split('.')
        time = time.split(':')
        
        reminder_time = datetime.datetime(int(date[2]), int(date[1]),
                                          int(date[0]), int(time[0]),
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
            reminder_name = user_data[message.chat.id]['reminder_name']
            bot.send_message(message.chat.id,
                'Напоминание "{}" установлено на {}.'.format(reminder_name,
                                                             reminder_time))
            
            reminder_timer = threading.Timer(delta.total_seconds(),
                                             send_reminder,
                                             [message, reminder_name, text])
            reminder_timer.start()
            buildMainMenu(message)
    except Exception as e:
        print(e)             
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
def add_table_values(user_id, name, login, password):
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

def upd_cookies(login, cookie):
    cursor.execute('UPDATE users SET cookie = ? WHERE login = ?',
                   (cookie, login))
    conn.commit()

def new_parser(login):
    b = DataParser()
    pechenki, passw = cursor.execute('SELECT cookie, password FROM users WHERE login = ?',
                                     (login,)).fetchone()[0]
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
        cursor.execute('SELECT * FROM users WHERE user_id = ?',
                       (message.chat.id,))
        res = cursor.fetchall()
        if len(res):
            buildMainMenu(message, name=message.chat.first_name)
        else:
            bot.send_message(message.chat.id, 'Сначала нужно войти в аккаунт')
            get_login(message)


@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    if is_admin_check(message.chat.id):
        userid = message.text.split(" ")[1]
        cursor.execute("INSERT INTO admins(user_id) VALUES (?)",
                       (str(userid), ))
        conn.commit()
        bot.send_message(message.chat.id, 'Админ добавлен')


@bot.message_handler(commands=['delete_admin'])
def delete_admin(message):
    if is_admin_check(message.chat.id):
        userid = message.text.split(" ")[1]
        if is_admin_check(userid):
            cursor.execute("DELETE FROM admins WHERE user_id = ?",
                           (str(userid), ))
            conn.commit()
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
    cursor.execute("SELECT login, password FROM users WHERE user_id = ?",
                       [str(message.chat.id)])
    
    result = cursor.fetchall()
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
    cursor.execute("SELECT user_id FROM users")
    res = cursor.fetchall()
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
        print(call.data)
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
                    except Exception as e:
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





def buildMainMenu(message, name='', eco=False):
    markup = types.InlineKeyboardMarkup(row_width=1)

    item3 = types.InlineKeyboardButton('🎒 Расписание и оценки',
                                       callback_data='Grades'if not eco else 'Grades_eco')
    markup.row(item3)
    
    item1 = types.InlineKeyboardButton('🗓 Табель успеваемости',
                                       callback_data='year' if not eco else 'year_eco')
    markup.row(item1)
    
    item2 = types.InlineKeyboardButton('🏛 Прочие функции',
                                       callback_data='other')
    markup.row(item2)
    
    item4 = types.InlineKeyboardButton('⚙ Настройки',
                                       callback_data='Options' if not eco else 'Options_eco')
    markup.row(item4)
    a = "\n(Включен режим экономии трафика 🔋)"
    if name != '':
        res = f'✅ Рады видеть вас снова, {name.split(" ")[-1]}!' + "\n(Включен режим экономии трафика 🔋)" if eco else '✅ Рады видеть вас снова!'
    else:
        res = '✅ Рады видеть вас снова!'  + "\n(Включен режим экономии трафика 🔋)" if eco else '✅ Рады видеть вас снова!'
    try:
        bot.edit_message_text(res, message.chat.id, message.message_id,
                              reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, res, reply_markup=markup)



def is_admin_check(chat_id):
    cursor.execute("SELECT EXISTS(SELECT * FROM admins WHERE user_id = ?)",
                   (str(chat_id),))
    result = cursor.fetchone()
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
                                      callback_data='mainmenu' if not eco else 'mainmenu_eco')

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



        bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'),
                       caption=f'✅ Ваш табель успеваемости за {per.lower()}',
                       reply_markup=options)

        os.remove(f'{flname}.png')
    else:
        text = '\n'.join(list(map(lambda x: ' '.join(x), data[1:])))
        print(text)
        text = f'✅ Ваш табель успеваемости за {per.lower()}\n' + text
        bot.send_message(call.message.chat.id, text, reply_markup=options)
 

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
    back = types.InlineKeyboardButton(text='Назад', callback_data='mainmenu' if not eco else 'mainmenu_eco')
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
        try:
            if len(data) != 1:
                bot.send_photo(message.chat.id, open(f'{flname}.png', 'rb'),
                               caption='Ваше расписание на сегодня ✅',
                               reply_markup=options)
            else:
                bot.send_message('😯 В этот день нет уроков!', message.chat.id,
                                      message.message_id,
                                      reply_markup=options)
        except Exception as e:  #для напоминаний
            if len(data) != 1:
                bot.send_photo(message.chat.id, open(f'{flname}.png', 'rb'),
                               caption=f'{text} ✅',
                               reply_markup=options)

            else:
                bot.send_message(message.chat.id,
                                 f'😯 в этот день нет уроков!',
                                 reply_markup=options)

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
def changeDayOfGrades(call, sign, eco=False):
    options = types.InlineKeyboardMarkup(row_width=3)
    
    previous = types.InlineKeyboardButton(text='⬅'
                                          , callback_data=f'next{sign-1}' if not eco else f'next{sign-1}_eco')
    back = types.InlineKeyboardButton(text='Назад',
                                      callback_data='mainmenu' if not eco else 'mainmenu_eco')
    nextt = types.InlineKeyboardButton(text='➡',
                                       callback_data=f'next{sign+1}' if not eco else f'next{sign+1}_eco')

    options.add(previous, back, nextt)
    userdata = logging(call.message)
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

            bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=options)
        else:
            bot.send_message(call.message.chat.id, f'😯 В этот день ({DAYS[intDay]}, {date.day} {MOUNTS[date.month - 1]}) нет уроков!',

                                  reply_markup=options)

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
        print(e)
        bot.send_message(call.message.chat.id, res, reply_markup=markup)    
    

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
        changeDayOfGrades(call, sign, eco=eco)



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
        cursor.execute("SELECT * FROM users WHERE user_id = ?",
                       (str(call.message.chat.id),))
        res = cursor.fetchall()
        
        cursor.execute("DELETE FROM users WHERE user_id = ?",
                       (str(call.message.chat.id), ))
        conn.commit()
        
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
        
    if call.data == 'many_time_reminder':
        reminder_message(call.message, 'None')
        
    if call.data == 'take_grades' or call.data == 'pass':
        response = choose_reminder_fuction(call.message, call.data)
        if response != None:
            choose_day_or_time(call.message, response)
           
            
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
                   
    
    
    '''
    
    НАСТРОЙКИ
    
    '''
    if call.data == 'add_new':
        get_login(call.message)
    
    if call.data == 'change_usr':
        cursor.execute("SELECT * FROM users WHERE user_id=?",
                       (str(call.message.chat.id),))
        res = cursor.fetchall()        
        
        choose_user(call, res)
        
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

    cursor.execute("SELECT * FROM users WHERE user_id=?",
                   (str(call.message.chat.id),))
    res = cursor.fetchall()

    if len(res) != 1:
        change = types.InlineKeyboardButton(text='👨‍💻 Поменять аккаунт',
                                            callback_data='change_usr')
        options.row(change)
    eco_tr = types.InlineKeyboardButton(text='включить режим экономии трафика 🔋' if not eco else 'выключить режим экономии трафика 🪫', callback_data='traffic' if not eco else 'traffic_eco')
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
    bot.polling(none_stop=True)
