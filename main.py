import telebot
from telebot import types
from text import texts
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
from telebot.types import ReplyKeyboardRemove, CallbackQuery 
from texttable import Texttable
import datetime
from PIL import Image, ImageFont, ImageDraw
import os
import time

from parser_main import DataParser

bot = telebot.TeleBot("6040676784:AAF157wL-6d9Cla06BjP-2FPuT-UcRK6iZA", parse_mode='HTML')

login = None
password = None

parser_worker = DataParser()

calendar = Calendar(language=RUSSIAN_LANGUAGE)
calendar_1_callback = CallbackData("calendar_1", "action", "year", "month", "day")



@bot.message_handler(commands=['start', 'Войти'])
def get_login(message):
    bot.send_message(message.chat.id, 'Сначала нужно войти в аккаунт')
    
    get_login(message)


def get_login(message):
    bot.send_message(message.chat.id, 'Введите логин на edu.tatar:')
    bot.register_next_step_handler(message, get_password)
    
                                      
def get_password(message):
    login = message.text
    
    password = bot.send_message(message.chat.id, 'Введите пароль:')
	
    bot.register_next_step_handler(password, log_in, login)


def log_in(message, login):
    password = message.text
    parser_worker.login(login, password)
    
	
    if parser_worker.login_status:
        markup = types.InlineKeyboardMarkup(row_width=1)
        item3 = types.InlineKeyboardButton('🎒 Расписание и оценки', callback_data='Grades')
        markup.row(item3)
        
        item1 = types.InlineKeyboardButton('🗓 Табель успеваемости', callback_data='TableOfGrades')
        markup.row(item1)
        
        item4 = types.InlineKeyboardButton('⚙ Настройки', callback_data='Options')
        markup.row(item4)

        bot.send_message(message.chat.id, '✅ Авторизация прошла успешно!', reply_markup=markup)        
    
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton('Попробовать ещё раз', callback_data='login_error')
        markup.add(item1)
        bot.send_message(message.chat.id, 'Неверный логин или пароль!', reply_markup=markup)


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
            
            t = Texttable()
            data = parser_worker.get_day_marks(str(int((time.mktime(date.timetuple())))))
            t.add_rows(data)
            
            table_width = max([ len(x) for x in t.draw().split('\n') ])
            
            table_height = 0
            for i in t.draw():
                if i == '\n':
                    table_height += 1
                    
            
            img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
            fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
            
            ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
           
           
            img.save('out.png')
            
            bot.send_photo(call.message.chat.id, open("out.png", 'rb'), caption=f'Ваше расписание на {day} число ✅', reply_markup=options)
        
            os.remove("out.png")
            
        
        elif action == "CANCEL":
            markup = types.InlineKeyboardMarkup(row_width=1)
        
            item2 = types.InlineKeyboardButton('🏫 Расписание', callback_data='TimeTable')
            item3 = types.InlineKeyboardButton('🎒 Оценки', callback_data='Grades')
            markup.row(item2, item3)
        
            item1 = types.InlineKeyboardButton('🗓 Табель успеваемости', callback_data='TableOfGrades')
            markup.row(item1)
        
            item4 = types.InlineKeyboardButton('⚙ Настройки', callback_data='Options')
            markup.row(item4)
            
            bot.send_message(call.message.chat.id, '✅ Рады видеть вас снова!', reply_markup=markup)
           
            
    
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == 'login_error':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        get_login(call.message)
    
    
    
    if call.data == 'TimeTable':
        grades = types.InlineKeyboardMarkup(row_width=1)
        
        timetable_today = types.InlineKeyboardButton(text='🗓 Расписание на сегодня', callback_data='check_timetable_today')
        timetable_get = types.InlineKeyboardButton(text='📆 Выбрать дату', callback_data='check_timetable_get')
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        
        grades.add(timetable_today, timetable_get, back)
        bot.edit_message_text('🏫 Просмотр расписания', call.message.chat.id, call.message.message_id,
                              reply_markup=grades) 
    
    if call.data == 'check_timetable_get':
        buildCalendar(call.message)
        
        
        
        
        
    if call.data == 'Grades':
        grades = types.InlineKeyboardMarkup(row_width=1)
        
        grades_today = types.InlineKeyboardButton(text='🗓 Оценки за сегодня', callback_data='check_grades_today')
        grades_get = types.InlineKeyboardButton(text='📆 Выбрать дату', callback_data='check_grades_get')
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        
        grades.add(grades_today, grades_get, back)
        bot.edit_message_text('🎒 Просмотр оценок', call.message.chat.id, call.message.message_id,
                              reply_markup=grades) 
    
    
    
    
    if call.data == 'check_grades_today':
        options = types.InlineKeyboardMarkup(row_width=1)
            
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
            
        options.add(back)
            
        t = Texttable()
        data = parser_worker.get_day_marks('')
        t.add_rows(data)
            
        table_width = max([ len(x) for x in t.draw().split('\n') ])
            
        table_height = 0
        for i in t.draw():
            if i == '\n':
                table_height += 1
                    
            
        img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
        fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
            
        ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
           
           
        img.save('out.png')
            
        bot.send_photo(call.message.chat.id, open("out.png", 'rb'), caption=f'Ваше расписание на сегодня ✅', reply_markup=options)
        
        os.remove("out.png")
    
    if call.data == 'check_grades_get':
        buildCalendar(call.message)
    



    if call.data == 'year':
        options = types.InlineKeyboardMarkup(row_width=1)
            
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        
        options.add(back)
            
        t = Texttable()
        res = parser_worker.schcedule(period='year')
        data = res[1]
        periods = res[0]
        
        for i in periods.items():
            option = types.InlineKeyboardButton(i[0], callback_data=i[1])
            options.add(option)
        data[-1].append('')
        t.add_rows(data)
            
        table_width = max([ len(x) for x in t.draw().split('\n') ])
            
        table_height = 0
        for i in t.draw():
            if i == '\n':
                table_height += 1
                    
            
        img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
        fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
            
        ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
           
           
        img.save('out.png')
            
        bot.send_photo(call.message.chat.id, open("out.png", 'rb'), caption=f'Ваше расписание на сегодня ✅', reply_markup=options)
        
        os.remove("out.png")
        
    if call.data == '1':
        options = types.InlineKeyboardMarkup(row_width=1)
            
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        
        options.add(back)
            
        t = Texttable()
        res = parser_worker.schcedule(period='1')
        data = res[1]
        periods = res[0]
        
        for i in periods.items():
            option = types.InlineKeyboardButton(i[0], callback_data=i[1])
            options.add(option)
        data[-1].append('')
        t.add_rows(data)
            
        table_width = max([ len(x) for x in t.draw().split('\n') ])
            
        table_height = 0
        for i in t.draw():
            if i == '\n':
                table_height += 1
                    
            
        img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
        fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
            
        ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
           
           
        img.save('out.png')
            
        bot.send_photo(call.message.chat.id, open("out.png", 'rb'), caption=f'Ваше расписание на сегодня ✅', reply_markup=options)
        
        os.remove("out.png")
        
    if call.data == '2':
        options = types.InlineKeyboardMarkup(row_width=1)
            
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        
        options.add(back)
            
        t = Texttable()
        res = parser_worker.schcedule(period='2')
        data = res[1]
        periods = res[0]
        data[-1].append('')
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
           
           
        img.save('out.png')
            
        bot.send_photo(call.message.chat.id, open("out.png", 'rb'), caption=f'Ваше расписание на сегодня ✅', reply_markup=options)
        
        os.remove("out.png")        
    
    if call.data == 'TableOfGrades':
        options = types.InlineKeyboardMarkup(row_width=1)
            
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        
        options.add(back)
            
        t = Texttable()
        res = parser_worker.schcedule(period='year')
        data = res[1]
        periods = res[0]
        
        for i in periods.items():
            option = types.InlineKeyboardButton(i[0], callback_data=i[1])
            options.add(option)
        print(periods)
        t.add_rows(data)
            
        table_width = max([ len(x) for x in t.draw().split('\n') ])
            
        table_height = 0
        for i in t.draw():
            if i == '\n':
                table_height += 1
                    
            
        img = Image.new('RGB', (table_width * 20 - 50, table_height * 35 - 50), color = (255, 255, 255))
        fnt = ImageFont.truetype("fonts/CourierNewPSMT.ttf", 30)
            
        ImageDraw.Draw(img).text((50,50), t.draw(), font=fnt, fill=(0,0,0))
           
           
        img.save('out.png')
            
        bot.send_photo(call.message.chat.id, open("out.png", 'rb'), caption=f'Ваше расписание на сегодня ✅', reply_markup=options)
        
        os.remove("out.png")
    
    
    
    
    
    if call.data == 'mainmenu':
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        item3 = types.InlineKeyboardButton('🎒 Расписание и оценки', callback_data='Grades')
        markup.row(item3)
        
        item1 = types.InlineKeyboardButton('🗓 Табель успеваемости', callback_data='TableOfGrades')
        markup.row(item1)
        
        item4 = types.InlineKeyboardButton('⚙ Настройки', callback_data='Options')
        markup.row(item4)
        
        try:
            bot.edit_message_text('✅ Рады видеть вас снова!', call.message.chat.id, call.message.message_id,
                              reply_markup=markup)
        except Exception as e:
            markup = types.InlineKeyboardMarkup(row_width=1)
            item3 = types.InlineKeyboardButton('🎒 Расписание и оценки', callback_data='Grades')
            markup.row(item3)
        
            item1 = types.InlineKeyboardButton('🗓 Табель успеваемости', callback_data='TableOfGrades')
            markup.row(item1)
        
            item4 = types.InlineKeyboardButton('⚙ Настройки', callback_data='Options')
            markup.row(item4)
            
            bot.send_message(call.message.chat.id, '✅ Рады видеть вас снова!', reply_markup=markup)            
    
    
    
    
    if call.data == 'Options':
        options = types.InlineKeyboardMarkup(row_width=1)
        
        exit = types.InlineKeyboardButton(text='🛑 Выйти', callback_data='exit')
        back = types.InlineKeyboardButton(text='⬅ Назад', callback_data='mainmenu')
        
        options.add(exit, back)
        bot.edit_message_text('⚙ Настройки', call.message.chat.id, call.message.message_id,
                              reply_markup=options)    
        
	

def buildCalendar(message):
    now = datetime.datetime.now()
    bot.edit_message_text('🗓 Выберите нужную дату', message.chat.id, message.message_id,
                              reply_markup=calendar.create_calendar(
                                   name=calendar_1_callback.prefix,
                                   year=now.year,
                                   month=now.month,),)   
    
bot.infinity_polling(none_stop=True)
