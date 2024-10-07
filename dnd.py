"""Это документация к оформлению кода для последующего редактирования. Я понимаю, что это усложняет редактирование при аварийных ситуациях, тем не менее, эти принципы крайне рекомендуются к соблюдению:

	1. Должны соблюдаться PEP 8 и PEP 257. Пожалуйста, прочитайте эти документы и хотя бы старайтесь им соответствовать. 
	   https://pythonworld.ru/osnovy/pep-8-rukovodstvo-po-napisaniyu-koda-na-python.html и https://pythonworld.ru/osnovy/dokumentirovanie-koda-v-python-pep-257.html соответственно.
	2. Старайтесь указывать в функциях параметры, которые вы задаёте. Это необходимо для упрощения дальнейшего редактирования.
	3. Делайте документацию ко всему. Всегда.
	4. Расставляйте код по категориям, чтобы всегда можно было легко найти что и где находится.
	5. Обособляйте взаимодействие с базой данных от взаимодействия с discord. Так просто удобно находить необходимые фрагменты кода.
	6. Используем snake_case, никаких верблюдов.

"""

import random
import asyncio
import sqlite3
import datetime
import discord
from discord.ext import commands
from tokens import token

# Задача базовых параметров.

intents = discord.Intents.default()
intents = discord.Intents.all()
bot = discord.Bot(intents = intents)
bot.auto_sync_commands = False
activity = discord.Activity(type = discord.ActivityType.custom, state = "test state")

dm_role_id = 1283712029198254090
server_id = 787280396915048498

log_channel = 1129758742448185364    #Может быть None (смотреть log())

## Взаимодействие с SQL.

connection = sqlite3.connect("parties.db")
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS parties (
		name TEXT,
		category_id INT,
		role_id INT,
		dm_id INT,
		members TEXT,
		invites TEXT
	)""")
connection.commit()

# База текстовых ответов.

statuses = ["Веди себя как заклинатель, колдунишка!", 
			"Получай, слащавый эльф!", 
			"Чё за заклинание он сотворяет?!", 
			"Передаю привет твоему божеству!", 
			"Бро, тебе нужно больше фехтовать.", 
			"Я готов очаровывать всех!", 
			"Гном, иди в шахту играй.", 
			"В утробу Селунэ, время отступать!", 
			"Я сейчас порву книгу заклинаний!", 
			"Это просто бардовское выступление!", 
			"Полурослик, чё ты делаешь?!", 
			"Магия работает!", 
			"Закрой харизмо-выдаватель!", 
			"Этот арбалет просто имба!", 
			"Я сидел в храме и молился весь год!", 
			"Если бы Гонд хотел, чтобы вы жили, он бы не выковал мой меч!", 
			"Я в Астральном плане прячусь!", 
			"Безмолвие со рта развей!", 
			"А для таких вообще латы создают?", 
			"Твоя сила набухнет от веры!", 
			"Саня, заклинание \"Ужас\" работает на них!", 
			"Не бойся, исчадие, изгнание будет не больно!", 
			"Ты под заклинанием \"Слабоумие\", ливни!", 
			"На в морду, орчище!", 
			"Поднимайся, союзник, быстрее! У МЕНЯ ТРУДНОПРОХОДИМАЯ МЕСТНОСТЬ, ЧЕРТ...", 
			"Вы тупые тролли! Я с вас поражаюсь!", 
			"Чёрт! Как Темпус позволил нам выиграть?!", 
			"Эй, гоблины, сейчас вам достанется девятой ячейкой!", 
			"Я содомировал дракона!",
			"Бум, критическое попадание!"
			]
reports = {"bot_online": "{0}{bot} был запущен.{0}",
"party_created": "{0}Группа создана{0}. Название: {0}{party}{0}, категория: {0}{category}{0}, роль: {role}, организатор: {owner}.",
"invite": "{0}{action}{0}. Тип: {0}{type}{0}, отправитель: {sender}, получатель: {recipient}, группа: {0}{party}{0}.",
"party_changed": "{0}{action}{0}. Участник: {member}, группа: {0}{party}{0}.",
"party_removed": "Группа {0}{party}{0} удалена пользователем {owner}.",
"status_changed": 'Статус изменён на "{status}"'
}
responds = {"bot_online": ["{bot} был запущен {time}."
						  ],
		   "party_created": ["`{party}` занесена в базу данных.",
							 "База данных обновлена.",
							 "Создана группа `{party}`.",
							 "Группа `{party}` зарегистрирована."
							 ],
		   "unexpected_error": ["Возникла непредвиденная ошибка. Уведомите администратора о ней, если она произошла с серверной стороны, в ином случае, повторите совершаемое действие.\n-# Известно о нестабильностях в последнее время со стороны самого Discord.\n```python\n{error}\n```"
								]
		   }
answers_invites = {"dm": ["`{inviting}` предлагает вам стать организатором группы \"`{party}`\"."],
				   "member": ["`{inviting}` предлагает вам стать участником группы \"`{party}`\"."]
				   }

# Функции.

def random_answer(dict, key):
	"""Функция случайного выбора элемента списка в словаре."""
	return random.choice(dict[key])

async def timed_status():
	"""Функция постоянной смены статуса."""
	while True:
		new_status = random.choice(statuses)
		await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.custom, state = new_status))
		await asyncio.sleep(delay = 30)
		await log("status_changed", status = new_status)

async def log(event, **kwargs):
	"""Отправляет отчёт о вызове команд, смене статуса и включении бота в определённый дискорд-канал (log_channel) и в консоль. event — ключ из словаря reports, а **kwargs — аргументы для format()"""
	console_kwargs = kwargs.copy()
	discord_kwargs = kwargs.copy()
	print("-----------------------------------\nkwargs:", kwargs, "\n")
	for key, value in console_kwargs.items():
		if isinstance(value, discord.Member):
			console_kwargs[key] = value.global_name
	print("console kwargs:", console_kwargs, "\n")
	print(str("{0}[" + datetime.datetime.now().strftime('%H:%M:%S') + "]{0} " + reports[event].format('{1}', **console_kwargs)).format("", ""))
	
	if log_channel is not None:
		print("kwargs (2):", kwargs, "\n")
		
		for key, value in discord_kwargs.items():
			if isinstance(value, discord.Member) or isinstance(value, discord.Role):
				discord_kwargs[key] = value.mention
		print("discord_kwargs", discord_kwargs, "\n")
				
		channel = await bot.fetch_channel(log_channel)
		await channel.send(str("{0}[" + datetime.datetime.now().strftime('%H:%M:%S') + "]{0} " + reports[event].format('{1}', **discord_kwargs)).format("`", "**"))
    
async def autocomplete_names(ctx):
	"""Функция для autocomplete в командах, где необходим список групп. Функция не используется в других местах, чтобы не вызывать конфликты из-за неизвестной мне работы autocomplete."""
	return [party[0] for party in cursor.execute(f"SELECT name FROM parties").fetchall()]
	

## Функции проверки.

def is_dm(ctx):
	"""Функция проверки наличия роли организатора."""
	return ctx.author.get_role(dm_role_id) is not None

def is_party_owner(ctx, party_name):
	"""Функция проверки, является ли автор сообщения организатором указанной группы."""
	return ctx.author.id == cursor.execute(f"SELECT dm_id FROM parties WHERE name = '{party_name}'").fetchone()[0]
		
def is_party_member(ctx, member, party_name):
	"""Функция проверки, является ли пользователь участником указанной группы."""
	return member in cursor.execute(f"SELECT members FROM parties WHERE name = '{party_name}'").fetchone()[0].split(", ")

## Функции категории manage_party.

async def change_dm(ctx, member, party_name):
	"""Функция смены организатора группы. Использует функцию request() для подтвереждения согласия."""
	#await ctx.defer()
	if await request(
		ctx,
		member = member,
		party_name = party_name,
		text = random_answer(dict = answers_invites, key = "dm"),
		type = "передача прав"
		):
		try:
			cursor.execute(f"UPDATE parties SET dm_id = {member.id} WHERE name = '{party_name}'")
			connection.commit()
			category = discord.utils.get(ctx.guild.categories, id = cursor.execute(f"SELECT category_id FROM parties WHERE name = '{party_name}'").fetchone()[0])

			await category.set_permissions(
				target = ctx.author,
				overwrite = None
				)
			await category.set_permissions(
				target = member,
				view_channel = True,
				manage_channels = True,
			    manage_permissions = True
				)
			await kick_party_member(guild = ctx.guild, member = member, party_name = party_name)
		except Exception as err:
			await ctx.respond(f"Не удалось заменить организатора группы {party_name} на {member}: `{err}`")
			return False
		await log("party_changed", action = "Произошла смена организатора", member = member, party = party_name)
		return True

async def invite_to_party(ctx, member, party_name):
	"""Функция добавления участника группы. Использует функцию request() для подтвереждения согласия."""
	if await request(
		ctx,
		member = member,
		party_name = party_name,
		text = random_answer(dict = answers_invites, key = "member"),
		type = "приглашение"
		):
		try:
			current_members = cursor.execute(f"SELECT members FROM parties WHERE name = '{party_name}'").fetchone()[0]
			new_list_of_members = f"{current_members}, {member.id}" if len(current_members) > 0 else member.id
			cursor.execute(f"UPDATE parties SET members = '{new_list_of_members}' WHERE name = '{party_name}'")
			connection.commit()

			await member.add_roles(ctx.guild.get_role(int(cursor.execute(f"SELECT role_id FROM parties WHERE name = '{party_name}'").fetchone()[0])))
		except Exception as err:
			await ctx.respond(f"Не удалось взаимодействовать с {member}: `{err}`")
			return False
		await log("party_changed", action = "Участник включён в группу", member = member, party = party_name)
		return True

class requestView(discord.ui.View):
	"""Класс для упрощения взаимодействия с view функции request()."""
	def __init__(self):
		super().__init__()
		self.value = None
		self.timeout = None
		
	@discord.ui.button(label = "Принять",
					   style = discord.ButtonStyle.green)
	async def accept_callback(self, button, interaction):
		await interaction.response.send_message("Запрос принят.")
		await interaction.message.edit(view = self.disable_all_items())
		self.value = True
		self.stop()

	@discord.ui.button(label = "Отклонить",
					   style = discord.ButtonStyle.red)
	async def reject_callback(self, button, interaction):
		await interaction.response.send_message("Запрос отклонён.")
		await interaction.message.edit(view = self.disable_all_items())
		self.value = False
		self.stop()

async def request(ctx, member, party_name, text, type):
	"""Функция проверки согласия пользователя на то или иное действие."""
	if ctx.author.id == member.id:
		await ctx.respond("Вы не можете взаимодействовать сами с собой.")
		return False

	if member.id in cursor.execute(f"SELECT invites FROM parties WHERE name = '{party_name}'").fetchone()[0].split(", "):
		await ctx.respond("Этому участнику уже отправлен запрос.")
		return False

	current_invites = cursor.execute(f"SELECT invites FROM parties WHERE name = '{party_name}'").fetchone()[0]
	if member.id not in current_invites.split(", "):
		new_list_of_invites = f"{current_invites}, {member.id}" if len(current_invites) > 0 else member.id
		cursor.execute(f"UPDATE parties SET invites = '{new_list_of_invites}' WHERE name = '{party_name}'")
		connection.commit()

		View = requestView()
		dm = member.dm_channel
		if dm is None:
			try:
				dm = await member.create_dm()
			except:
				await ctx.respond("Не удалось создать личные сообщения с пользователем.")
				return False
		await ctx.respond("Запрос отправлен.")
		await dm.send(content = text.format(inviting = ctx.author.global_name, party = party_name), view = View)
		await log("invite", action = "Запрос отправлен", type = type, sender = ctx.author, recipient = member, party = party_name)
		await View.wait()
		if View.value:
			await ctx.respond(f"{member} принял запрос о взаимодействии с `{party_name}`")
			await log("invite", action = "Запрос принят", type = type, sender = ctx.author, recipient = member, party = party_name)
		else:
			await ctx.respond(f"{member} отклонил запрос о взаимодействии с `{party_name}`")
			await log("invite", action = "Запрос отклонён", type = type, sender = ctx.author, recipient = member, party = party_name)

		# Этот фрагмент кода был продублирован для удаления приглашения из базы данных. Поскольку функция асинхронная, приходится удлинять код.
		current_invites = cursor.execute(f"SELECT invites FROM parties WHERE name = '{party_name}'").fetchone()[0].split(', ')
		current_invites.remove(str(member.id))
		new_list_of_invites = ", ".join(current_invites)
		cursor.execute(f"UPDATE parties SET invites = '{new_list_of_invites}' WHERE name = '{party_name}'")
		connection.commit()

		return View.value
	else:
		await ctx.respond("Вы уже отправляли недавно запрос этому пользователю. Дождитесь ответа.")
		return False

async def kick_party_member(guild, member, party_name = None):
	"""Функция исключения пользователя из группы. Исключает пользователя из всех групп, если не указан party_name."""
	if party_name is not None:
		parties = [party_name]
	else:
		parties = [party[0] for party in cursor.execute(f'SELECT name FROM parties').fetchall()]
	for party_name in parties:
		current_members = cursor.execute(f"SELECT members FROM parties WHERE name = '{party_name}'").fetchone()[0].split(', ')
		if str(member.id) in current_members:
			current_members.remove(str(member.id))
			new_list_of_members = ", ".join(current_members)

			cursor.execute(f"UPDATE parties SET members = '{new_list_of_members}' WHERE name = '{party_name}'")
			connection.commit()

			try: # На случай, если пользователь ливнул.
				await member.remove_roles(guild.get_role(int(cursor.execute(f"SELECT role_id FROM parties WHERE name = '{party_name}'").fetchone()[0])))
			except discord.errors.NotFound:
				pass
			
			await log("party_changed", action = "Участник исключён", member = member, party = party_name)
			return True
		else:
			return False

# Обработка запуска.

@bot.event
async def on_ready():
	if not bot.auto_sync_commands: # Этот блок необходим для дебаггинга. ID гильдии ниже поменять на свой тестовый сервер, bot.auto_sync_commands переключить на False.
		await bot.sync_commands(guild_ids = [server_id])
	print(f"Подключённые команды: {', '.join(command.name for command in bot.commands)}.")
	#print(random_answer(dict = responds, key = "bot_online").format(bot = bot.user, time = datetime.datetime.now().strftime('%H:%M:%S')))
	await log("bot_online", bot = bot.user)
	print(f"bot_status: {bot.status}")
	# await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.custom, state = f"Запуск произведён {datetime.datetime.now().strftime('%H:%M:%S')}")) # Этот блок тоже необходим для дебаггинга. Отключите timed_status() перед этим.

	await timed_status()

# Непосредственно application commands.

@bot.application_command(name = "создать_группу", description = "Создаёт группу по интересам")
@commands.check(is_dm)
async def create_party(ctx,
		party_name: discord.Option(
			str,
			name = "название_группы",
			description = "Должно быть уникальным, поскольку это название используется в базе данных.",
			required = True
			),
		category_name: discord.Option(
			str,
			name = "название_категории",
			description = "Бот создаст категорию с данным названием для группы. Оно может отличаться от названия самой группы.",
			required = True
			)):
	"""Функция создания группы."""
	await ctx.defer()
	if party_name not in [party[0] for party in cursor.execute(f"SELECT name FROM parties").fetchall()]:
		role = await ctx.guild.create_role(name = f'Жетон "{party_name.capitalize()}"')
		await role.edit(colour = discord.Colour.random())
		category = await ctx.guild.create_category(name = category_name, position = 3)
		await category.set_permissions(
			target = ctx.author,
			view_channel = True,
			manage_channels = True,
			manage_permissions = True
			)
		await category.set_permissions(
			target = role,
			view_channel = True
			)
		await category.set_permissions(
			target = ctx.guild.default_role,
			view_channel = False
			)
		cursor.execute(f"INSERT INTO parties VALUES ('{party_name}', {category.id}, {role.id}, {ctx.author.id}, '', '')")
		connection.commit()
		await log("party_created", party = party_name, category = category_name, role = role, owner = ctx.author)
		await ctx.respond(f"{random_answer(dict = responds, key = 'party_created').format(party = party_name)} Создана категория `{category_name}`. Роль группы: {role.mention}.")
	else:
		await ctx.respond("Это имя группы уже занято.")

@create_party.error
async def create_party_error(ctx, error):
	await ctx.defer()
	if type(error) is discord.errors.CheckFailure:
		await ctx.respond("У вас недостаточно прав для создания группы.")
	else:
		await ctx.respond(random_answer(dict = responds, key = "unexpected_error").format(error = error))

@bot.application_command(name = "распоряжаться_группой", description = "Приглашает или убирает участников, а также позволяет сменить владельца группы.")
async def manage_party(
		ctx,
		party_name: discord.Option(
			str,
			name = "название_группы",
			description = "То уникальное название, что вы вводили при создании группы.",
			autocomplete = discord.utils.basic_autocomplete(autocomplete_names),
			required = True
			),
		action: discord.Option(
			str,
			name = "действие",
			choices = ["передать права организатора", "пригласить в группу", "выгнать из группы"],
			required = True
			),
		target: discord.Option(
			discord.Member,
			name = "участник",
			required = True
			)):
	"""Функция изменения тех или иных параметров группы."""
	await ctx.defer()
	if is_party_owner(ctx, party_name = party_name):
		if action == "передать права организатора":
			await change_dm(ctx, member = target, party_name = party_name)
		elif action == "пригласить в группу":
			if is_party_member(ctx, member = target, party_name = party_name):
				await ctx.respond(f"{target} уже является участником группы `{party_name}`.")
			else:
				await invite_to_party(ctx, member = target, party_name = party_name)
		elif action == "выгнать из группы":
			if not await kick_party_member(guild = ctx.guild, member = target, party_name = party_name):
				await ctx.respond(f"{target} не является участником группы `{party_name}`.")
			else:
				await ctx.respond(f"{target} удалён из группы `{party_name}`")
	else:
		await ctx.respond("Вы не являетесь организатором данной группы.")

@manage_party.error
async def manage_party_error(ctx, error):
	await ctx.defer()
	if type(error) is TypeError:
		await ctx.respond("Такой группы не существует.")
	else:
		await ctx.respond(random_answer(dict = responds, key = "unexpected_error").format(error = error))

@bot.application_command(name = "удалить_группу")
async def delete_party(
		ctx,
		party_name: discord.Option(
			str,
			name = "название_группы",
			description = "То уникальное название, что вы вводили при создании группы.",
			required = True
			)):
	"""Функция удаления группы."""
	await ctx.defer()
	try:
		if is_party_owner(ctx, party_name = party_name):
			try:
				await ctx.guild.get_role(int(cursor.execute(f"SELECT role_id FROM parties WHERE name = '{party_name}'").fetchone()[0])).delete()
				await discord.utils.get(ctx.guild.categories, id = cursor.execute(f"SELECT category_id FROM parties WHERE name = '{party_name}'").fetchone()[0]).set_permissions(
					target = ctx.author, 
					overwrite = None
					)
				await discord.utils.get(ctx.guild.categories, id = cursor.execute(f"SELECT category_id FROM parties WHERE name = '{party_name}'").fetchone()[0]).set_permissions(
					target = ctx.guild.default_role,
					view_channel = False
					)
			except:
				pass
			cursor.execute(f"DELETE FROM parties WHERE name = '{party_name}'")
			connection.commit()
			await log("party_removed", party = party_name, owner = ctx.author)

			await ctx.respond(f"Группа `{party_name}` была удалена.")
		else:
			await ctx.respond("Вы не являетесь организатором данной группы.")
	except TypeError:
		await ctx.respond("Этой группы не существует.")

@bot.application_command(name="просмотреть")
async def list(
	ctx,
	option: discord.Option(
		str,
		name = "выбор",
		choices = ["список групп", "информация о группе"],
		required = True
		),
	party_name: discord.Option(
		str,
		name = "группа",
		description = "Это поле обязательно для опции \"player-list\"",
		autocomplete = discord.utils.basic_autocomplete(autocomplete_names),
		required = False
		)):
	"""Функция просмотра списка тех или иных параметров."""
	await ctx.defer(ephemeral = True)
	if option == "список групп":
		await ctx.respond(f"Список активных групп: {', '.join([party[0] for party in cursor.execute(f'SELECT name FROM parties').fetchall()])}")
	elif option == "информация о группе":
		if party_name is None:
			await ctx.respond(random_answer(dict = responds, key = "unexpected_error").format(error = "Хаха! Попался, педик! Я же говорил, что поле \"party_name\" обязательно для опции \"player-list\"!"))
		else:
			dm = cursor.execute(f"SELECT dm_id FROM parties WHERE name = '{party_name}'").fetchone()[0]
			members = cursor.execute(f"SELECT members FROM parties WHERE name = '{party_name}'").fetchone()[0].split(', ')
			if not (members[0] == ""):
				text = ""
				for member in members:
					text += f"<@!{member}>, "
				await ctx.respond(f"Организатор: {await bot.get_or_fetch_user(int(dm))}.\nУчастники: {text[:-2]}.") 
			else:
				await ctx.respond(f"Организатор: {await bot.get_or_fetch_user(int(dm))}.\nУчастники: отсутствуют.") 

@bot.event
async def on_member_remove(member):
	await kick_party_member(guild = member.guild, member = member)

bot.run(token)
