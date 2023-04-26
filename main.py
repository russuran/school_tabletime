import telebot
from text import texts
bot = telebot.TeleBot("6040676784:AAF157wL-6d9Cla06BjP-2FPuT-UcRK6iZA", parse_mode=None)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.send_message(message.chat.id, texts['greetings'])
	


bot.infinity_polling()
