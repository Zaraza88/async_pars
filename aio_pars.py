import aiofiles
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from aiocsv import AsyncWriter


HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 6.1; rv:6.0) Gecko/20100101 Firefox/19.0"
    }
URL = 'https://belbazar24.by/men/dress/'


async def get_block():
    """Получаем конкретный блок с каждой страницы"""

    async with aiohttp.ClientSession() as session:
        response = await session.get(url=URL, headers=HEADERS)
        soup = BeautifulSoup(await response.text(), 'lxml')

        pages = int(soup.find('div', class_='navigation_content').find_all('a')[-1].text)

        tasks = []

        for page in range(1, pages + 1):
            task = asyncio.create_task(get_block_content(session, page))
            tasks.append(task)

        await asyncio.gather(*tasks)


async def get_block_content(session, page):
    """Собираем данные с каждого блока на каждой странице"""
    
    url = f'{URL}?page={page}'

    async with session.get(url=url, headers=HEADERS) as response:
        soup = BeautifulSoup(await response.text(), 'lxml')

        block = soup.find_all('div', class_='cat_list_item')

        data = [] 

        for item in block:

            try: 
                sign = item.find('a', class_='product_znak new').text
            except AttributeError:
                sign = 'Пусто'
            try: 
                discount = item.find('a', class_='product_znak sale second').text
            except AttributeError:
                discount = 'Нет скидки'
            title = item.find('div', class_='product_item_brand').find('a').text
            price = f"{item.find('span', class_='price').text} BYN"

            data.append({
                'title': title,
                'price': price,
                'sign': sign,
                'discount': discount
            })
        
        await save(page, data)
        print(f"[INFO] Обработал страницу {page}")


async def save(page, data):
    """Сохраняем данные в csv"""

    async with aiofiles.open(f"labirint_{page}_async.csv", "w") as file:
        writer = AsyncWriter(file, delimiter=' ')
        await writer.writerow(
            ("Название", "Цена BYN", "Знак", "Скидка")
            )

        for item in data:
            await writer.writerow(
                (
                    item["title"], 
                    item["price"], 
                    item['sign'], 
                    item['discount']
                )
                )


if __name__ == '__main__':
    asyncio.run(get_block())

