import discord
from discord.ext import commands
import random
import asyncio
from tokens import token
# import manage

activity = discord.Activity(type=discord.ActivityType.custom, state='test state')
bot = discord.Bot()
bot.auto_sync_commands = True
# intents = discord.Intents.all()
# intents.message_content = True

dm_role_id = 1283892392700805243

db = {'test_party': {'dm': 637590037751660544, 'members': set()}}  #пастроим тут бальшы бальшы бд
invites = dict() #это можно в бд перенести

statuses = ['Веди себя как заклинатель, колдунишка!', 
            'Получай, слащавый эльф!', 'Чё за заклинание он сотворяет?!', 
            'Передаю привет твоему божеству!', 
            'Бро, тебе нужно больше фехтовать.', 
            'Я готов очаровывать всех!', 
            'Гном, иди в шахту играй.', 
            'В утробу Селунэ, время отступать!', 
            'Я сейчас порву книгу заклинаний!', 
            'Это просто бардовское выступление!', 
            'Полурослик, чё ты делаешь?!', 
            'Магия работает!', 
            'Закрой харизмо-выдаватель!', 
            'Этот арбалет просто имба!', 
            'Я сидел в храме и молился весь год!', 
            'Если бы Гонд хотел, чтобы вы жили, он бы не выковал мой меч!', 
            'Я в Астральном плане прячусь!', 
            'Безмолвие со рта развей!', 
            'А для таких вообще латы создают?', 
            'Твоя сила набухнет от веры!', 
            'Саня, заклинание "Ужас" работает на них!', 
            'Не бойся, исчадие, изгнание будет не больно!', 
            'Ты под заклинанием "Слабоумие", ливни!', 
            'На в морду, орчище!', 
            'Поднимайся, союзник, быстрее! У МЕНЯ ТРУДНОПРОХОДИМАЯ МЕСТНОСТЬ, ЧЕРТ...', 
            'Вы тупые тролли! Я с вас поражаюсь!', 
            'Чёрт! Как Темпус позволил нам выиграть?!', 
            'Эй, гоблины, сейчас вам достанется девятой ячейкой!', 
            'Я содомировал дракона!', 'Бум, критическое попадание!']

reports = {'bot_online': ['{bot} на проводе.', '{bot} is ready.', '{bot} готов к труду и обороне.', '{bot} успешно запущен.'],
           'party_created': ['`{party}` занесена в базу данных.', 'База данных обновлена.', 'Создана партия `{party}`.', 'Партия `{party}` зарегистрирована.'],
           'unexpected_error': ['```python\n-{error}\n```\nЕбитесь с этим сами.', '```python\n{error}\n```\nНу вот чини теперь.','Диверсия!\n```python\n{error}\n```', 'dnd.py создаёт скриптовые ошибки!\n```python\n{error}\n```', 'An error occured!\n```python\n{error}\n```', 'Проклятые эльфы!\n```python\n{error}\n```', 'Специальная Выполняемая Операция идёт по плану.\n||```python\n{error}\n```||', 'Гномы кодокрады реальны!\n```python\n{error}\n```']
           }
invites = {'dm': ['{inviting} предлагает вам стать ДМом партии {party}.'], 'member': ['{inviting} предлагает вас стать участником партии {party}.']}


class invitationView(discord.ui.View):    #timeout=86400.0
    def __init__(self):
        super().__init__()
        self.value = None
        
    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green)
    async def accept_callback(self, button, interaction):
        await interaction.response.send_message("Приглашение принято.") #ephemeral=True
        self.value = True
        self.stop()


    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red)
    async def reject_callback(self, button, interaction):
        await interaction.response.send_message("Приглашение отклонено.")
        self.value = False
        self.stop()


def r(d, key):
    return random.choice(d[key])

async def timed_status():
    while True:
        status = random.choice(statuses)
        activity = discord.Activity(type=discord.ActivityType.custom, state=status)
        await bot.change_presence(activity = activity)
        await asyncio.sleep(30, result=f'chainging status to "{status}"')
    

async def invite(ctx, user, party_name, text):        #makes an embed and sends an invite. True if user resonse is "Принять", False otherwise
    if ctx.author.id == user.id:
        await ctx.respond('Ты уже в списке.')
        return False
    try:
        l = invites[party_name]
    except KeyError:
        invites[party_name] = set()
        invites[party_name].add(user.id)
    if invites[party_name].isdisjoint({user.id}):
        await ctx.respond('Этому участнику уже отправлено приглашение.')
        return False
    View = invitationView()
    print(View, type(View))
    dm = user.dm_channel
    if dm is None:
        print('direct messages channel is None')
        dm = await user.create_dm()
    await ctx.respond('Приглашение отправлено.')
    await dm.send(content = text.format(inviting = ctx.author.global_name, party = party_name), view = View)
    await View.wait()
    if View.value:
        await ctx.respond(f'{user} принял приглашение в {party_name}')
    elif View.value == False:
        await ctx.respond(f'{user} отклонил приглашение в {party_name}')
    return View.value
    
    
async def promote_dm(ctx, member, party_name):        #calls invite() and waits. When positive response is received, if it's True, changes party's dm id.
    if (await invite(ctx, member, party_name, r(invites, 'dm'))):
    	try:
                      db[party_name]['dm'] = member.id
    		print(db)
    	except Exception as err:
    		await ctx.respond(f'Не удалось заменить ДМа партии {party_name} на {member}: `{err}`') #, r(reports, unexpected_error)
    		return False
    	#await ctx.respond
    	return True

async def invite_to_party(ctx, member, party_name):   #calls invite() and waits. When response is received, if it's True, adds the user to party's member list
    if (await invite(ctx, member, party_name, r(invites,'member'))):
    	try:
    		db[party_name]['members'].add(member.id)
    		print(db)
    	except Exception as err:
    		#await ctx.respond(r(reports, unexpected_error))
    		await ctx.respond(f'Не удалось добавить {member} в список участников: `{err}`')
    		return False
    	return True

async def fetch_players(ctx, party_name):
    l = []
    for player in db[party_name]['members']:
        l.append(str(await bot.get_or_fetch_user(player)))
    return ', '.join(l)
        

#', '.join(await bot.get_or_fetch_user(player).name for player in db[party_name]['members'])

#checks
def is_dm(ctx):
    return ctx.author.get_role(dm_role_id) is not None

def is_party_owner(ctx, party_name):
    return ctx.author.id == db[party_name]['dm']
        
def is_party_member(ctx, user, party_name):
    return db[party_name]['members'].isdisjoint(set(user.id))
    
@bot.application_command(name="создать-партию", description="Создать партию D&D")
@commands.check(is_dm)
async def create_party(
        ctx,
        party_name: discord.Option(
            str,
            name = 'название_партии',
            description = 'Должно быть уникальным, это название используется в БД.'
        ),
        category_name: discord.Option(
            str,
            name = 'название_категории',
            description = 'Бот создаст категорию с данным названием для партии.'
        )
):
    db[party_name] = {'dm': ctx.author.id, 'members': []}

    category = await ctx.guild.create_category(category_name, position = 0)
    await category.set_permissions(ctx.author, manage_channels = True, manage_permissions = True)

    # db_file = open("db.txt", mode="a")
    # db_file.write("\n" + party_name)
    # db_file.close()
    await ctx.respond(r(reports, 'party_created').format(party = party_name) + f' Создана категория `{category_name}`.')

@create_party.error
async def create_party_error(ctx, error):
    if type(error) is discord.errors.CheckFailure:
        await ctx.respond('Не дорос, сынок.')
    else:
        await ctx.respond(r(reports, 'unexpected_error').format(error = error))
        

@bot.application_command(name="распоряжаться-партией", description="Приглашает или убирает участников, а также позволяет сменить владельца партии.")
async def manage_party(
        ctx,
        party_name: discord.Option(
            str,
            name = 'название_партии',
            description = 'То уникальное название, что вы вводили при создании партии.',
            autocomplete = discord.utils.basic_autocomplete(db.keys())
        ),
        action: discord.Option(
            str,
            name = 'действие',
            choices = ['change_dm', 'invite_to_party', 'kick_out_of_party']
        ),
        target: discord.Option(discord.Member, name='участник')
):
    if(is_party_owner(ctx, party_name)):
#        await ctx.respond(f'Владелец, {action}')

        if action == 'change_dm':
            await promote_dm(ctx, target, party_name)

        elif action == 'invite_to_party':
            if is_party_member(ctx, target, party_name):
                await ctx.respond(f'{target} уже является участником партии `{party_name}`')
                return
            await invite_to_party(ctx, target, party_name)

        elif action == 'kick_out_of_party':
            try:
                db[party_name]['members'].remove(target.id)
            except KeyError:
                await ctx.respond(f'{target} не является участником партии `{party_name}`.')
                return
            await ctx.respond(f'{target} исключён из списка участников партии `{party_name}`.')
            
    else:
        raise discord.errors.CheckFailure('Не похож ты на владельца партии.')

@manage_party.error
async def create_party_error(ctx, error):
    if type(error) is discord.errors.CheckFailure:
        await ctx.respond('Самозванец.')
    else:
        await ctx.respond(r(reports, 'unexpected_error').format(error = error))


@bot.application_command(name='просмотреть')
async def list(ctx, option: discord.Option(str, name = 'выбор', choices = ['party-list', 'player-list']), party_name: discord.Option(str, name = 'партия', description = 'Это поле обязательно для опции "player-list"', autocomplete = discord.utils.basic_autocomplete(db.keys()), required = False)):
    if option == 'party-list':
        await ctx.respond('Список действующих партий: ' + ', '.join(party for party in db.keys()))
    elif option == 'player-list':
        if party_name is None:
            await ctx.respond(r(reports,'unexpected_error').format(error = 'Хаха! Попался, педик! Я же говорил, что поле "party_name" обязательно для опции "player-list"!'))
        dm = await bot.get_or_fetch_user(db[party_name]['dm'])
        print(dm, type(dm))
        await ctx.respond(f"DM: {dm} \nИгроки: {await fetch_players(ctx, party_name)}")


# def setup(bot):
#     bot.add_application_command(manage_party)

# def teardown(bot):
#     print("teardown")
   

@bot.event
async def on_ready():
    if not bot.auto_sync_commands:
        await bot.sync_commands()   #guild_ids=[1127574931970981898]
    print(", ".join(command.name for command in bot.commands))
    print(r(reports, 'bot_online').format(bot=bot.user))
    print('bot_status: ', bot.status, type(bot.status))
    await timed_status()
    
    
@bot.event
async def on_disconnect():
    print("disconnecting")
    bot.clear()
    # await bot.guilds[0].channels[0].send("<@!386912646609502229>")


bot.run(token)
#bot.add_application_command(create_party)
#bot.add_application_command(manage_party)
