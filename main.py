# -----Разраб: ento_Vanek-----
# -----Подключение библиотек-----
from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
from peewee import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton


# -----Настройки-----
TOKEN = "111:xxx"
proxy_url = 'http://proxy.server:3128'
bot = Bot(token=TOKEN, proxy=proxy_url)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# -----Объявляем списки-----
data_name = []
data_age = []
data_description = []
data_city = []
data_id_user = []
data_id_user_old = []

# -----Скилет базы-----
class Person(Model):
    name = CharField()
    age = IntegerField()
    id_user = IntegerField()
    username = CharField()
    city = CharField()
    description = TextField()

    class Meta:
        database = SqliteDatabase('data.db')

# -----FSM - aiogram (машина состояний)-----
class AwaitMessages(StatesGroup):
    age = State()
    city = State()
    description = State()
    left = State()
    photo = State()

SqliteDatabase('data.db').create_tables([Person])

# -----Точка входа-----
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
	# -----Проверка на регистрацию-----
	try:
		for i in Person.select().where(Person.id_user == msg.from_user.id):
			user_data = "{}, {}, {}\n{}\nТы уже зарегистрирован. Смотреть анкеты?".format(i.name, i.age, i.city, i.description)
		button_yes = KeyboardButton('👀Да👀')
		button_no = KeyboardButton('💣Заполнить анкету💣')
		greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_yes, button_no)
		await bot.send_photo(msg.chat.id, types.InputFile('photo//{}.jpg'.format(msg.from_user.id)), caption=user_data, reply_markup=greet_kb)
		await AwaitMessages.left.set()
	except:	
		button_hi = KeyboardButton('💣Начать!💣')
		greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_hi)
		await bot.send_message(msg.from_user.id, "📍Привет! Этот бот предназначен для мотобратьев. Здесь ты можешь найти людей которые ищут с кем можно покататься.📍", reply_markup=greet_kb)

@dp.message_handler(lambda msg: msg.text == "💣Заполнить анкету💣")
async def re_complite(msg):
	await bot.send_message(msg.from_user.id, "Хорошо! Буду называть тебя " + msg.from_user.first_name)
	await bot.send_message(msg.from_user.id, "🔥Пришли фото своего аппарата🔥")
	await AwaitMessages.photo.set()

@dp.message_handler(lambda msg: msg.text == "💣Начать!💣")
async def echo_message(msg: types.Message):
	await bot.send_message(msg.from_user.id, "Хорошо! Буду называть тебя " + msg.from_user.first_name)
	await bot.send_message(msg.from_user.id, "🔥Пришли фото своего аппарата🔥")
	await AwaitMessages.photo.set()

@dp.message_handler(content_types=['photo'], state=AwaitMessages.photo)
async def get_photo(msg):
	# -----Забираем фото от юзера-----
	await msg.photo[-1].download('photo//{}.jpg'.format(msg.from_user.id))
	await bot.send_message(msg.from_user.id, "🔢Сколько тебе лет?🔢")
	await AwaitMessages.age.set()

@dp.message_handler(state=AwaitMessages.age)
async def get_city(msg, state: FSMContext):
	# -----Забираем возраст у юзера-----
	async with state.proxy() as data:
		data['age'] = msg.text
	await bot.send_message(msg.from_user.id, "🌍С какого ты города?🌍")
	await AwaitMessages.city.set()

@dp.message_handler(state=AwaitMessages.city)
async def get_bio(msg, state: FSMContext):
	# -----Забираем город у юзера-----
	async with state.proxy() as data:
		data['city'] = msg.text
	await bot.send_message(msg.from_user.id, "💣Напиши что-то про себя и своего стального коня💣")
	await AwaitMessages.description.set()

@dp.message_handler(state=AwaitMessages.description)
async def questionnaire(msg, state: FSMContext):
	# -----Забираем описание у юзера-----
	async with state.proxy() as data:
		data['description'] = msg.text
	await bot.send_message(msg.from_user.id, "🥳Всё готово! Вот твоя анкета...🥳")
	# -----Сохраняем и спрашиваем правильно или нет-----
	try:
		user = Person(name=msg.from_user.first_name, age=data["age"], id_user=msg.from_user.id, city=data['city'].lower(), description=data['description'], username=msg.from_user.username)
		user.save()
	except:
		user = Person(name=msg.from_user.first_name, age=data["age"], id_user=msg.from_user.id, city=data['city'].lower(), description=data['description'], username="")
		user.save()
	for i in Person.select().where(Person.id_user == msg.from_user.id):
		user_data = "{}, {}, {}\n{}".format(i.name, i.age, i.city, i.description)
	await bot.send_photo(msg.chat.id, types.InputFile('photo//{}.jpg'.format(msg.from_user.id)), caption=user_data)
	btn_yes = KeyboardButton('👀Да👀')
	btn_no = KeyboardButton('💣Заполнить анкету💣')
	gr_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(btn_yes, btn_no)
	await bot.send_message(msg.from_user.id, "Всё правильно?", reply_markup=gr_kb)
	await AwaitMessages.left.set()

@dp.message_handler(state=AwaitMessages.left)
async def echo_message(msg: types.Message, state: FSMContext):
	# -----Админка-----
	if msg.text == "!admin":
		if msg.from_user.id == 772328798:
			btn_yes = KeyboardButton('💣!Кол-во юзеров!💣')
			btn_no = KeyboardButton('💣!Рассылка!💣')
			btn_pass = KeyboardButton('💣Продолжить просмотр анкет💣')
			gr_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(btn_yes, btn_no, btn_pass)
			await bot.send_message(msg.from_user.id, "Выбери нужное...", reply_markup=gr_kb)
		else:
			await bot.send_message(msg.from_user.id, "Ты не админ!")
	if msg.text == "💣!Кол-во юзеров!💣" and msg.from_user.id == 772328798:
		amount_people = 0
		for i in Person.select().where(Person.id_user):
			amount_people += 1
		await bot.send_message(msg.from_user.id, "В боте зарегистрировано {} человек".format(amount_people))
		btn_yes = KeyboardButton('💣!Кол-во юзеров!💣')
		btn_no = KeyboardButton('💣!Рассылка!💣')
		btn_pass = KeyboardButton('💣Продолжить просмотр анкет💣')
		gr_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(btn_yes, btn_no, btn_pass)
		await bot.send_message(msg.from_user.id, "Выбери нужное...", reply_markup=gr_kb)
	if msg.text == "💣!Рассылка!💣" and msg.from_user.id == 772328798:
		await bot.send_message(772328798, "Введи текст рассылки (не менее 20 символов)...")
	if msg.from_user.id == 772328798 and len(msg.text) >= 20 and "!!!" in msg.text:
		for i in Person.select().where(Person.id_user):
			await bot.send_message(i.id_user, "{}".format(msg.text))
		await bot.send_message(772328798, "Закончил рассылку по юзерам!")
	# -----Забираем анкеты с базы и скидываем юзеру-----
	if msg.text == '👀Да👀' or msg.text == "💣Продолжить просмотр анкет💣" or msg.text == '💣Смотреть анкеты💣':
		user_data = ''
		await bot.send_message(msg.from_user.id, "👀Начинаю поиск анкет...👀")
		for i in Person.select().where(Person.id_user != msg.from_user.id):
			if msg.text == "💣Продолжить просмотр анкет💣":
				pass
			else:
				data_name.append(i.name)
				data_age.append(i.age)
				data_city.append(i.city)
				data_id_user.append(i.id_user)
				data_id_user_old.append(i.id_user)
				data_description.append(i.description)
		try:
			user_data = "{}, {}, {}\n{}".format(data_name[0], data_age[0], data_city[0], data_description[0])
		except:
			button_yes = KeyboardButton('💣Моя анкета💣')
			button_no = KeyboardButton('💣Смотреть анкеты💣')
			button_del = KeyboardButton('💤Отключить мою анкету💤')
			greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_yes, button_no, button_del)
			await bot.send_message(msg.from_user.id, "👻Анкеты закончились, подождём пока тебя кто-то лайкнет...👻", reply_markup=greet_kb)
		else:
			await bot.send_photo(msg.chat.id, types.InputFile('photo//{}.jpg'.format(data_id_user[0])), caption=user_data)
			data_name.remove(data_name[0])
			data_age.remove(data_age[0])
			data_city.remove(data_city[0])
			data_description.remove(data_description[0])
			data_id_user.remove(data_id_user[0])
			button_yes = KeyboardButton('💣Лойс!💣')
			button_no = KeyboardButton('💩Ну такое...💩')
			button_my_add = KeyboardButton('💣Моя анкета💣')
			button_del = KeyboardButton('💤Отключить мою анкету💤')
			greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_yes, button_no, button_del, button_my_add)
			await bot.send_message(msg.from_user.id, "Как тебе?", reply_markup=greet_kb)
	if msg.text == '💣Заполнить анкету💣':
		# -----Удаляем юзера с базы и регистрируем заново-----
		query = Person.delete().where(Person.id_user == msg.from_user.id)
		query.execute()
		await re_complite(msg)
		return 
	if msg.text == "💣Лойс!💣":
		# -----Скидываем с базы юзернэйм или id понравившегося юзера и уведомляем его-----
		try:
			for i in Person.select().where(Person.id_user == data_id_user_old[0]):
				if i.username != "":
					await bot.send_message(msg.chat.id, '@{}\n🔥Хороших покатушек!🔥'.format(i.username))
					await bot.send_message(int(data_id_user_old[0]), 'Тобой заинтересовался @{}\nХороших покатушек!'.format(msg.from_user.username))
				else:
					await bot.send_message(msg.from_user.id, '<a href="https://web.telegram.org/k/#{}">Тык</a>\n🔥Хороших покатушек!🔥'.format(data_id_user_old[0]), parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
					await bot.send_message(int(data_id_user_old[0]), 'Тобой заинтересовался\n<a href="https://web.telegram.org/k/#{}">Тык</a>\nХороших покатушек!'.format(msg.from_user.id), parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
			data_id_user_old.remove(data_id_user_old[0])
			user_data = "{}, {}, {}\n{}".format(data_name[0], data_age[0], data_city[0], data_description[0])
			await bot.send_photo(msg.chat.id, types.InputFile('photo//{}.jpg'.format(data_id_user[0])), caption=user_data)
			data_name.remove(data_name[0])
			data_age.remove(data_age[0])
			data_city.remove(data_city[0])
			data_description.remove(data_description[0])
			data_id_user.remove(data_id_user[0])
			button_yes = KeyboardButton('💣Лойс!💣')
			button_no = KeyboardButton('💩Ну такое...💩')
			button_my_add = KeyboardButton('💣Моя анкета💣')
			button_del = KeyboardButton('💤Отключить мою анкету💤')
			greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_yes, button_no, button_del, button_my_add)
			await bot.send_message(msg.from_user.id, "Как тебе?", reply_markup=greet_kb)
		except:
			button_yes = KeyboardButton('💣Моя анкета💣')
			button_no = KeyboardButton('💣Смотреть анкеты💣')
			button_del = KeyboardButton('💤Отключить мою анкету💤')
			greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_yes, button_no, button_del)
			await bot.send_message(msg.from_user.id, "👻Анкеты закончились, подождём пока тебя кто-то лайкнет...👻", reply_markup=greet_kb)
		await AwaitMessages.left.set()
	if msg.text == "💩Ну такое...💩":
		# -----Пролистываем-----
		try:
			data_id_user_old.remove(data_id_user_old[0])
			user_data = "{}, {}, {}\n{}".format(data_name[0], data_age[0], data_city[0], data_description[0])
			await bot.send_photo(msg.chat.id, types.InputFile('photo//{}.jpg'.format(data_id_user[0])), caption=user_data)
			data_name.remove(data_name[0])
			data_age.remove(data_age[0])
			data_city.remove(data_city[0])
			data_description.remove(data_description[0])
			data_id_user.remove(data_id_user[0])
			button_yes = KeyboardButton('💣Лойс!💣')
			button_no = KeyboardButton('💩Ну такое...💩')
			button_my_add = KeyboardButton('💣Моя анкета💣')
			button_del = KeyboardButton('💤Отключить мою анкету💤')
			greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_yes, button_no, button_del, button_my_add)
			await bot.send_message(msg.from_user.id, "Как тебе?", reply_markup=greet_kb)
		except:
			button_yes = KeyboardButton('💣Моя анкета💣')
			button_no = KeyboardButton('💣Смотреть анкеты💣')
			button_del = KeyboardButton('💤Отключить мою анкету💤')
			greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_yes, button_no, button_del)
			await bot.send_message(msg.from_user.id, "👻Анкеты закончились, подождём пока тебя кто-то лайкнет...👻", reply_markup=greet_kb)
		await AwaitMessages.left.set()
	if msg.text == "💣Моя анкета💣":
		# -----Запрашиваем анкету с базы-----
		for i in Person.select().where(Person.id_user == msg.from_user.id):
			user_data = "{}, {}, {}\n{}".format(i.name, i.age, i.city, i.description)
		await bot.send_message(msg.from_user.id, "Твоя анкета...")
		button_yes = KeyboardButton('💣Продолжить просмотр анкет💣')
		button_no = KeyboardButton('💣Заполнить анкету💣')
		button_del = KeyboardButton('💤Отключить мою анкету💤')
		greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_yes, button_no, button_del)
		await bot.send_photo(msg.chat.id, types.InputFile('photo//{}.jpg'.format(msg.from_user.id)), caption=user_data, reply_markup=greet_kb)
	if msg.text == "💤Отключить мою анкету💤":
		# -----Удаляем анкету-----
		query = Person.delete().where(Person.id_user == msg.from_user.id)
		query.execute()
		button_hi = KeyboardButton('💣Заполнить анкету💣')
		greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_hi)
		await bot.send_message(msg.from_user.id, "🥹Удалил твою анкету, надеюсь ты ещё вернёшься. Я буду скучать...🥹", reply_markup=greet_kb)

if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)
