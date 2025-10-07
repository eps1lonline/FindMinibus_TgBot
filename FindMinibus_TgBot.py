import ast
import calendar
import requests
import time as t
import asyncio

from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler



CITY = {
    'Минск' : 'c625144',
    'Дятлово' : 'c628658'
}
TG_BOT_TOKEN = '8418015159:AAFkDdde3QsWinhSg6Sa866C5onf_wAYSxU' # @botfather
TG_MY_URL = '762753264' # @userinfobot

scheduler = AsyncIOScheduler(timezon='Europe/Minsk')
bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()



def initialized():
    global year, month, day, time, start_place, finish_place, passengers

    day = datetime.now().date()
    next_day = day + timedelta(days=1)

    month = datetime.now().month
    if month == 12:
        next_month = 1
    else:
        next_month = month + 1

    year = datetime.now().year

    base_settings = [str(year), [str(month).zfill(2), str(next_month).zfill(2)], [str(day.day).zfill(2), str(next_day.day).zfill(2)], ['19:50:00', '20:50:00'], 'Минск', 'Дятлово', '1']

    year = base_settings[0]
    month = base_settings[1]
    day = base_settings[2]
    time = base_settings[3]
    start_place = base_settings[4]
    finish_place = base_settings[5]
    passengers = base_settings[6]



@dp.message(Command('set_settings'))
async def set_settings(command: CommandObject):
    global year, month, day, time, start_place, finish_place, passengers

    try:
        personal_settings = ast.literal_eval(command.args) 

        year = personal_settings[0]
        month = personal_settings[1]
        day = personal_settings[2]
        time = personal_settings[3]
        start_place = personal_settings[4]
        finish_place = personal_settings[5]
        passengers = personal_settings[6]
    except Exception as e:
        await bot.send_message(TG_MY_URL, f'❌ *Ошибка:* `{str(e)}` \n🔍 *Проверьте корректность сформированного вами запроса\\!*', parse_mode='MarkdownV2') 
    else:
        await bot.send_message(TG_MY_URL, '✅ *Новые настройки были применены\\!*', parse_mode='MarkdownV2') 



@dp.message(Command('get_settings'))
async def get_settings(text: Message):
    try:
        text = f'\
⚙️ _*Настройки:*_ \n\n\
📆 *Год:* `{year}` \n\
🌜 *Месяц:* `{month}` \n\
☀️ *День:* `{day}` \n\
⏰ *Время:* `{time}` \n\
✈️ *Отправление:* `{start_place}` \n\
🏠 *Прибытие:* `{finish_place}` \n\
🙂 *Пассажиры:* `{passengers}` \n'
        
        await bot.send_message(TG_MY_URL, text, parse_mode='MarkdownV2')
    except Exception as e:
        await bot.send_message(TG_MY_URL, f'❌ *Ошибка:* `{str(e)}`', parse_mode='MarkdownV2')



@dp.message(Command('search'))
async def search(text: Message):
    try:
        if not scheduler.running:
            scheduler.add_job(search_main, 'interval', minutes = 1)
            scheduler.start()
            await bot.send_message(TG_MY_URL, '✅ *Мониторинг включен\\!* \n📌 *Сайт будет пинговаться каждые* `5\\-ть минут`*\\!*', parse_mode='MarkdownV2')
        else:
            await bot.send_message(TG_MY_URL, '⚠️ *Мониторинг уже запущен\\!*', parse_mode='MarkdownV2')
    except Exception as e:
        await bot.send_message(TG_MY_URL, f'❌ *Ошибка:* `{str(e)}`', parse_mode='MarkdownV2')



async def search_main():
    try:
        await bot.send_message(TG_MY_URL, '⏳ Запрос\\.\\.\\.', parse_mode='MarkdownV2')

        find = False
        text = f'🔍 _*Результаты поиска:*_ \n\n'
        for m in month:
            for d in day:
                t.sleep(3)
                date = str(year) + '-' + str(m).zfill(2) + '-' + str(d).zfill(2)
                request = 'https://atlasbus.by/api/search?from_id=' + CITY[start_place] + '&to_id=' + CITY[finish_place] + '&calendar_width=' + str(calendar.monthrange(int(year), int(m))[1]) + '&date=' + date + '&passengers=' + passengers
                answer = requests.get(request, verify=False).json()

                for a in answer['rides']:
                    if (a['freeSeats'] - int(passengers) >= 0 and a['departure'][11:] in time):
                        find = True
                        text += f'\
⏰ *Время:* `{a['departure'][11:]} - {a['arrival'][11:]}` \n\
📆 *Дата:* `{date}` \n\
✈️ *Отправление:* ` {start_place} ({' → '.join(j['desc'] for j in a['pickupStops'])})` \n\
🏠 *Прибытие:* `{finish_place} ({' → '.join(j['desc'] for j in a['dischargeStops'])})` \n\
💰 *Цена:* `{a['price']} {a['currency']}` \n\
🚍 *Автобус:* `{a['bus']['mark']} / {a['bus']['model']} / {a['bus']['color']['name']}` \n\
📏 *Расстояние:* `{a['distance']} km` \n\
☎️ *Телефон:* `{a['carrier_phones']}` \n\
👩‍👦 *Перевозчик:* `{a['legal']['name']}` \n\
🪑 *Мест:* `{a['freeSeats']}` \n'

        if find:
            await bot.send_message(TG_MY_URL, text, parse_mode='MarkdownV2') 
            scheduler.remove_all_jobs()
            scheduler.shutdown(wait=False)
            await bot.send_message(TG_MY_URL, '⛔️ *Мониторинг остановлен\\!*', parse_mode='MarkdownV2') 
        else:
            await bot.send_message(TG_MY_URL, f'{text}🙅🏻 *Свободных мест нет\\!*', parse_mode='MarkdownV2') 
    except Exception as e:
        await bot.send_message(TG_MY_URL, f'❌ *Ошибка:* `{str(e)}`', parse_mode='MarkdownV2')



@dp.message(Command('info'))
async def info(text: Message):
    try:
        curr_year = datetime.now().year
        curr_month = datetime.now().month
        curr_day = datetime.now().day

        curr_date = str(curr_year) + '-' + str(curr_month).zfill(2) + '-' + str(curr_day).zfill(2)
        curr_request = 'https://atlasbus.by/api/search?from_id=' + CITY[start_place] + '&to_id=' + CITY[finish_place] + '&calendar_width=' + str(calendar.monthrange(int(curr_year), int(curr_month))[1]) + '&date=' + curr_date + '&passengers=' + passengers
        curr_answer = requests.get(curr_request, verify=False).json()

        await bot.send_message(TG_MY_URL, '☝️ *Пожалуйста, подождите\\! \n⏳ Процесс может занять до* `30 секунд`\\ \n🙏 *Спасибо за ваше терпение\\!*', parse_mode='MarkdownV2')

        text = f'📊 _*Информация:*_ \n\n'
        for a_c in curr_answer['calendar']:
            if a_c['rideCount'] != 0:
                text += f'\
📆 *Дата:* `{a_c['date']}` \n\
🚍 *Количество поездок:* `{a_c['rideCount']}` \n'

                new_year = a_c['date'][:4]
                new_month = a_c['date'][5:7]
                new_day = a_c['date'][8:10]

                t.sleep(3)
                new_date = str(new_year) + '-' + str(new_month).zfill(2) + '-' + str(new_day).zfill(2)
                new_request = 'https://atlasbus.by/api/search?from_id=' + CITY[start_place] + '&to_id=' + CITY[finish_place] + '&calendar_width=' + str(calendar.monthrange(int(new_year), int(new_month))[1]) + '&date=' + new_date + '&passengers=' + passengers
                new_answer = requests.get(new_request, verify=False).json()

                for a_r in new_answer['rides']:
                    text += f'• `{a_r['departure'][11:]} \\- {a_r['freeSeats']}` \n'
                text += f'\n'

        await bot.send_message(TG_MY_URL, text, parse_mode='MarkdownV2') 
    except Exception as e:
        await bot.send_message(TG_MY_URL, f'❌ *Ошибка:* `{str(e)}`', parse_mode='MarkdownV2')



@dp.message(Command('start'))
async def start(text: Message):
    try:
        text = f"\n\
📟 _*Команды:*_ \n\n\
**/start** *\\- список комманд* ℹ️ \n\n\
**/search** *\\- запустить мониторинг* 🚀 \n\n\
`/set\\_settings` *\\- задать настройки для поиска* ⚙️ \n\n\
• *Пример запроса:* \n`/set\\_settings [{year}, {month}, {day}, ['19:50:00', '20:50:00'], 'Минск', 'Дятлово', '1']` \n\n\
• *Формат ввода для аргумента:* \n`/set\\_settings ['Год', ['Месяц_1', 'Месяц_2', ...], ['День_1', 'День_2', ...], ['Время_1', 'Время_2', ...], 'Место_Отправления', 'Место_Прибытия', 'Количество_Пассажиров']` \n\n\
**/get\\_settings** *\\- посмотреть текущие настройки для поиска* 🔍 \n\n\
**/info** *\\- посмотреть все будущие рейсы* 📋 \n\n\
**/stop** *\\- остановить мониторинг* ⛔️ \n\n"
    
        await bot.send_message(TG_MY_URL, text, parse_mode='MarkdownV2') 
    except Exception as e:
        await bot.send_message(TG_MY_URL, f'❌ *Ошибка:* `{str(e)}`', parse_mode='MarkdownV2')



@dp.message(Command('stop'))
async def stop(message: Message):
    try:
        if scheduler.running:
            scheduler.remove_all_jobs()
            scheduler.shutdown(wait=False)
            await bot.send_message(TG_MY_URL, '⛔️ *Мониторинг остановлен\\!*', parse_mode='MarkdownV2') 
        else:
            await bot.send_message(TG_MY_URL, '⚠️ *Мониторинг уже был выключен\\!*', parse_mode='MarkdownV2')
    except Exception as e:
        await bot.send_message(TG_MY_URL, f'❌ *Ошибка:* `{str(e)}`', parse_mode='MarkdownV2')



async def main():
    await dp.start_polling(bot)
    


if __name__ == "__main__":
    initialized()
    asyncio.run(main())