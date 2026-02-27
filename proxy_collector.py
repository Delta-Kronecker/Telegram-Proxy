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
group_usernames = ['@chatnakonn', '@v2ray_proxyz', '@VasLshoGap', '@chat_naakon', '@FlexEtesal', '@chat_nakonnn', '@letsproxys', '@Alpha_V2ray_Group', '@VpnTvGp', '@VPN_iransaz', '@chat_nakoni']
NUM_LAST_MESSAGES = 20
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

    def download_session(self):
        if os.path.exists(SESSION_FILE):
            print('✅ Session file already exists.')
            return True
        if not github_token:
            print('❌ No GitHub token provided, cannot download session.')
            return False
        
        headers = {'Authorization': f'token {github_token}'}
        
        for url in SESSION_URLS:
            print(f'Trying to download from: {url}')
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    with open(SESSION_FILE, 'wb') as f:
                        f.write(response.content)
                    print(f'✅ Session file downloaded successfully from {url}')
                    return True
                else:
                    print(f'❌ Failed from {url}. Status code: {response.status_code}')
            except Exception as e:
                print(f'❌ Error from {url}: {e}')
        
        print('❌ All download attempts failed.')
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
            print(f'\n📥 Fetching last {limit} messages from {group}...')
            try:
                chat = await self.client.get_entity(group)
                chat_title = chat.title if hasattr(chat, 'title') else chat.username
                messages = await self.client.get_messages(chat, limit=limit)
                new_count = 0
                for msg in messages:
                    if msg.text:
                        links = self.extract_proxy_links(msg.text)
                        for link in links:
                            if self.add_proxy(link, chat_title):
                                new_count += 1
                if new_count:
                    print(f'✅ Found {new_count} new proxies from {chat_title}.')
                else:
                    print(f'ℹ️ No new proxies found from {chat_title}.')
            except Exception as e:
                print(f'❌ Error accessing group {group}: {e}')

    async def handle_new_message(self, event):
        message = event.message
        chat = await event.get_chat()
        chat_title = chat.title if hasattr(chat, 'title') else chat.username
        new_links = self.extract_proxy_links(message.text)
        if new_links:
            for link in new_links:
                self.add_proxy(link, chat_title)

    async def start(self):
        if not self.download_session():
            print('❌ Cannot proceed without session file.')
            return

        self.client = TelegramClient(SESSION_FILE, int(api_id), api_hash)

        @self.client.on(events.NewMessage(chats=group_usernames))
        async def message_handler(event):
            await self.handle_new_message(event)

        print('🔌 Connecting to Telegram...')
        await self.client.start(phone=phone_number)
        print('✅ Connected!')

        await self.fetch_recent_messages(NUM_LAST_MESSAGES)
        await asyncio.sleep(2)
        print('\n✅ Program completed.')
        self.print_summary()
        await self.client.disconnect()

    def print_summary(self):
        print('\n' + '='*50)
        print(f'📊 Summary of collected proxies: {len(self.proxies)}')
        print('='*50)
        if self.group_counts:
            print('\n📈 Proxies found per group:')
            for group, count in self.group_counts.items():
                print(f'  • {group}: {count}')
        print(f'\n💾 Proxies saved in file {PROXY_FILE}.')

async def main():
    collector = ProxyCollector()
    try:
        await collector.start()
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
