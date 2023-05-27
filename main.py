# OPENAI_API_KEY"] = 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
# telegram.Bot(token='****************************')


import os
import openai
import pyttsx3
import telegram
import csv
import datetime
import threading
import time
import logging
import logging
import math
from telegram import Update, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import nltk

nltk.download('punkt')

# VAR INIT---------------------------------------------------------------------------------------------
slot = 5  #Slot for active user in simultan
time_limit = 90  #User offline time limit in seconds

bot_active = False  # Menambahkan variabel global untuk menyimpan status bot (aktif atau tidak aktif)
users = []  # list untuk menyimpan id user yang sedang menggunakan bot
dalle_users = []  # list untuk menyimpan id user yang sedang menggunakan DALL-E
waitl = []  # list untuk menyimpan id user yang tergabung dalam waiting list
wlID = ' '  # Variabel user id waiting list
users.clear()  # Memastikan list users bersih
last_message = {
}  # Menyimpan waktu terakhir pengguna mengirim pesan (spam analyzer)
last_active = {}  # Menyimpan waktu terakhir pengguna mengirim pesan
inact_time = {}  # Menyimpan waktu offline pengguna
inact = 0  # Variabel untuk menyimpan sementara inactive time
spam_limit = 3  # Batas gap waktu pengiriman setiap pesan untuk deteksi spam
chat_delay = 0  # Variabel pembatas kecepatan response chat
user_lang = {}  # Dictionary untuk menyimpan preferensi bahasa user
flag = False  # Boolean flag untuk inisialisasi Genesis
y = ""  # Variabel untuk menyimpan prompt Genesis di satu waktu
has_sent_message = False  # Boolean pendukung untuk inisialisasi Genesis

# Inisiasi variabel untuk menyimpan data percakapan dan memori model
conversation_history = {}  # Menyimpan history percakapan mentah
gpt_memo = {}  # Menyimpan history percakapan siap olah (memori model)
token_count = 0

XAPI = ''

# tokenizer = GPT2Tokenizer.from_pretrained('EleutherAI/gpt-neo-2.7B')
# model = GPT2Model.from_pretrained('EleutherAI/gpt-neo-2.7B')

# INIT-------------------------------------------------------------------------------------------------

# Inisialisasi logger
logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO)
logger = logging.getLogger(__name__)

# Membuat direktori chat_history jika belum ada
if not os.path.exists('chat_history'):
  os.makedirs('chat_history')

# Membuat direktori WaitingList_history jika belum ada
if not os.path.exists('WaitingList_history'):
  os.makedirs('WaitingList_history')

# Membuat direktori Genesis_history jika belum ada
if not os.path.exists('Genesis_history'):
  os.makedirs('Genesis_history')

# Membuat file chat_history.csv jika belum ada
file_path = "chat_history/chat_history.csv"
file_exists = os.path.isfile(file_path)
if not file_exists:
  with open(file_path, mode='w') as chat_file:
    fieldnames = ['Time','U_ID', 'Name', 'Username', 'User', 'Bot']
    writer = csv.DictWriter(chat_file, fieldnames=fieldnames)
    writer.writeheader()
else:
  file_exists = True  # tambahkan variabel ini

# Membuat file WaitingList_history.csv jika belum ada
wl_file_path = "WaitingList_history/WaitingList_history.csv"
wl_file_exists = os.path.isfile(wl_file_path)
if not wl_file_exists:
  with open(wl_file_path, mode='w') as wl_chat_file:
    fieldnames = ['Time', 'Name', 'Username', 'UserID']
    writer = csv.DictWriter(wl_chat_file, fieldnames=fieldnames)
    writer.writeheader()
else:
  wl_file_exists = True  # tambahkan variabel ini

# Membuat file genesis_history.csv jika belum ada
gn_file_path = "Genesis_history/Genesis_history.csv"
gn_file_exists = os.path.isfile(gn_file_path)
if not gn_file_exists:
  with open(gn_file_path, mode='w') as gn_chat_file:
    fieldnames = ['Time', 'Name', 'Username', 'UserID', 'Prompt', 'ResultLink']
    writer = csv.DictWriter(gn_chat_file, fieldnames=fieldnames)
    writer.writeheader()
else:
  gn_file_exists = True  # tambahkan variabel ini
  
# ORI
# cos******@gmail.com	[$5 GR]	: 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
# ho********@gmail.com	[$18 GR]: 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
# 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
#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
#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


API_A = ""
API_B = ""
API_C = ""
  

# # fungsi untuk mengubah XAPI setiap setengah detik
# def change_api_key():
#     global XAPI
#     XAPI = API_A
#     while True:
#         # time.sleep(0.01)
#         # print(". . . ")
#         if XAPI == API_A:
#             XAPI = API_B
#             # print("Menggunakan kunci API[B]:", XAPI)
#         elif XAPI == API_B:
#             XAPI = API_C
#             # print("Menggunakan kunci API[C]:", XAPI)
#         else:
#             XAPI = API_A
#             # print("Menggunakan kunci API[A]:", XAPI)
#         # kode selanjutnya disini
    
#     print(f"XAPI: {XAPI}")
#     t_api = threading.Thread(target=change_api_key)

      
# # menjalankan fungsi change_api_key dalam thread terpisah
# t_api = threading.Thread(target=change_api_key).start()
# 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
  
# Mengatur kunci API OpenAI
os.environ[
  "OPENAI_API_KEY"] = "OPEN_AI_API_KEY_HERE"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Inisialisasi bot Telegram
bot = telegram.Bot(token='TELEGRAM_BOT_TOKEN_HERE')

# KEEP ALIVE 24/7-------------------------------------------------------------------------------------------
from keep_alive import keep_alive

# FUNCTION SIDE---------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------------


def count_tokens(message):
  inputs = tokenizer(message, return_tensors='pt')
  tokens = model(**inputs).input_ids.shape[1]
  return tokens


# Fungsi untuk menambahkan pesan ke dalam memori percakapan
def add_conversation(user_name, question, response):
  if user_name in conversation_history:
    conversation_history[user_name].append((question, response))
  else:
    conversation_history[user_name] = [(question, response)]


# Fungsi untuk menambahkan pesan ke dalam memori model
def add_msg(user_name, prompt):
  if user_name in gpt_memo:
    gpt_memo[user_name].append(prompt)
  else:
    gpt_memo[user_name] = [prompt]


# ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||


def start(update, context):
  global bot_active
  global users
  global last_active

  user = update.message.from_user.username

  last_name = update.message.from_user.last_name
  if last_name:
    real_name = update.message.from_user.first_name + ' ' + last_name
  else:
    real_name = update.message.from_user.first_name

  if update.message.chat_id in users:

    # print(f"NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | JOINED THE CHAT")
    # Jika pengguna sudah terdaftar, maka sistem memberikan pemberitahuan

    # if update.message.chat_id in user_lang:

    #   if user_lang[update.message.chat_id] == 'id' :
    #   if user_lang[update.message.chat_id] == 'eng' :
    # if update.message.chat_id not in user_lang:
    #   print(f"{user} BELUM MEMIIH BAHASA")
    #   language(update, context)

    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Anda sudah terhubung dengan ID: {update.message.chat_id}")

    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"You've been connected with ID: {update.message.chat_id}")

    return

  # jika jumlah user yang menggunakan bot belum mencapai maksimum, maka user bisa menggunakan bot
  if len(users) < slot and update.message.chat_id in user_lang:
    print("\n\n")
    print(
      f"[START] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | JOINED THE CHAT"
    )
    users.append(update.message.chat_id)
    bot_active = True

    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "Halo! Saya adalah bot QGPT!. Silakan kirim pesan Anda. \n\n*/stop - mematikan bot*\n*/help - bantuan penggunaan*\n\n*Bot lambat?* _gunakan versi extended_:\n\n || EXTD1 [https://t.me/QXTD1_BOT] \n\nMerasa terbantu? anda dapat mengirimkan donasi melalui :\n\nօ BuyMeCoffe 🌐\t\t\t: https://bit.ly/3loIdGC \nօ Saweria 🇮🇩           : https://bit.ly/3JOIbkJ  \n\n ",
        parse_mode='Markdown')
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        f"*⚠️* _Anda akan dinonaktifkan jika anda tidak aktif selama lebih dari {time_limit/60} menit_",
        parse_mode='Markdown')

    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "Hello! I'm QGPT bot!. Please send your message. \n\n*/stop - stop bot*\n*/help - usage guidelines*\n\n*Bot unresponsive?* _use extended version_:\n\n || EXTD1 [https://t.me/QXTD1_BOT] \n\nFound it helpfull? you can send me donation through :\n\nօ BuyMeCoffe 🌐\t\t\t: https://bit.ly/3loIdGC \nօ Saweria 🇮🇩           : https://bit.ly/3JOIbkJ  \n\n ",
        parse_mode='Markdown')
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        f"*⚠️* _You will be deactivated if you are inactive for more than {time_limit/60} minute_",
        parse_mode='Markdown')

    # Menginisialisasi waktu terakhir pengguna mengirim pesan
    last_active[update.message.chat_id] = datetime.datetime.now()
    inact_time[update.message.chat_id] = inact

    # Menjalankan fungsi untuk menonaktifkan pengguna jika tidak aktif selama 30 detik
    t = threading.Thread(target=inactive_user, args=(update, context))
    t.start()

  elif update.message.chat_id not in user_lang:
    print(f"{user} BELUM MEMIIH BAHASA")
    language(update, context)

  else:

    # jika sudah mencapai maksimum, maka user lain tidak bisa menggunakan bot
    print(
      f"NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | CAN'T JOIN THE CHAT"
    )
    active_users = '\n '.join([
      "▫ " + str(chat_id) +
      f" | remain: {math.floor(time_limit - inact_time.get(chat_id))}'s "
      for chat_id in users
    ])
    context.bot.send_message(
      chat_id=update.effective_chat.id,
      text=
      f"Maaf, jumlah pengguna mencapai batas maksimum. Pengguna saat ini: \n\n{active_users} \n\nSilakan coba lagi nanti."
    )

    waitinglist(update, context)


# --------------------------------------------------


def stop(update, context):
  global bot_active
  global users
  global lang_users

  user = update.message.from_user.username

  last_name = update.message.from_user.last_name
  if last_name:
    real_name = update.message.from_user.first_name + ' ' + last_name
  else:
    real_name = update.message.from_user.first_name

  # menghapus chat_id user yang keluar dari pengguna bot
  if update.message.chat_id in users and update.message.chat_id in user_lang:
    users.remove(update.message.chat_id)

    has_sent_message = False
    y = ''

    if len(dalle_users) > 0:
      dalle_users.remove(update.message.chat_id)

      print(
        f"NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | LEFT THE QGPT"
      )

    elif update.message.chat_id not in user_lang:
      print(f"{user} BELUM MEMIIH BAHASA")
      language(update, context)

  # menghapus chat_id user yang keluar dari pengguna bot
  if update.message.chat_id in users and update.message.chat_id in dalle_users and update.message.chat_id in user_lang:
    users.remove(update.message.chat_id)

    dalle_users.remove(update.message.chat_id)
    has_sent_message = False
    y = ''

    print(
      f"NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | LEFT THE GENESIS & QGPT"
    )

  # jika tidak ada pengguna yang menggunakan bot, maka bot dinonaktifkan
  if update.message.chat_id not in users and update.message.chat_id in user_lang:
    bot_active = False

    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Bot telah dinonaktifkan. /start untuk memulai")
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(chat_id=update.effective_chat.id,
                               text="Bot deactivated. /start to start")

    has_sent_message = False
    y = ''

  elif update.message.chat_id not in user_lang:
    print(f"{user} BELUM MEMIIH BAHASA")
    language(update, context)

  else:
    return


# -----------------------------------------------------------------------------------------------


def check_user(update):
  global users
  if update.message.chat_id not in users:
    context.bot.send_message(
      chat_id=update.message.chat_id,
      text=
      "Maaf, Anda tidak terdaftar sebagai pengguna bot. ['/start' to start bot]"
    )
    return False
  return True


# --------------------------------------------------


def active_user(update, context):
  global users
  global inactive_time
  global inact_time

  if len(users) > 0:

    active_users = '\n '.join([
      "▫ " + str(chat_id) +
      f" | remain: {math.floor(time_limit - inact_time.get(chat_id))}'s "
      for chat_id in users
    ])
    context.bot.send_message(
      chat_id=update.effective_chat.id,
      text=f"ID Pengguna aktif saat ini: \n\n *{active_users}*\n\n",
      parse_mode='Markdown')

  else:
    if update.message.chat_id in user_lang:
      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Tidak ada pengguna aktif saat ini")

      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="There are no active users at this time")
    if update.message.chat_id not in user_lang:
      print(f"{update.message.chat_id} BELUM MEMIIH BAHASA")
      language(update, context)


# --------------------------------------------------


def inactive_user(update, context):
  global bot_active
  global users
  global last_active
  global inactive_time

  user = update.message.from_user.username

  last_name = update.message.from_user.last_name
  if last_name:
    real_name = update.message.from_user.first_name + ' ' + last_name
  else:
    real_name = update.message.from_user.first_name

  while bot_active and update.message.chat_id in users:
    # Menghitung selisih waktu sejak terakhir pengguna mengirim pesan
    inactive_time = (datetime.datetime.now() -
                     last_active[update.message.chat_id]).total_seconds()
    inact = inactive_time

    inact_time[update.message.chat_id] = inact

    # Jika pengguna tidak aktif selama 30 detik, maka pengguna dinonaktifkan

    if inactive_time >= time_limit:
      users.remove(update.message.chat_id)
      if update.message.chat_id in user_lang:
        if user_lang[update.message.chat_id] == 'id':
          context.bot.send_message(
            chat_id=update.message.chat_id,
            text=
            f"Maaf, Anda telah dinonaktifkan karena tidak aktif selama lebih dari {time_limit/60} menit."
          )
        if user_lang[update.message.chat_id] == 'eng':
          context.bot.send_message(
            chat_id=update.message.chat_id,
            text=
            f"Sorry, you have been deactivated due to inactivity for over {time_limit/60} minute."
          )
      if update.message.chat_id not in user_lang:
        print(f"{update.message.chat_id} BELUM MEMIIH BAHASA")
        language(update, context)

      print(
        f"NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | OFFLINE USER KICKED "
      )
      # if update.message.chat_id in waitl:
      #   context.bot.send_message(
      #     chat_id=update.effective_chat.id,
      #     text=
      #     f"{slot - len(users)} Slot tersedia silakang bergabung dengan /start"
      #   )
      #   waitl.clear()

      # Menghapus waktu terakhir pengguna mengirim pesan dari dictionary last_active
      del last_active[update.message.chat_id]

      if len(dalle_users) > 0: dalle_users.remove(update.message.chat_id)
      has_sent_message = False
      y = ''

      # Jika tidak ada pengguna yang menggunakan bot, maka bot dinonaktifkan
      if not users:
        bot_active = False
        if update.message.chat_id in user_lang:
          if user_lang[update.message.chat_id] == 'id':
            context.bot.send_message(
              chat_id=update.effective_chat.id,
              text="Bot telah dinonaktifkan. ['/start' untuk memulai]")
          if user_lang[update.message.chat_id] == 'eng':
            context.bot.send_message(
              chat_id=update.effective_chat.id,
              text="Bot deactivated. ['/start' to start bot]")

        if update.message.chat_id not in user_lang:
          print(f"{update.message.chat_id} BELUM MEMIIH BAHASA")
          language(update, context)

    # Menunggu 0.1 detik sebelum memeriksa kembali waktu terakhir pengguna mengirim pesan
    time.sleep(0.1)


# -----------------------------------------------------------------------------------------------
def echo(update: Update, context: CallbackContext):

  global bot_active
  global user_lang
  global token_count

  # Jika bot sedang aktif, lakukan proses membaca pesan
  if bot_active and update.message.chat_id in users:


    if update.message.chat_id in dalle_users:
      print("DL FUNC ECHO")

      dalle(update, context)
      return



    # Kirim pesan ke pengguna
    message = context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='🙈 _sending. . ._',
                                       parse_mode='Markdown')
    message_id = message.message_id

    time.sleep(chat_delay)


    print("\n\n")

    # Mendapatkan input dari pengguna
    message_x = update.message.text
    user = update.message.from_user.username

    last_name = update.message.from_user.last_name
    if last_name:
      real_name = update.message.from_user.first_name + ' ' + last_name
    else:
      real_name = update.message.from_user.first_name

    #-----

    # Tambahkan pesan ke dalam memori percakapan
    add_conversation(user, message_x, "")

    qq_msg = {"role": "user", "content": conversation_history[user][-1][0]}
    add_msg(user, qq_msg)

    if user not in gpt_memo:
      # Jika user_name belum ada di dalam gpt_memo, gunakan pesan pengguna sebagai input untuk model
      input_data = [{"role": "user", "content": message_x}]
      add_msg(
        user, {
          "role": "system",
          "content": 'asisten pembantu yang yang memiliki memori kuat'
        })
    else:
      # Jika user_id sudah ada di dalam gpt_memo, gunakan data memori model sebagai input untuk model
      input_data = gpt_memo[user]







    

    # Cek apakah pengguna sebelumnya telah mengirim pesan dalam batas waktu yang ditentukan
    if user in last_message and time.time() - last_message[user] < spam_limit:
      # Jika iya, maka abaikan pesan tersebut dan tidak melakukan apapun

      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="*Spam terdeteksi*\n\nAnda akan dikeluarkan dari percakapan...",
        parse_mode='Markdown')
      stop(update, context)

      return

    # Jika tidak, lanjutkan dengan mengubah waktu terakhir pengguna mengirim pesan
    last_message[user] = time.time()




    

    # Ubah pesan
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=message_id,
                                  text='🐵  *received*',
                                  parse_mode='Markdown')

    
    # Menginisialisasi waktu terakhir pengguna mengirim pesan
    last_active[update.message.chat_id] = datetime.datetime.now()

    # Menjalankan fungsi untuk menonaktifkan pengguna jika tidak aktif selama beberapa detik
    t = threading.Thread(target=inactive_user, args=(update, context))
    t.start()

    print(
      f"[ECHO][Q] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | Q: "
      + str(message_x))
    time.sleep(chat_delay)

    # Ubah pesan
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=message_id,
                                  text='🙉 _processing. . ._',
                                  parse_mode='Markdown')
    # animate(update, context)

    total_tokens = 0
    for item in gpt_memo[user]:
      tokens = nltk.word_tokenize(item['content'])
      total_tokens += len(tokens)
    print(f"TOKEN [{user}] : {total_tokens}")

    if total_tokens > 2000:
      del gpt_memo[user]
      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          "*Note*: _Pesan yang dikirimkan sebelumnya melebihi 2000 Token, seluruh memori akan dihapus untuk memperbesar limit ingatan. . ._",
          parse_mode='Markdown')
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text="*Silakan kirim pertanyaan baru yang lebih pendek*",
          parse_mode='Markdown')
      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          "*Note*: _Previous sent messages exceed 2000 Tokens, the entire memory will be cleared to increase the order limit. . ._",
          parse_mode='Markdown')
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="*Please post a new, shorter question*",
                                 parse_mode='Markdown')

    try:

      # Jalankan model untuk menghasilkan output
      res = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                         messages=input_data)
      # Ambil output dari hasil model dan tambahkan ke dalam memori percakapan dan model
      output = res.choices[0].message['content']

      add_conversation(user, message, output)
      q_msg = {"role": "user", "content": conversation_history[user][-2][0]}
      a_msg = {
        "role": "assistant",
        "content": conversation_history[user][-1][1]
      }
      add_msg(user, q_msg)
      add_msg(user, a_msg)

      # Jika panjang memori model sudah lebih dari 6, hapus data pada indeks ke-1 sampai ke-3
      if len(gpt_memo[user]) > 9:
        del gpt_memo[user][1:3]
        print("\n\nARRAY SLICED, NOW: ")
        print("LENGTH: " + str(len(gpt_memo[user])) + "\n\n")

    except openai.error.APIError as e:

      # Tangani kesalahan API
      logger.error(f"OpenAI API Error: {e}")
      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Bentar..., saya lagi pusing ECH😭")
        total_tokens = 0
        for item in gpt_memo[user]:
          tokens = nltk.word_tokenize(item['content'])
          total_tokens += len(tokens)
        print(f"TOKEN [{user}] : {total_tokens}")

      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Hold on..., I'm dizzy ECH😭")

    except Exception as e:
      # Tangani kesalahan umum
      logger.error(f"Error: {e}")
      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Bentar..., saya lagi pusing😭")

      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Hold on..., I'm dizzy😭")

    print(
      f"[ECHO][QGPT] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | Q: "
      + str(message_x) + " | A: " + output + "\n")
    print("GPT MEMO: " + str(gpt_memo) + "\n")

    for item in gpt_memo[user]:
      tokens = nltk.word_tokenize(item['content'])
      total_tokens += len(tokens)
    print(total_tokens)
    if total_tokens > 2000:
      del gpt_memo[user]
      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          "*Note*: _Pesan yang anda kirim melebihi 2000 Token, seluruh memori akan dihapus untuk memperbesar limit ingatan. . ._",
          parse_mode='Markdown')
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text="*Silakan kirim pertanyaan baru yang lebih pendek*",
          parse_mode='Markdown')
      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          "*Note*: _Previous sent messages exceed 2000 Tokens, the entire memory will be cleared to increase the order limit. . ._",
          parse_mode='Markdown')
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="*Please post a new, shorter question*",
                                 parse_mode='Markdown')

    # Mengirim output ke pengguna
    context.bot.send_message(chat_id=update.effective_chat.id, text=output)

    # Ubah pesan
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=message_id,
                                  text='🦊 *QGPT:*',
                                  parse_mode='Markdown')

    # Menyimpan percakapan ke dalam file csv
    chat_time = datetime.datetime.now(
      datetime.timezone(
        datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    # file_path = "chat_history/chat_history.csv"
    with open(file_path, mode='a') as chat_file:
      fieldnames = ['Time', 'U_ID', 'Name', 'Username', 'User', 'Bot']
      writer = csv.DictWriter(chat_file, fieldnames=fieldnames)
      writer.writerow({
        'Time': chat_time,
        'U_ID': update.message.chat_id,
        'Name': real_name,
        'Username': user,
        'User': message_x,
        'Bot': output
      })

    # Menampilkan pesan jika jumlah pengguna melebihi batas
    if len(context.chat_data) > slot and update.message.chat_id in users:
      active_users = ', '.join([str(chat_id) for chat_id in users])
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        f"Maaf, jumlah pengguna telah mencapai batas maksimum. Pengguna saat ini: {active_users}"
      )
      bot_active = false
      return



  else:
    if update.message.chat_id not in user_lang:
      print(f"{update.message.from_user.username} BELUM MEMIIH BAHASA")
      print("ECHO PIL BAHASA")
      language(update, context)
    if update.message.chat_id in user_lang:
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Maaf, bot sedang offline. /start untuk memulai")

# -----------------------------------------------------------------------------------------------


def dalle(update, context):

  global flag
  global y
  global has_sent_message

  user = update.message.from_user.username

  last_name = update.message.from_user.last_name
  if last_name:
    real_name = update.message.from_user.first_name + ' ' + last_name
  else:
    real_name = update.message.from_user.first_name

  print("\n\n")

  print(
    f"[GENESIS] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | ENTERING DALLE FUNCTION"
  )

  if update.message.chat_id in users and update.message.chat_id not in dalle_users:
    print(
      f"[GENESIS] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | REGIST THE USER"
    )
    dalle_users.append(update.message.chat_id)
    # Menginisialisasi waktu terakhir pengguna mengirim pesan
    last_active[update.message.chat_id] = datetime.datetime.now()

    # Menjalankan fungsi untuk menonaktifkan pengguna jika tidak aktif selama beberapa detik
    t = threading.Thread(target=inactive_user, args=(update, context))
    t.start()

    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(chat_id=update.effective_chat.id,
                               text="*GENESIS AKTIF*",
                               parse_mode='Markdown')

      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "*Tips Penggunaan*:\n\n_'deskripsi gambar' , 'gaya'_\n\ncth:\n\n_Two cats playing chess, oil painting_\n\n",
        parse_mode='Markdown')

    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(chat_id=update.effective_chat.id,
                               text="*GENESIS ACTIVATED*",
                               parse_mode='Markdown')

      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "*Tips*:\n\n_'image description' , 'style'_\n\nexc:\n\n_Two cats playing chess, oil painting_\n\n",
        parse_mode='Markdown')

    print("[GENESIS] USER : " + str(dalle_users))
    flag = True
    has_sent_message = False

  if update.message.chat_id in users and update.message.chat_id in dalle_users:
    print(
      f"[GENESIS] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | USER VALIDATED"
    )

    # Menginisialisasi waktu terakhir pengguna mengirim pesan
    last_active[update.message.chat_id] = datetime.datetime.now()

    # Menjalankan fungsi untuk menonaktifkan pengguna jika tidak aktif selama beberapa detik
    t = threading.Thread(target=inactive_user, args=(update, context))
    t.start()

    if flag and has_sent_message:
      print(
        f"[GENESIS] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | SUCCEEDED AUTHENTICATION"
      )

      if user_lang[update.message.chat_id] == 'id':

        # Kirim pesan ke pengguna
        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='🎨  _Memproduksi gambar. . ._',
                                           parse_mode='Markdown')
        message_id = message.message_id

      if user_lang[update.message.chat_id] == 'eng':

        # Kirim pesan ke pengguna
        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='🎨  _Generates image. . ._',
                                           parse_mode='Markdown')
        message_id = message.message_id

      # context.bot.send_message(chat_id=update.effective_chat.id, text="MEMPRODUKSI GAMBAR")
      # print("FLAG TRUE AND HSM TRUE")
      y = update.message.text

      print(
        f"[GENESIS] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | PROMPT: "
        + y)
      try:

        response = openai.Image.create(prompt=y, n=1, size="1024x1024")
        image_url = response['data'][0]['url']
        print(
          f"[GENESIS] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | RES: \n\n"
          + image_url + "\n\n")
      except openai.error.OpenAIError as e:
        print(e.http_status)
        print(e.error)
        # Ubah pesan
        if user_lang[update.message.chat_id] == 'id':
          context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text='Bentar. . ., Genesis lagi pusing😭',
            parse_mode='Markdown')

        if user_lang[update.message.chat_id] == 'eng':
          context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=message_id,
                                        text='Wait. . ., Genesis is dizzy😭',
                                        parse_mode='Markdown')
        return

      # Ubah pesan
      context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                    message_id=message_id,
                                    text='👾 *GENESIS: *',
                                    parse_mode='Markdown')

      context.bot.send_message(chat_id=update.effective_chat.id,
                               text=f"*{y} *\n\n" + image_url,
                               parse_mode='Markdown')

      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text="*/gen_off* untuk kembali ke mode percakapan *QGPT*",
          parse_mode='Markdown')
      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text="*/gen_off* to return to *QGPT* conversation mode ",
          parse_mode='Markdown')

        # Menyimpan percakapan ke dalam file csv
      gn_chat_time = datetime.datetime.now(
        datetime.timezone(
          datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
      # file_path = "chat_history/chat_history.csv"
      with open(gn_file_path, mode='a') as gn_chat_file:
        fieldnames = [
          'Time', 'Name', 'Username', 'UserID', 'Prompt', 'ResultLink'
        ]
        writer = csv.DictWriter(gn_chat_file, fieldnames=fieldnames)
        writer.writerow({
          'Time': gn_chat_time,
          'Name': real_name,
          'Username': user,
          'UserID': update.message.chat_id,
          'Prompt': y,
          'ResultLink': image_url
        })

        has_sent_message = False
        y = ''

        dalle(update, context)

      # threading.Timer(3.0, dalle(update, context)).start()

    elif flag and not has_sent_message:
      print(
        f"[GENESIS] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | LOGIC ADJUSTMENT"
      )
      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          "_Silakan ketik deskripsi gambar yang ingin anda hasilkan dalam bahasa Inggris.._",
          parse_mode='Markdown')
      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          "_Please type a description of the image that you want to generate in English.._",
          parse_mode='Markdown')
      # print("FLAG TRUE AND HSM FALSE")
      has_sent_message = True
      # print("CHANGES: FLAG TRUE AND HSM TRUE")
  else:
    if update.message.chat_id not in user_lang:
      print(f"{user} BELUM MEMIIH BAHASA")
      language(update, context)
      print(
        f"[GENESIS] NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | TRY TO REACH "
      )
      print("DALL PIL BAHASA")
    if update.message.chat_id in user_lang:
      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          "Anda perlu bergabung ke percakapan untuk menggunakan Genesis, /start untuk memulai percakapan"
        )

      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          "You need to join the conversation to use Genesis, /start to start the conversation"
        )

      # print("Y: "+y)
      # y = update.message.text
      # flag = True
      # has_sent_message = True
      # print("CHANGES: FLAG TRUE AND HSM TRUE")


# -------------------------------------------------


def stop_dalle(update, context):

  user = update.message.from_user.username
  last_name = update.message.from_user.last_name
  if last_name:
    real_name = update.message.from_user.first_name + ' ' + last_name
  else:
    real_name = update.message.from_user.first_name

  # menghapus chat_id user yang keluar dari pengguna bot
  if update.message.chat_id in users and update.message.chat_id in dalle_users:

    dalle_users.remove(update.message.chat_id)

    has_sent_message = False
    y = ''

    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(chat_id=update.effective_chat.id,
                               text=f"*Genesis dimatikan*",
                               parse_mode='Markdown')
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(chat_id=update.effective_chat.id,
                               text=f"*Genesis deactivated*",
                               parse_mode='Markdown')

    print(
      f"NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | LEFT THE GENESIS. BACK TO CHAT MODE"
    )

  if update.message.chat_id in users and update.message.chat_id not in dalle_users:

    if user_lang[update.message.chat_id] == 'id':

      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='_Saat ini anda sedang dalam mode percakapan_ *QGPT*',
        parse_mode='Markdown')

    if user_lang[update.message.chat_id] == 'eng':

      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='_You are currently in_ *QGPT* _conversation mode_ ',
        parse_mode='Markdown')

      # print(f"NAME : {real_name} | USERNAME: {user} | ID {update.message.chat_id} | LEFT THE GENESIS")

  else:
    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(chat_id=update.effective_chat.id,
                               text="Bot sedang offline. /start untuk memulai")
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(chat_id=update.effective_chat.id,
                               text="Bot offline. /start to start")


# ---------------------------------------------------------------------------------------------
def waitinglist(update, context):

  user = update.message.from_user.username

  last_name = update.message.from_user.last_name
  if last_name:
    real_name = update.message.from_user.first_name + ' ' + last_name
  else:
    real_name = update.message.from_user.first_name

  # jika jumlah user yang menggunakan bot belum mencapai maksimum, maka user bisa menggunakan bot
  if len(
      users
  ) >= slot and update.message.chat_id not in users and update.message.chat_id not in waitl and update.message.chat_id in user_lang:
    context.bot.send_message(
      chat_id=update.effective_chat.id,
      text=
      "Akses */waitlist* untuk mendapatkan pemberitahuan jika terdapat slot kosong",
      parse_mode='Markdown')

    waitl.append(update.message.chat_id)
    wlID = update.message.chat_id

    print(
      f"NAME : {real_name} | USERNAME: {user} | ID {wlID} | JOINED TO WAITING LIST "
    )

    # Menyimpan percakapan ke dalam file csv
    wl_chat_time = datetime.datetime.now(
      datetime.timezone(
        datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    # file_path = "chat_history/chat_history.csv"
    with open(wl_file_path, mode='a') as wl_chat_file:
      fieldnames = ['Time', 'Name', 'Username', 'UserID']
      writer = csv.DictWriter(wl_chat_file, fieldnames=fieldnames)
      writer.writerow({
        'Time': wl_chat_time,
        'Name': real_name,
        'Username': user,
        'UserID': wlID,
      })

    print("WAITINGLIST: " + str(waitl))

  elif len(
      users
  ) >= slot and update.message.chat_id not in users and update.message.chat_id in waitl and update.message.chat_id in user_lang:
    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        f"_Anda sudah tergabung dalam waiting list dengan ID: {update.message.chat_id}_",
        parse_mode='Markdown')
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        f"_You have joined the waiting list with ID: {update.message.chat_id}_",
        parse_mode='Markdown')

  elif len(
      users
  ) >= slot and update.message.chat_id in users and update.message.chat_id in user_lang:
    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"_Anda sudah terhubung dengan ID:_ *{update.message.chat_id}*",
        parse_mode='Markdown')
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"_You are connected with ID:_ *{update.message.chat_id}*",
        parse_mode='Markdown')
  elif len(
      users
  ) <= slot and update.message.chat_id in users and update.message.chat_id in user_lang:
    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"_Anda sudah terhubung dengan ID:_ *{update.message.chat_id}*",
        parse_mode='Markdown')
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"_You are connected with ID:_ *{update.message.chat_id}*",
        parse_mode='Markdown')

  else:
    if update.message.chat_id in user_lang:
      if user_lang[update.message.chat_id] == 'id':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          f"*{slot - len(users)} Slot kosong tersedia.*\n\nSilakan mulai menggunakan bot dengan\n/start.",
          parse_mode='Markdown')
      if user_lang[update.message.chat_id] == 'eng':
        context.bot.send_message(
          chat_id=update.effective_chat.id,
          text=
          f"*{slot - len(users)} Empty slots available.*\n\nPlease start using the bot with\n/start.",
          parse_mode='Markdown')
    else:
      print(f"{update.message.from_user.username} BELUM MEMIIH BAHASA")
      print("ECHO PIL BAHASA")
      language(update, context)


# --------------------------------------------------


def check_waitlist():
  global waitl

  if len(users) < slot and len(waitl) > 0:
    chat_id = waitl.pop(0)
    bot.send_message(
      chat_id=chat_id,
      text=
      f"*{slot - len(users)} Slot kosong tersedia.*\n{slot - len(users)}_Empty slots available_\n\nSilakan mulai menggunakan bot dengan\n_Please start using the bot with_\n/start.",
      parse_mode='Markdown')
    print("SLOT ALERT SENT SUCCESSFULLY")

  threading.Timer(1.0, check_waitlist).start()
  # print("WAITINGLIST: " + str(waitl))


# Memulai thread untuk memeriksa waiting list setiap 1 detik
threading.Timer(1.0, check_waitlist).start()




# -----------------------------------------------------------------------------------------------


def help(update, context):

  if update.message.chat_id in user_lang:
    if user_lang[update.message.chat_id] == 'id':

      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "*Tata cara penggunaan QGPT bot*\n\n1. Mulai percakapan dengan /start\n2. Masukkan pertanyaan\n3. Ketika pengguna penuh, akses /waitlist untuk mendapatkan notifikasi jika terdapat slot kosong\n4. Hentikan percakapan dengan /stop\n\n*Info Menarik:*\n\n_Sekarang QGPT sudah memiliki memori/ingatan hingga 9 percakapan masa lalu, dengan begitu anda dapat bertanya selayaknya kepada konsultan ataupun asisten_\n",
        parse_mode='Markdown')
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "*How to use QGPT bot*\n\n1. Start the conversation with /start\n2. Enter a question\n3. When the user is full, access /waitlist to get notified if there is a free slot\n4. End the conversation with /stop\n \n*For Your Information:*\n\n_Now QGPT already has memory for up to 9 past conversations, so you can ask questions like a consultant or assistant_\n",
        parse_mode='Markdown')
  if update.message.chat_id not in user_lang:
    print(f"{update.message.chat_id} BELUM MEMIIH BAHASA")
    language(update, context)


# --------------------------------------------------


# Fungsi untuk menangani kesalahan
def error(update: Update, context: CallbackContext) -> None:
  # Log error
  logger.warning(f"Update {update} caused error {context.error}")
  if user_lang[update.message.chat_id] == 'id':
    # Kirim pesan kesalahan ke pengguna
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Bentar.., saya lagi pusing😭")

  if user_lang[update.message.chat_id] == 'eng':
    # Kirim pesan kesalahan ke pengguna
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hold on.., I'm dizzy😭")


# --------------------------------------------------


def donate(update, context):
  if update.message.chat_id in user_lang:
    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "Anda dapat melakukan donasi melalui platform berikut:\n\nօ Saweria\t\t\t\t: https://saweria.co/qyuzet \nօ BuyMeCoffe : https://www.buymeacoffee.com/qzett"
      )
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "You can send the donations through the following platforms:\n\nօ Saweria\t\t\t\t: https://saweria.co/qyuzet \nօ BuyMeCoffe : https://www.buymeacoffee.com/qzett"
      )
  if update.message.chat_id not in user_lang:
    print(f"{update.message.chat_id} BELUM MEMIIH BAHASA")
    language(update, context)


# --------------------------------------------------


def community(update, context):
  if update.message.chat_id in user_lang:
    if user_lang[update.message.chat_id] == 'id':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "Gabung komunitas _Q-Community_ melalui link berikut:\n\nhttps://t.me/+aEyLSeavzX1jYTc1",
        parse_mode='Markdown')
    if user_lang[update.message.chat_id] == 'eng':
      context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
        "Join the _Q-Community_ via the following link:\n\nhttps://t.me/+aEyLSeavzX1jYTc1",
        parse_mode='Markdown')
  if update.message.chat_id not in user_lang:
    print(f"{update.message.chat_id} BELUM MEMIIH BAHASA")
    language(update, context)


def language(update, context):

  context.bot.send_message(
    chat_id=update.effective_chat.id,
    text="Choose Language (_pilih bahasa_): \n/english | /indonesia",
    parse_mode='Markdown')


def ID(update, context):
  user_lang[update.message.chat_id] = 'id'
  print(str(user_lang))

  context.bot.send_message(chat_id=update.effective_chat.id,
                           text="*Mode bahasa indonesia akif*",
                           parse_mode='Markdown')

  context.bot.send_message(chat_id=update.effective_chat.id,
                           text="_Akses /start untuk memulai_",
                           parse_mode='Markdown')


def ENG(update, context):
  user_lang[update.message.chat_id] = 'eng'
  print(str(user_lang))
  context.bot.send_message(chat_id=update.effective_chat.id,
                           text="*English language mode activated*",
                           parse_mode='Markdown')
  context.bot.send_message(chat_id=update.effective_chat.id,
                           text="_Click /start to start_",
                           parse_mode='Markdown')

  # # if user_lang[update.message.chat_id] == 'id' :
  #     user_lang[update.message.chat_id].append((question, response))
  # else:
  #     conversation_history[user_name] = [(question, response)]


# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------


def main():

  # Inisialisasi updater dan dispatcher
  updater = Updater(token='6107663477:AAHlcBPpPK6JSQVUYGDf8USKi__DFwMhHrA',
                    use_context=True)
  dispatcher = updater.dispatcher
  updater.dispatcher.add_error_handler(error)

  # Menambahkan handler untuk command "/start"
  start_handler = CommandHandler('start', start)
  dispatcher.add_handler(start_handler)

  # Menambahkan handler untuk command "/stop"
  stop_handler = CommandHandler('stop', stop)
  dispatcher.add_handler(stop_handler)

  # Menambahkan handler untuk pesan
  echo_handler = MessageHandler(Filters.text & ~Filters.command, echo)
  dispatcher.add_handler(echo_handler)

  # Menambahkan handler untuk command /active_user
  active_user_handler = CommandHandler('active_user', active_user)
  dispatcher.add_handler(active_user_handler)

  # Menambahkan handler untuk command /active_user
  donate_handler = CommandHandler('donate', donate)
  dispatcher.add_handler(donate_handler)

  # Menambahkan handler untuk command /waitlist
  waitinglist_handler = CommandHandler('waitlist', waitinglist)
  dispatcher.add_handler(waitinglist_handler)

  # Menambahkan handler untuk command /genesis
  dalle_handler = CommandHandler('genesis', dalle)
  dispatcher.add_handler(dalle_handler)

  # Menambahkan handler untuk command /gen_off
  stop_dalle_handler = CommandHandler('gen_off', stop_dalle)
  dispatcher.add_handler(stop_dalle_handler)

  # Menambahkan handler untuk command /community
  community_handler = CommandHandler('community', community)
  dispatcher.add_handler(community_handler)

  # Menambahkan handler untuk command /help
  help_handler = CommandHandler('help', help)
  dispatcher.add_handler(help_handler)

  # Menambahkan handler untuk command /language
  lang_handler = CommandHandler('lang', language)
  dispatcher.add_handler(lang_handler)

  # Menambahkan handler untuk command /bahasa indonesia
  langID_handler = CommandHandler('indonesia', ID)
  dispatcher.add_handler(langID_handler)

  # Menambahkan handler untuk command /bahasa inggris
  langENG_handler = CommandHandler('english', ENG)
  dispatcher.add_handler(langENG_handler)

  # Memulai bot
  updater.start_polling()
  updater.idle()


keep_alive()

if __name__ == '__main__':
  main()
