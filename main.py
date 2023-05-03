import telebot
from telebot import types
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
from telebot.types import ReplyKeyboardRemove, CallbackQuery 
from texttable import Texttable
import datetime
from PIL import Image, ImageFont, ImageDraw
import os
import time
import sqlite3
from random import randint


from parser_main import DataParser


class Adv:
    def __init__(self):
        self.text = None
        self.media = []

bot = telebot.TeleBot("6040676784:AAF157wL-6d9Cla06BjP-2FPuT-UcRK6iZA", parse_mode='HTML')

calendar = Calendar(language=RUSSIAN_LANGUAGE)
calendar_1_callback = CallbackData("calendar_1", "action", "year", "month", "day")

conn = sqlite3.connect('db/telebot_users', check_same_thread=False)
cursor = conn.cursor()

def add_table_values(user_id, name, login, password):
    cursor.execute('SELECT * FROM users WHERE user_id = ? AND login = ?', (user_id, login, ))
    res = cursor.fetchall()
    if len(res) == 0:
        cursor.execute('INSERT INTO users (user_id, name, login, password) VALUES (?, ?, ?, ?)', (user_id, name, login, password))
        conn.commit()
    else:
        #markup = types.InlineKeyboardMarkup(row_width=1)
        #back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        #markup.row(back)
        bot.send_message(user_id, 'Такой пользователь уже добавлен в ваш аккаунт ⚙', reply_markup=markup)
        
@bot.message_handler(commands=['start', 'Войти'])
def on_start(message):
    if is_admin_check(message.chat.id):
        markup = show_admin_panel()
        bot.send_message(message.chat.id, 'Админ панель', reply_markup=markup)
    
    else:
        bot.send_message(message.chat.id, 'Сначала нужно войти в аккаунт')
        
        get_login(message)


@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    if is_admin_check(message.chat.id):
        userid = message.text.split(" ")[1]
        cursor.execute("INSERT INTO admins(user_id) VALUES (?)", (str(userid), ))
        conn.commit()
        bot.send_message(message.chat.id, 'Админ добавлен')


@bot.message_handler(commands=['delete_admin'])
def add_admin(message):
    if is_admin_check(message.chat.id):
        userid = message.text.split(" ")[1]
        if is_admin_check(userid):
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (str(userid), ))
            conn.commit()
            bot.send_message(message.chat.id, 'Админ удалён')
        else:
            bot.send_message(message.chat.id, 'Такого админа нет')
        
        
def get_login(message):
    bot.send_message(message.chat.id, 'Введите логин на edu.tatar (только цифры, без пробелов):')
    bot.register_next_step_handler(message, get_password)
    
                                      
def get_password(message):
    login = message.text
    
    password = bot.send_message(message.chat.id, 'Введите пароль (учитывая регистр, без пробелов):')
	
    bot.register_next_step_handler(password, log_in, login)


def log_in(message, login):
    password = message.text
    parser_worker = DataParser()
    print('user ' + str(login) + ' ' + password + ' joined')
    parser_worker.login(login, password)
    
    
    
	
    if parser_worker.login_status:
        try:
            add_table_values(message.chat.id,message.from_user.first_name, login, password)
        except Exception as e:
            print(e)
        markup = types.InlineKeyboardMarkup(row_width=1)
        item3 = types.InlineKeyboardButton('🎒 Расписание и оценки', callback_data='Grades')
        markup.row(item3)
        
        item1 = types.InlineKeyboardButton('🗓 Табель успеваемости', callback_data='year')
        markup.row(item1)
        
        item4 = types.InlineKeyboardButton('⚙ Настройки', callback_data='Options')
        markup.row(item4)

        bot.send_message(message.chat.id, '✅ Авторизация прошла успешно!', reply_markup=markup)        
    
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton('Попробовать ещё раз', callback_data='login_error')
        markup.add(item1)
        bot.send_message(message.chat.id, 'Неверный логин или пароль!', reply_markup=markup)


def logging(call):
    cursor.execute("SELECT login, password FROM users WHERE user_id = ?", [str(call.message.chat.id)])
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
        bot.edit_message_text('✅ Выберите пользователя:', call.message.chat.id, call.message.message_id,
                                  reply_markup=markup)
    except Exception as e:
        bot.send_message(call.message.chat.id, '✅ Выберите пользователя:', reply_markup=markup)
        
        
def get_add_id():
    cursor.execute("SELECT user_id FROM users")
    res = cursor.fetchall()
    return res

def show_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton('Реклама', callback_data='Advertisment')
    markup.row(item1)

    return markup


def advertisment(message, adv):
    adv.text = message.text
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
    markup.add(back)
    mes = bot.send_message(message.chat.id,
                           'Теперь присылайте картинки, по одной штуке, максимум 10, когда закончите нажмите на "Закончить с файлами"')
    bot.register_next_step_handler(mes, advert_add_media, adv)
    

def advert_add_media(message, adv):
    if message.text == 'Закончить с файлами':
        markup = types.InlineKeyboardMarkup(row_width=1)
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        markup.add(back)
        mm = bot.send_message(message.chat.id, 'a', reply_markup=types.ReplyKeyboardRemove())
        bot.delete_message(mm.chat.id, mm.id)
        mes = bot.send_message(message.chat.id, 'A теперь всё проверим:', reply_markup=markup)
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
            msg = bot.send_message(message.chat.id, 'Ошибка поддерживаются только фото/видео')
            bot.register_next_step_handler(msg, advert_add_media, adv)
        if len(adv.media) < 10:
            kb = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton(text='Закончить с файлами')
            btn2 = types.KeyboardButton(text='⬅ Назад')
            kb.add(btn1, btn2)
            msg = bot.send_message(message.chat.id, f'Принято {len(adv.media)} файл(ов)', reply_markup=kb)
            bot.register_next_step_handler(msg, advert_add_media, adv)
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
            markup.add(back)
            mes = bot.send_message(message.chat.id, 'A теперь всё проверим:', reply_markup=markup)
            agree_send_adv(message, adv)

    else:
        msg = bot.send_message(message.chat.id, 'Ошибка поддерживаются только фото/видео')
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
            bot.send_photo(message.chat.id, medialst[0].media, caption=adv.text)
            formatt = 'photo'
        elif adv.media[0][1] == 'video':
            formatt = 'video'
            bot.send_video(message.chat.id, medialst[0].media, caption=adv.text)
            medialst[0].caption = adv.text

    else:
        medialst[-1].caption = adv.text
        bot.send_media_group(message.chat.id, medialst)
        formatt = 'mediagroup'
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
    markup.add(back)
    mes = bot.send_message(message.chat.id, 'Если вас все устраивает отправьте любое сообщеение, иначе выберите "назад" под эти сообщением', reply_markup=markup)
    bot.register_next_step_handler(mes, mailing_adv, medialst, formatt)    
        

def mailing_adv(message, medialst, formatt):
    bot.send_message(message.chat.id, 'ОТПРАВКА...')
    data = get_add_id()
    data = set(data)
    c = 0
    if formatt == 'photo':
        for id in data:
            try:
                bot.send_photo(id, medialst[0].media, caption=medialst[0].caption)
                c+=1
            except:
                pass

    elif formatt == 'video':
        for id in data:
            try:
                bot.send_video(id, medialst[0].media, caption=medialst[0].caption)
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
    bot.send_message(message.chat.id, f'Отправка завершена, доставлено {c}/{len(data)} сообщений', reply_markup=kb)
    
    
@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_1_callback.prefix))	    
def callback_inline(call: CallbackQuery):
        name, action, year, month, day = call.data.split(calendar_1_callback.sep)
        date = calendar.calendar_query_handler(
            bot=bot, call=call, name=name, action=action, year=year, month=month, day=day
        )
        if action == "DAY":
            options = types.InlineKeyboardMarkup(row_width=1)
            
            back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
            
            options.add(back)
            

            
            userdata = logging(call)
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
                    
            
            img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
            fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
            
            ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
           
            flname = str(randint(100000, 1000000))
            img.save(f'{flname}.png')   
            
            
            intDay = date.weekday()
            days = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
            months = ['января', 'февраля','мара', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
            bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'), caption=f'Ваше расписание на {days[intDay]} ({date.day} {months[date.month - 1]}) ✅', reply_markup=options)
        
            os.remove(f'{flname}.png')
            
        
        elif action == "CANCEL":
            markup = types.InlineKeyboardMarkup(row_width=1)
        
            item2 = types.InlineKeyboardButton('🏫 Расписание', callback_data='TimeTable')
            item3 = types.InlineKeyboardButton('🎒 Оценки', callback_data='Grades')
            markup.row(item2, item3)
        
            item1 = types.InlineKeyboardButton('🗓 Табель успеваемости', callback_data='year')
            markup.row(item1)
        
            item4 = types.InlineKeyboardButton('⚙ Настройки', callback_data='Options')
            markup.row(item4)
            
            bot.send_message(call.message.chat.id, '✅ Рады видеть вас снова!', reply_markup=markup)
           



def buildMainMenu(call, name=''):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    item3 = types.InlineKeyboardButton('🎒 Расписание и оценки', callback_data='Grades')
    markup.row(item3)
    
    item1 = types.InlineKeyboardButton('🗓 Табель успеваемости', callback_data='year')
    markup.row(item1)
    
    item4 = types.InlineKeyboardButton('⚙ Настройки', callback_data='Options')
    markup.row(item4)
    
    if name != '':
        res = f'✅ Рады видеть вас снова, {name.split(" ")[-1]}!'
    else:
        res = '✅ Рады видеть вас снова!'
    try:
        bot.edit_message_text(res, call.message.chat.id, call.message.message_id,
                              reply_markup=markup)
    except Exception as e:
        bot.send_message(call.message.chat.id, res, reply_markup=markup)
    

def is_admin_check(chat_id):
    cursor.execute("SELECT EXISTS(SELECT * FROM admins WHERE user_id = ?)", (str(chat_id),))
    result = cursor.fetchone()
    return bool(result[0])    

def makeSchcedule(call, period):
    options = types.InlineKeyboardMarkup(row_width=1)
        
    t = Texttable()
    
    userdata = logging(call)
    login, password = userdata[0][0], userdata[0][1]         
    parser_worker = DataParser()
    parser_worker.login(login, password)
    res = parser_worker.schcedule(period=period)
    parser_worker.logout()    
    

    if len(res[1][-1]) == 3:
        res[1][-1].insert(1, '') 
       
    data = res[1]    
    
    periods = res[0]
    
    
    for i in periods.items():
        option = types.InlineKeyboardButton(i[0], callback_data=i[1])
        options.add(option)
  
    t.add_rows(data)
        
    table_width = max([ len(x) for x in t.draw().split('\n') ])
        
    table_height = 0
    for i in t.draw():
        if i == '\n':
            table_height += 1
                
        
    img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
    fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
        
    ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
       
    flname = str(randint(100000, 1000000))
    img.save(f'{flname}.png')       
    
    back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
    
    options.add(back)    
    
    per = list(periods.keys())[list(periods.values()).index(period)]
    
    bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'), caption=f'✅ Ваш табель успеваемости за {per.lower()}', reply_markup=options)
    
    os.remove(f'{flname}.png')    
 

def buidGradesMenu(call):
    grades = types.InlineKeyboardMarkup(row_width=1)
    
    grades_today = types.InlineKeyboardButton(text='🗓 Оценки за сегодня', callback_data='check_grades_today')
    grades_get = types.InlineKeyboardButton(text='📆 Выбрать дату', callback_data='check_grades_get')
    back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
    
    grades.add(grades_today, grades_get, back)
    bot.edit_message_text('🎒 Просмотр оценок', call.message.chat.id, call.message.message_id,
                          reply_markup=grades)
    
    
def buildGradesToday(call):
    options = types.InlineKeyboardMarkup(row_width=3)
    
    previous = types.InlineKeyboardButton(text='⬅', callback_data='prev')
    back = types.InlineKeyboardButton(text='Назад', callback_data='mainmenu')
    nextt = types.InlineKeyboardButton(text='➡', callback_data='nextt')
    
    options.add(previous, back, nextt)
    
    
    userdata = logging(call)
    login, password = userdata[0][0], userdata[0][1]         
    parser_worker = DataParser()
    parser_worker.login(login, password)
    data = parser_worker.get_day_marks('')
    parser_worker.logout()
    
    
    
    t = Texttable()
    t.add_rows(data)
        
    table_width = max([ len(x) for x in t.draw().split('\n') ])
        
    table_height = 0
    for i in t.draw():
        if i == '\n':
            table_height += 1
                
        
    img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
    fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
        
    ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
       
       
    flname = str(randint(100000, 1000000))
    img.save(f'{flname}.png')
    
    if len(data) != 1:   
        bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'), caption=f'Ваше расписание на сегодня ✅', reply_markup=options)
    else:
        bot.edit_message_text('В этот день нет уроков!', call.message.chat.id, call.message.message_id,
                              reply_markup=options)        
    os.remove(f'{flname}.png')
    
 
def changeDayOfGrades(call, sign):
    options = types.InlineKeyboardMarkup(row_width=3)
    
    previous = types.InlineKeyboardButton(text='⬅', callback_data='prev')
    back = types.InlineKeyboardButton(text='Назад', callback_data='mainmenu')
    nextt = types.InlineKeyboardButton(text='➡', callback_data='nextt')
    
    options.add(previous, back, nextt)
    
     
    
    t = Texttable()
    
    date = datetime.datetime.now()
    date = date + 1 * sign * datetime.timedelta(days=1)    #fixxxx
    
    userdata = logging(call)
    login, password = userdata[0][0], userdata[0][1]         
    parser_worker = DataParser()
    parser_worker.login(login, password)
    data = parser_worker.get_day_marks(str(int((time.mktime(date.timetuple())))))
    parser_worker.logout()
    
    t.add_rows(data)
        
    table_width = max([ len(x) for x in t.draw().split('\n') ])
        
    table_height = 0
    for i in t.draw():
        if i == '\n':
            table_height += 1
                
        
    img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
    fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
        
    ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
       
       
    flname = str(randint(100000, 1000000))
    img.save(f'{flname}.png')
        
    if len(data) != 1:
        intDay = date.weekday()
        days = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
        months = ['января', 'февраля','мара', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        bot.send_photo(call.message.chat.id, open(f'{flname}.png', 'rb'), caption=f'Ваше расписание на {days[intDay]} ({date.day} {months[date.month - 1]}) ✅', reply_markup=options)        

    else:
        try:
            bot.edit_message_text('В этот день нет уроков!', call.message.chat.id, call.message.message_id,
                                  reply_markup=options)
        except Exception as e:
            bot.send_message(call.message.chat.id, 'В этот день нет уроков!', reply_markup=options)
    
    os.remove(f'{flname}.png')
    
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == 'login_error':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        get_login(call.message)
    
    
    if 'user' in call.data:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(call.message.chat.id),))
        res = cursor.fetchall()
        
        cursor.execute("DELETE FROM users WHERE user_id = ?", (str(call.message.chat.id), ))
        conn.commit()
        
        index = call.data.split()
        
        index = int(index[0][-1])
        
        parser_worker = DataParser()
        parser_worker.login(res[index][3], res[index][4])
        name = parser_worker.get_name()
        
        add_table_values(res[index][1], res[index][2], res[index][3], res[index][4])
        del res[index]
        for i in res:
            add_table_values(i[1], i[2], i[3], i[4])
        
        buildMainMenu(call, name)
            
            
    '''
   
    МЕНЮ ОЦЕНOK
   
    '''
      
    if call.data == 'Grades':
        buidGradesMenu(call) 
    
    '''
    
    ОЦЕНКИ ЗА СЕГОДНЯ
    
    '''
    if call.data == 'check_grades_today':
        buildGradesToday(call)
     
    '''
    
    КНОПКА СЛЕД И ПРЕД. ДЕНЬ
    
    '''
    if call.data == 'prev' or call.data == 'nextt':
        sign = 1 if call.data == 'nextt' else -1
        changeDayOfGrades(call, sign)
    
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
        buildMainMenu(call)
                   
    
    
    '''
    
    НАСТРОЙКИ
    
    '''
    if call.data == 'add_new':
        get_login(call.message)
    
    if call.data == 'change_usr':
        cursor.execute("SELECT * FROM users WHERE user_id=?", (str(call.message.chat.id),))
        res = cursor.fetchall()        
        
        choose_user(call, res)
        
    if call.data == 'Options':
        options = types.InlineKeyboardMarkup(row_width=1)
        
        add_user = types.InlineKeyboardButton(text='ㅤㅤㅤ✏ Добавить пользователяㅤㅤㅤ', callback_data='add_new')
        options.row(add_user)
        
        cursor.execute("SELECT * FROM users WHERE user_id=?", (str(call.message.chat.id),))
        res = cursor.fetchall()
    
        if len(res) != 1:
            change = types.InlineKeyboardButton(text='👨‍💻 Поменять аккаунт', callback_data='change_usr')
            options.row(change)
        
        
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        options.add(back)
        bot.edit_message_text('⚙ Настройки', call.message.chat.id, call.message.message_id,
                              reply_markup=options)    
    
    
    '''
    
    ВЕТКА ВЫХОДА В НАСТРОЙКАХ
    
    '''   
	
    if call.data == 'exit':
        #parser_worker.logout() #удалять ли юзера из бд?
        bot.edit_message_text('⚙ Вы вышли из аккаунта, напишите "/start" чтобы войти снова', call.message.chat.id, call.message.message_id)
    
    
    
    if call.data == 'Advertisment':
        markup = types.InlineKeyboardMarkup(row_width=1)
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        markup.add(back)        
        if is_admin_check(call.message.chat.id):
            mes = bot.send_message(call.message.chat.id, 'Пришлите текст для рекламы\n!!!картинки потом, сначало текст',
                                   reply_markup=markup)
            adv = Adv()
            bot.register_next_step_handler(mes, advertisment, adv)
        else:
            bot.send_message(call.message.chat.id, 'Доступ запрещён!', reply_markup=markup)
       
        
def buildCalendar(message):
    now = datetime.datetime.now()
    bot.edit_message_text('🗓 Выберите нужную дату', message.chat.id, message.message_id,
                              reply_markup=calendar.create_calendar(
                                   name=calendar_1_callback.prefix,
                                   year=now.year,
                                   month=now.month,),)   
    
if __name__ == '__main__':
    bot.polling(none_stop=True)
