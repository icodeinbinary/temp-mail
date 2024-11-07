import requests
import telebot
from telebot import types
import json
import time
import threading

token = '8078841011:AAEuA-eE9U4rv2x09WOSTPwWDeyECzW62ms'

#Here is your bot token
bot = telebot.TeleBot(token)

def load_temp_emails():
    try:
        with open('temp_emails.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_temp_emails(emails):
    with open('temp_emails.json', 'w') as f:
        json.dump(emails, f)

def generate_temp_email():
    url = "https://www.1secmail.com/api/v1/"
    params = {'action': "genRandomMailbox",
'count': "1"}
    headers = {'User-Agent': "okhttp/3.9.1",
'Accept-Encoding': "gzip"}
    req = requests.get(url, params=params, headers=headers).text
    return req.split('["')[1].split('"]')[0]

def refresh_messages(email):
    name = email.split('@')[0]
    dom = email.split('@')[1]

    url = "https://www.1secmail.com/api/v1/"
    params = {'action': "getMessages",
'login': name,
'domain': dom}
    headers = {'User-Agent': "okhttp/3.9.1",
'Accept-Encoding': "gzip"}
    response = requests.get(url, params=params, headers=headers)
    return response.json() if response.status_code == 200 else []

@bot.message_handler(commands=['start'])
def start(message):
    buttons = [
        [types.InlineKeyboardButton("Get new email", callback_data='get_new_email')],
        [types.InlineKeyboardButton("Show emails", callback_data='show_emails')]
        ]
    reply_markup = types.InlineKeyboardMarkup(buttons)
    bot.send_message(message.chat.id, "Click on Get Email to create a new one.", reply_markup=reply_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'get_new_email')
def get_new_email(call):
    email = generate_temp_email()
    temp_emails = load_temp_emails()
    temp_emails[str(call.message.chat.id)] = temp_emails.get(str(call.message.chat.id), []) + [email]
    save_temp_emails(temp_emails)

    bot.send_message(call.message.chat.id, f"Email created : {email}")

    thread = threading.Thread(target=check_for_new_messages, args=(call.message.chat.id, email))
    thread.start()

def check_for_new_messages(chat_id, email):
    known_message_ids = set()
    
    while True:
        messages = refresh_messages(email)
        for msg in messages:
            if msg['id'] not in known_message_ids:
                known_message_ids.add(msg['id'])
                message_text = msg.get('text', "No content")
                
                bot.send_message(chat_id, f"New message:\nman: {msg['from']}\The subject: {msg['subject']}\n\n___________________\n{message_text}")
        
        time.sleep(1)
@bot.callback_query_handler(func=lambda call: call.data == 'show_emails')
def show_emails(call):
    temp_emails = load_temp_emails()
    user_emails = temp_emails.get(str(call.message.chat.id), [])

    if user_emails:
        buttons = [[types.InlineKeyboardButton(email, callback_data=f'delete_{email}')] for email in user_emails]
        reply_markup = types.InlineKeyboardMarkup(buttons)
        bot.send_message(call.message.chat.id, "Click on any one to delete it.", reply_markup=reply_markup)
    else:
        bot.send_message(call.message.chat.id, "You do not have emails")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_email(call):
    email_to_delete = call.data.split('_')[1]
    temp_emails = load_temp_emails()
    user_emails = temp_emails.get(str(call.message.chat.id), [])
    
    if email_to_delete in user_emails:
        user_emails.remove(email_to_delete)
        temp_emails[str(call.message.chat.id)] = user_emails
        save_temp_emails(temp_emails)
        bot.send_message(call.message.chat.id, f"Email deleted: {email_to_delete}")
    else:
        bot.send_message(call.message.chat.id, "Email not found.")


if __name__ == '__main__':
    bot.polling(none_stop=True)