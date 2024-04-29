import asyncio
import telegram

from parameters import TOKEN

"""
Запустив этот скрипт вы сможете получить идентификатор чата
"""


async def main():
    bot = telegram.Bot(TOKEN)
    async with bot:
        print((await bot.get_updates())[0])  # Просмотр полученных ботом сообщений и получение идентификатора чата

if __name__ == '__main__':
    asyncio.run(main())
