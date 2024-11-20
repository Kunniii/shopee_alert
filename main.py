import os
from dotenv import load_dotenv
import json

import requests

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7,en-GB;q=0.6',
    'priority': 'u=1, i',
    'referer': 'https://spx.vn/track?SPXVN04842113686B',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'x-language': 'vi',
}

params = {
    'sls_tracking_number': 'SPXVN04842113686B|1731949825ed30c9e1c3e17f7ab6db22962369c4f217898f2fee26c9a87bead74d7513e26a',
}
from time import sleep

while True:
    old_data: dict = None

    if os.path.isfile('old.json'):
        try:
            with open('old.json', 'r+') as f:
                old_data = json.load(f)
        except:
            ...

    old_tracking_list: list = []
    if old_data != None:
        old_tracking_list = old_data['data']['tracking_list']

    response = requests.get('https://spx.vn/api/v2/fleet_order/tracking/search', params=params, headers=headers).json()
    print(response)
    tracking_list = response['data']['tracking_list']

    with open('old.json', 'w+') as f:
        json.dump(response, f)
        
    if len(tracking_list) > len(old_tracking_list):
        from dotenv import load_dotenv
        from Bot_API import TelegramBot
        import os
        load_dotenv()
        bot_token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        url = os.getenv("TRACK_URL")

        if not bot_token or not chat_id:
            print("Error: BOT_TOKEN or CHAT_ID not found in .env file.")
            exit(1)

        bot = TelegramBot(bot_token, chat_id)
        
        tracking_message = tracking_list[0]['message']

        message = f"New status on your shipment.\n{tracking_message}\nPlease check: {url}"
        response = bot.send_message(message)
        if response:
            print(response)
    sleep(10)

