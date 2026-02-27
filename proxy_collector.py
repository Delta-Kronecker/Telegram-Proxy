import re
import asyncio
from telethon import TelegramClient, events
import os
import requests
from datetime import datetime

api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
phone_number = os.environ.get('PHONE_NUMBER')
github_token = os.environ.get('GH_TOKEN')
telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
group_usernames = ['@chatnakonn', '@v2ray_proxyz', '@VasLshoGap', '@chat_naakon', '@FlexEtesal', '@chat_nakonnn', '@letsproxys', '@Alpha_V2ray_Group', '@VpnTvGp', '@VPN_iransaz', '@chat_nakoni']
NUM_LAST_MESSAGES = 1000
PROXY_FILE = 'proxies.txt'

SESSION_URLS = [
    'https://github.com/S00SIS/tel/raw/refs/heads/main/session.session',
    'https://raw.githubusercontent.com/S00SIS/tel/main/session.session'
]
SESSION_FILE = 'session.session'

class ProxyCollector:
    def __init__(self):
        self.client = None
        self.proxies = self.load_proxies()
        self.group_counts = {}
        self.new_proxies_count = 0

    def download_session(self):
        if os.path.exists(SESSION_FILE):
            return True
        if not github_token:
            return False
        
        headers = {'Authorization': f'token {github_token}'}
        
        for url in SESSION_URLS:
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    with open(SESSION_FILE, 'wb') as f:
                        f.write(response.content)
                    return True
            except Exception:
                continue
        return False

    def load_proxies(self):
        proxies = set()
        if os.path.exists(PROXY_FILE):
            with open(PROXY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        proxies.add(line)
        return proxies

    def add_proxy(self, proxy_url, group_name):
        if proxy_url in self.proxies:
            return False
        with open(PROXY_FILE, 'a', encoding='utf-8') as f:
            if os.path.getsize(PROXY_FILE) > 0:
                f.write('\n')
            f.write(proxy_url + '\n')
        self.proxies.add(proxy_url)
        self.group_counts[group_name] = self.group_counts.get(group_name, 0) + 1
        self.new_proxies_count += 1
        return True

    def extract_proxy_links(self, text):
        if not text:
            return []
        pattern = r'https?://t\.me/proxy\?[^\s<>"\'(){}|\\^`\[\]]+'
        found = re.findall(pattern, text, re.IGNORECASE)
        unique = []
        for link in found:
            link = link.rstrip('.,;:!?)]}')
            unique.append(link)
        return unique

    async def fetch_recent_messages(self, limit):
        for group in group_usernames:
            try:
                chat = await self.client.get_entity(group)
                chat_title = chat.title if hasattr(chat, 'title') else chat.username
                messages = await self.client.get_messages(chat, limit=limit)
                for msg in messages:
                    if msg.text:
                        links = self.extract_proxy_links(msg.text)
                        for link in links:
                            self.add_proxy(link, chat_title)
            except Exception:
                continue

    async def handle_new_message(self, event):
        message = event.message
        chat = await event.get_chat()
        chat_title = chat.title if hasattr(chat, 'title') else chat.username
        new_links = self.extract_proxy_links(message.text)
        if new_links:
            for link in new_links:
                self.add_proxy(link, chat_title)

    async def send_to_telegram(self):
        if not telegram_bot_token or not telegram_chat_id:
            return
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        total_proxies = len(self.proxies)
        
        caption = f"**Telegram Proxy Collector Update {current_date}**\n\n"
        caption += f"✅ **New Proxies Found: {self.new_proxies_count}**\n"
        caption += f"📊 **Statistics:**\n"
        caption += f"• Total Proxies Collected: {total_proxies}\n"
        caption += f"• Groups Monitored: {len(group_usernames)}"
        
        try:
            with open(PROXY_FILE, 'rb') as f:
                url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
                files = {'document': f}
                data = {'chat_id': telegram_chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
                response = requests.post(url, data=data, files=files, timeout=60)
                if response.status_code == 200:
                    print("File with caption sent to Telegram successfully.")
                else:
                    print(f"Failed to send: {response.status_code}")
        except Exception as e:
            print(f"Error sending to Telegram: {e}")

    async def start(self):
        if not self.download_session():
            return

        self.client = TelegramClient(SESSION_FILE, int(api_id), api_hash)

        @self.client.on(events.NewMessage(chats=group_usernames))
        async def message_handler(event):
            await self.handle_new_message(event)

        await self.client.start(phone=phone_number)
        await self.fetch_recent_messages(NUM_LAST_MESSAGES)
        await self.send_to_telegram()
        await asyncio.sleep(2)
        await self.client.disconnect()

async def main():
    collector = ProxyCollector()
    try:
        await collector.start()
    except Exception:
        pass

if __name__ == '__main__':
    asyncio.run(main())
