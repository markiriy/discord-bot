import random
import discord
import json
import asyncio
from yandex_music import Client
from asyncio import sleep
import time
from pypresence import Presence

import re, urllib
from discord import FFmpegPCMAudio, PCMVolumeTransformer


from discord.ext import commands
from config import settings  # Импорт из файла config.py словаря конфигураций
import requests

intents = discord.Intents.default()  # Подключаем "Разрешения"
intents.message_content = True
prefix = settings['PREFIX']

client = commands.Bot(command_prefix=settings['PREFIX'], intents=intents)  # нужна для всех взаимодействий с ботом
client.remove_command('help')  # Удаляем изначальную команду "help"
yaclient = Client(settings['YANDEXTOKEN']).init()

type_to_name = {
    'track': 'трек',
    'artist': 'исполнитель',
    'album': 'альбом',
    'playlist': 'плейлист',
    'video': 'видео',
    'user': 'пользователь',
    'podcast': 'подкаст',
    'podcast_episode': 'эпизод подкаста',
}


# возвращение гифок по тегу
def get_gif(search_term):
    tenorkey = "" #тут ключ
    ckey = "my_test_app"
    lmt = 50
    response = requests.get("https://tenor.googleapis.com/v2/search?q=%s&key=%s&client_key=%s&limit=%s"
                            % (search_term, tenorkey, ckey,  lmt))
    if response.status_code == 200:
        gifs = json.loads(response.content)
        print(gifs)
    else:
        gifs = None
    randgif = random.choice(gifs['results'])
    return randgif['url']


#  инфа по названию трека и автору
def ya_musicinfo(query):
    search_result = yaclient.search(query)

    text = [f'Результаты по запросу "{query}":', '']

    best_result_text = ''
    if search_result.best:
        type_ = search_result.best.type
        best = search_result.best.result

        text.append(f'❗️Лучший результат: {type_to_name.get(type_)}')

        if type_ in ['track', 'podcast_episode']:
            artists = ''
            if best.artists:
                artists = ' - ' + ', '.join(artist.name for artist in best.artists)
            best_result_text = best.title + artists
        elif type_ == 'artist':
            best_result_text = best.name
        elif type_ in ['album', 'podcast']:
            best_result_text = best.title
        elif type_ == 'playlist':
            best_result_text = best.title
        elif type_ == 'video':
            best_result_text = f'{best.title} {best.text}'

        text.append(f'Содержимое лучшего результата: {best_result_text}\n')

    if search_result.artists:
        text.append(f'Исполнителей: {search_result.artists.total}')
    if search_result.albums:
        text.append(f'Альбомов: {search_result.albums.total}')
    if search_result.tracks:
        text.append(f'Треков: {search_result.tracks.total}')
    if search_result.playlists:
        text.append(f'Плейлистов: {search_result.playlists.total}')
    if search_result.videos:
        text.append(f'Видео: {search_result.videos.total}')

    text.append('')
    message = '\n'.join(text)
    return message


#  качать музон по запросу, играть его в канале
@client.event
async def playyandexmusic(message):
    search_result = yaclient.search(message)
    print(search_result)
    trackid = search_result.best.result.id
    albumid = search_result.best.result.albums[0].id
    print(trackid, albumid)
    track = yaclient.users_likes_tracks()[0].fetch_track()
    print(track)
    search_result.best.result.download(f'{search_result.best.result.artists[0].name} - {search_result.best.result.title}.mp3', codec='mp3',
                    bitrate_in_kbps=320)

    channel = client.get_channel(706522953613049910)
    voice = await channel.connect()
    voice.play(discord.FFmpegPCMAudio(f'{search_result.best.result.artists[0].name} - {search_result.best.result.title}.mp3'))
    while voice.is_playing():
        await sleep(1)
    await voice.disconnect()


#  потенциально транслирует музон
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}


@client.event
async def musicstreaming(message):
    search_result = yaclient.search(message)
    print(search_result)
    trackid = search_result.best.result.id
    albumid = search_result.best.result.albums[0].id
    print(trackid, albumid)
    html = urllib.request.urlopen(f"https://music.yandex.ru/album/{albumid}/track/{trackid}")
    video_ids = re.findall(r"album/(\S{7})/track/(\S{8})", html.read().decode())
    #  await message.send(f"https://music.yandex.ru/album/{albumid}/track/{trackid}")
    source = FFmpegPCMAudio(html.url)  # converts the audio source into a source discord can use
    channel = client.get_channel() #тут айди
    voice = await channel.connect()
    voice.play(source)


#  шлет серегу
@client.event
async def serega(member, prev, cur):
    if not prev.channel and cur.channel and member.id == : #тут айди
        print(f'{member} хуила')
        channel = client.get_channel() #тут айди
        voice = await channel.connect()
        voice.play(discord.FFmpegPCMAudio('seregashort.mp3'))
        await asyncio.sleep(6)
        await voice.disconnect()
    else:
        pass


@client.event  # Объявление события
async def on_ready():
    print(f"Logged on as {settings['NAME BOT']}")

    await client.change_presence(status=discord.Status.online, activity=discord.Streaming(name=f'ем за троих', url='https://www.youtube.com/watch?v=UYBc4J_e0Ow&list=LL&index=4'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(f'{prefix}hello'):
        await message.channel.send('new phone who dis')

    if message.content.startswith(f'{prefix}nohomo'):
        gif_url = get_gif(message.content.lower()[8:])  # Collects word after no homo
        await message.channel.send(gif_url)

    if message.content.startswith(f'{prefix}info'):
        input_query = message.content.lower()[6:]  # Collects word after info
        await message.channel.send(ya_musicinfo(input_query))

    if message.content.startswith(f'{prefix}play'):
        query = message.content.lower()[6:]  # Collects word after play
        await playyandexmusic(query)

    if message.content.startswith(f'{prefix}music'):
        search = message.content.lower()[7:]  # Collects word after play
        await musicstreaming(search)


client.run(settings['TOKEN'])  # Убираем в самый конец файла и больше не трогаем (нужен для запуска бота)

#показывает что слушает бот
RPC = Presence(client_id=settings['ID'])
RPC.connect()
while True:
    try:
        queues = yaclient.queues_list()
        last_queue = yaclient.queue(queues[0].id)
        last_track_id = last_queue.get_current_track()
        last_track = last_track_id.fetch_track()
        artists = ', '.join(last_track.artists_name())
        title = last_track.title
        track_link = f"https://music.yandex.ru/album/{last_track['albums'][0]['id']}/track/{last_track['id']}/"
        image_link = "https://" + last_track.cover_uri.replace("%%", "1000x1000")
        btns = [
            {
                "label": "Слушать Трек",
                "url": track_link
            }
        ]

        RPC.update(
            details="Слушает: " + title,
            state="Исполнитель: " + artists,
            large_image=image_link,
            small_image="Link for small image if you want",
            large_text="Your Text Here",
            small_text="Your Text Here",
            buttons=btns
        )
    except:
        RPC.update(
            details='Поддерживаются только треки из плейлистов 😥',
            state='Попробуй включить трек из плейлистов 🙃',
            large_image='https://c.tenor.com/ZuIbNWpIN5MAAAAC/rias-gremory-high-school-dxd.gif'
        )

    time.sleep(1)
