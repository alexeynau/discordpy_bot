import json
from googletrans import Translator
from googlesearch import search
import re
import random
import discord
import lyricsgenius
from lyricsgenius import song
from datetime import timedelta
from discord.ext import commands
from config import settings

bot = commands.Bot(intents = discord.Intents.all(), command_prefix = settings['prefix'])

data = {} # Cловарь с данными о кол-ве игр и побед для каждого участика сервера  

genius = lyricsgenius.Genius(settings['genius_token'])

#========= Загрузка информации о командах ============
bot_commands = {} # Словарь с командами для бота
command_description = {} # Словарь с описанием комманд

with open('commands.json', 'r', encoding='utf-8') as file:
        bot_commands = json.load(file)
        file.close()   

for command in bot_commands: 
    command_description[command] = f'{bot_commands[command]["description"]}\n Использование: {settings["prefix"]}{bot_commands[command]["help"]}'



#======================================================
@bot.event
async def on_ready():
    print('i`m ready')

    #======= Заполнение словаря нулевыми значениями =======
    for guild in bot.guilds:        
        for member in guild.members:
            data[str(member.id)] = {
                'GAMES' : 0,
                'WINS' : 0
            }
    #======================================================



#====================== Команда !profile =========================
# Выводит информацию об участнике
@bot.command(help = command_description['profile'])
async def profile(ctx : commands.Context): 
    
    name = ctx.message.author # Получаем участника
    icon = name.avatar.url # Получаем аватарку участника
    
    # Помещаем все роли в строку
    author_roles = ''
    i = 1
    for role in name.roles:
        author_roles += f'{i}. {role} \n'
        i += 1

    # Создаём embed
    emb = discord.Embed(
        title = "Информация о профиле"
    )
    
    emb.set_thumbnail(url=icon)
    emb.add_field(name = 'Имя', value = name, inline=False)
    emb.add_field(name = 'Роли: ', value = author_roles, inline=False)
    
    await ctx.reply(embed=emb)
#==================================================================


#======================= Команда !game ============================
# С вероятностью 0.33 пользователь выигрывает и получает сообщение об успехе или проигрыше
@bot.command(help = command_description['game'])
async def game(ctx : commands.Context):

    data[str(ctx.message.author.id)]['GAMES'] += 1 # Увеличиваем количество сыгранных игр

    if random.randint(1,3) == 3:    # С вероятностью 1/3
        data[str(ctx.message.author.id)]['WINS'] += 1 # Увеличиваем количество побед
        await ctx.reply(':white_check_mark: Вы выиграли!') # Сообщаем о победе
    else:
        await ctx.reply(':x: Вы не выиграли!') # Иначе сообщаем о проигрыше
#===================================================================


#======================= Команда !stats ============================
# Выводит статистику о количестве сыгранных игр и побед для пользователя 
@bot.command(help = command_description['stats'])
async def stats(ctx):

    # Создаём embed
    emb = discord.Embed(
        title = f'Статистика игр {ctx.message.author}'
    )
    total_games = data[str(ctx.message.author.id)]['GAMES'] # Получаем количество всех игр
    total_wins = data[str(ctx.message.author.id)]['WINS']   # Получаем количество всех побед
    
    emb.add_field(name = 'Всего игр: ', value = total_games, inline=True)   # Создаём в embed поля с количеством игр и побед
    emb.add_field(name = 'Всего побед: ', value = total_wins, inline=True)

    await ctx.reply(embed = emb)    # Отвечаем на сообщение пользователя с embed со статистикой
#====================================================================

#======================= Команда !songsof ============================
# Reply with top 3 artist song
@bot.command(help = command_description['songsof'])
async def songsof(ctx, *, args):

    

    
    artist = genius.search_artist(args, max_songs=3)
    songs = artist.songs
    res = []
    for song in songs:
        res.append(song.title)
    await ctx.reply(str(res))   
#====================================================================
    
#======================= Команда !lyrics ============================
# Reply with lyrics of song by artist and title
@bot.command(help = command_description['lyrics'])
async def lyrics(ctx, *, args):
    splitted = args.split(",")
    print(splitted)
    artist_name = splitted[0]
    song_name = splitted[1]
    song = genius.search_song(song_name, artist_name)
    # Создаём embed
    emb = discord.Embed(
        title = f'{song.title} by {song.artist}'
    )
    emb.set_thumbnail(url=song.header_image_thumbnail_url)
    lyrics = song.lyrics

    # cut start garbage
    lyrics = lyrics[lyrics.find("["):]

    m = re.findall("\d+Embed", lyrics)
    lyrics = lyrics.replace(m[0], '')
    lyrics = lyrics.split("\n\n")
    print(lyrics)
    
    for para in lyrics:
        if len(para) > 1:
            emb.add_field(name="", value = para)   # Создаём в embed поля с количеством игр и побед
    
    await ctx.reply(embed = emb)   


@lyrics.error
async def lyrics_error(ctx, error):
    print(error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply('Отсутствуют аргументы!\nИспользование: ' + settings['prefix'] + bot_commands['lyrics']['help'])
    else:
        await ctx.reply('Что-то пошло не так :worried:')
#====================================================================

#======================= Команда !cover ============================
# Reply with album cover by artist and album title
@bot.command(help = command_description['cover'])
async def cover(ctx, *, args):
    if "," in args:
        splitted = args.split(",")
        print(splitted)
        artist_name = splitted[0]
        album_name = splitted[1]
        album = genius.search_album(album_name, artist_name)
    else:
        album = genius.search_album(name=args)
    # Создаём embed
    emb = discord.Embed(
        title = f'{album.name} by {album.artist.name}'
    )
    emb.set_image(url=album.cover_art_url)
    await ctx.reply(embed = emb)   


@cover.error
async def cover(ctx, error):
    print(error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply('Отсутствуют аргументы!\nИспользование: ' + settings['prefix'] + bot_commands['lyrics']['help'])
    elif isinstance(error, AttributeError):
        await ctx.reply('Не найдено! :face_with_monocle:')
    else:
        await ctx.reply('Что-то пошло не так :worried:')
#====================================================================



#======================= Команда !hello =============================
# Бот приветствует пользователя
@bot.command(help = command_description['hello'])
async def hello(ctx):
    author = ctx.message.author
    await ctx.send(f'Здарова, {author.mention}!')
#====================================================================


#============= Команда !translate, !tr, !trnslt, !перевод ==================
# Переводит текст с любого языка на русский, либо на английский, если изначальный текст был на русском
@bot.command(aliases = ['trnslt', 'перевод', 'tr'], help = command_description['translate'])
async def translate(ctx, *, text):

    message = await ctx.send(":mag: Перевод...")
    # Используем библиотеку googlesearch
     
    translator = Translator() # Используется библиотека googletrans

    detected = translator.detect(text) # Определяем исходный язык
    for lang in detected:
       print(lang.lang, lang.confidence)
    # Выбираем целевой язык
    if detected[0].lang == 'ru':
        dest = 'en'
    else:
        dest = 'ru'
    
    result = translator.translate(text, dest=dest) # Переводим, сохраняем результат

    await message.edit(content=result.text)
    # await ctx.reply(result.text) # Выводим результат

@translate.error
async def translate_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply('Отсутствуют аргументы!\nИспользование: ' + settings['prefix'] + bot_commands['translate']['help'])
#=============================================================================


#======================= Команда !gs, !google ============================
# Ищет запрос пользователя в Гугле, и возвращает 3 первых ссылки из выдачи
@bot.command(aliases = ['gs', 'google'], help = command_description['google_search'])
async def google_search(ctx, *, args):
    message = await ctx.send(":mag: Ищем...")
    # Используем библиотеку googlesearch
    print(args)
    res = search(args, num_results=3) # Ищем 3 страницы по запросу. search() возвращает генератор
    print(res)
    await message.edit(content="Найдено!")
    for _ in range(3):
        await ctx.send(res.__next__()) # Выводим поочереди все результаты. __next__() неоходим для итерации по генератору

@google_search.error
async def google_search_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply('Отсутствуют аргументы!\nИспользование: ' + settings['prefix'] + bot_commands['google_search']['help'])
#==========================================================================

 
#======================= Команда !repeat =================================
# Повторяет сообщение пользователя
@bot.command(help = command_description['repeat'])
async def repeat(ctx, *, args):
    await ctx.send(args)

@repeat.error
async def repeat_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply('Отсутствуют аргументы!\nИспользование: ' + settings['prefix'] + bot_commands['repeat']['help'])
#========================================================================


#============== Событие: участник присоединенился к серверу ==============
# Участнику должна выдаваться роль по умолчанию. 
# 
# НЕ ПРОВЕРЕНО
@bot.event
async def on_member_join(member): 
    role = discord.utils.get(member.guild.roles, name="Проветривающие")  
    await member.add_roles(role)
#=========================================================================


#======================= Команда !serverinfo =================================
# Выводит информацию о сервере
@bot.command(help = command_description['serverinfo'])
async def serverinfo(ctx):

    # Получаем основные даннные
    name = str(ctx.guild.name)
    owner = str(ctx.guild.owner)
    id = str(ctx.guild.id)
    memberCount = str(ctx.guild.member_count)
    icon = str(ctx.guild.icon.url)

    # Создаём embed для вывода
    embed = discord.Embed(
        title=name + ". Информация о сервере:",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Server ID", value=id, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)

    # Выводим embed
    await ctx.send(embed=embed)
#==========================================================================


#======================= Команда !rename =================================
# Переименовывает указанного участника
@bot.command(help = command_description['rename'])
@commands.has_permissions(manage_roles = True)
async def rename(ctx, member : discord.Member, *, new_nick):
    await member.edit(nick = new_nick)
    await ctx.send(f'Ник успешно изменён на {new_nick}')

@rename.error
async def rename_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply('Отсутствуют аргументы!\nИспользование: ' + settings['prefix'] + bot_commands['rename']['help'])
#========================================================================

bot.run(settings['token'])