import asyncio
import json
import random
from eth_account import Account
from eth_account.messages import encode_defunct
import requests
from web3 import Web3
import aiohttp
import logging
from typing import List, Dict
import os
import ssl
import re
from colorama import init, Fore, Style
import time
import sys

# Set console encoding to UTF-8 for Windows
if sys.platform.startswith('win'):
    import subprocess
    subprocess.run(['chcp', '65001'], shell=True)
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize colorama
init(convert=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),  # Log file with UTF-8 encoding
        logging.StreamHandler()  # Console output
    ]
)

# Custom console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(formatter)

# Create logger
logger = logging.getLogger('console')
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

def print_logo():
    logo = """
    ╔════════════════════════════════════════╗
    ║             GATA REGISTER BOT          ║
    ╚════════════════════════════════════════╝
    """
    print(Fore.CYAN + logo + Style.RESET_ALL)

def get_menu_choice():
    print(Fore.YELLOW + "\nSelect Operation:" + Style.RESET_ALL)
    print("1. Start Registration")
    print("2. Exit")
    while True:
        try:
            choice = input("\nEnter choice (1-2): ")
            if choice in ['1', '2']:
                return choice
        except:
            pass
        print(Fore.RED + "Invalid choice, please try again" + Style.RESET_ALL)

class InviteBot:
    def __init__(self):
        self.invite_code = ""
        self.proxies = []
        self.w3 = Web3()
        self.base_url = "https://earn.aggregata.xyz/api"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json",
            "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Google Chrome\";v=\"132\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "origin": "https://app.gata.xyz",
            "referer": "https://app.gata.xyz/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "accept-encoding": "gzip, deflate, br, zstd"
        }
        self.success_count = 0
        self.total_count = 0
        
    def load_proxies(self, proxy_file: str) -> None:
        """Load proxy list from file"""
        try:
            with open(proxy_file, 'r', encoding='utf-8') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            logger.info(Fore.GREEN + f"✓ Successfully loaded {len(self.proxies)} proxies" + Style.RESET_ALL)
        except Exception as e:
            logger.error(Fore.RED + f"✗ Failed to load proxy file: {str(e)}" + Style.RESET_ALL)
            raise

    def create_wallet(self) -> tuple:
        """Create new Ethereum wallet"""
        account = Account.create()
        private_key = account.key.hex()
        address = account.address
        self.total_count += 1
        logger.info(Fore.CYAN + f"⚡ Creating wallet [{self.total_count}]: {address}" + Style.RESET_ALL)
        return private_key, address

    def format_proxy(self, proxy: str) -> Dict:
        """Format proxy string to configuration dictionary"""
        try:
            if '@' in proxy:
                auth, host = proxy.split('@')
                auth = auth.replace('http://', '')
                username, password = auth.split(':')
                return {
                    'http': proxy,
                    'https': proxy.replace('http://', 'https://'),
                    'proxy_auth': aiohttp.BasicAuth(username, password)
                }
            return {
                'http': proxy,
                'https': proxy.replace('http://', 'https://')
            }
        except Exception as e:
            logger.error(Fore.RED + f"✗ Failed to format proxy: {proxy}, error: {str(e)}" + Style.RESET_ALL)
            return None

    def extract_nonce(self, auth_nonce: str) -> str:
        """Extract actual nonce value from auth_nonce string"""
        try:
            match = re.search(r'Nonce:\n([^\n]+)', auth_nonce)
            if match:
                return match.group(1)
            return ''
        except Exception as e:
            logger.error(Fore.RED + f"✗ Failed to extract nonce: {str(e)}" + Style.RESET_ALL)
            return ''

    async def get_signature_nonce(self, session: aiohttp.ClientSession, address: str, proxy_config: Dict, max_retries: int = 3) -> str:
        """Get signature nonce with retry mechanism"""
        for retry in range(max_retries):
            try:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                logger.info(Fore.YELLOW + f"↻ Getting nonce (attempt {retry + 1}/{max_retries}): {address}" + Style.RESET_ALL)
                async with session.post(
                    f"{self.base_url}/signature_nonce",
                    json={"address": address},
                    headers=self.headers,
                    proxy=proxy_config['http'],
                    proxy_auth=proxy_config.get('proxy_auth'),
                    ssl=ssl_context,
                    timeout=30
                ) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        result = json.loads(response_text)
                        if result.get('code') == 0:
                            auth_nonce = result.get('auth_nonce', '')
                            nonce = self.extract_nonce(auth_nonce)
                            if nonce:
                                logger.info(Fore.GREEN + f"✓ Got nonce successfully: {address}, nonce: {nonce}" + Style.RESET_ALL)
                                return auth_nonce
                            else:
                                logger.error(Fore.RED + f"✗ Unable to extract nonce from response: {auth_nonce}" + Style.RESET_ALL)
                        else:
                            logger.error(Fore.RED + f"✗ Registration failed, error code: {result.get('code')}" + Style.RESET_ALL)
                    else:
                        logger.error(Fore.RED + f"✗ Registration failed: {address}, status code: {response.status}, response: {response_text}" + Style.RESET_ALL)
                    
                    if retry < max_retries - 1:
                        delay = random.uniform(2, 4)
                        logger.info(Fore.YELLOW + f"⏳ Waiting {delay:.1f} seconds before retrying..." + Style.RESET_ALL)
                        await asyncio.sleep(delay)
            except Exception as e:
                logger.error(Fore.RED + f"✗ Error getting nonce: {address}, error: {str(e)}" + Style.RESET_ALL)
                if retry < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 4))
        
        return ''

    def sign_message(self, private_key: str, message: str) -> str:
        """Sign message with private key"""
        try:
            message_hash = encode_defunct(text=message)
            signed_message = Account.sign_message(message_hash, private_key)
            signature = signed_message.signature.hex()
            logger.info(Fore.GREEN + f"✓ Signed message successfully: {signature[:10]}..." + Style.RESET_ALL)
            return signature
        except Exception as e:
            logger.error(Fore.RED + f"✗ Failed to sign message: {str(e)}" + Style.RESET_ALL)
            return ''

    async def authorize(self, session: aiohttp.ClientSession, address: str, signature: str, proxy_config: Dict, max_retries: int = 3) -> bool:
        """Authorize registration with retry mechanism"""
        for retry in range(max_retries):
            try:
                data = {
                    "public_address": address,
                    "signature_code": signature,
                    "invite_code": self.invite_code
                }
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                logger.info(Fore.YELLOW + f"↻ Starting registration (attempt {retry + 1}/{max_retries}): {address}" + Style.RESET_ALL)
                async with session.post(
                    f"{self.base_url}/authorize",
                    json=data,
                    headers=self.headers,
                    proxy=proxy_config['http'],
                    proxy_auth=proxy_config.get('proxy_auth'),
                    ssl=ssl_context,
                    timeout=30
                ) as response:
                    response_text = await response.text()
                    logger.info(Fore.GREEN + f"✓ Registration response: {response_text}" + Style.RESET_ALL)
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        if result.get('code') == 0:
                            self.success_count += 1
                            logger.info(Fore.GREEN + f"✓ Registration successful [{self.success_count}/{self.total_count}]: {address}" + Style.RESET_ALL)
                            # Save token and invite code
                            with open('successful_accounts.txt', 'a', encoding='utf-8') as f:
                                f.write(f"{address},{result.get('token', '')},{result.get('invite_code', '')}\n")
                            return True
                        else:
                            logger.error(Fore.RED + f"✗ Registration failed: {address}, error message: {result.get('msg')}" + Style.RESET_ALL)
                    else:
                        logger.error(Fore.RED + f"✗ Registration failed: {address}, status code: {response.status}, response: {response_text}" + Style.RESET_ALL)
                    
                    if retry < max_retries - 1:
                        delay = random.uniform(3, 60)
                        logger.info(Fore.YELLOW + f"⏳ Waiting {delay:.1f} seconds before retrying..." + Style.RESET_ALL)
                        await asyncio.sleep(delay)
            except Exception as e:
                logger.error(Fore.RED + f"✗ Registration process failed: {address}, error: {str(e)}" + Style.RESET_ALL)
                if retry < max_retries - 1:
                    await asyncio.sleep(random.uniform(3, 60))
        
        return False

    async def process_registration(self, proxy: str):
        """Process single registration"""
        try:
            private_key, address = self.create_wallet()
            proxy_config = self.format_proxy(proxy)
            if not proxy_config:
                return
            
            logger.info(Fore.YELLOW + f"⚡ Starting registration: {address}, proxy: {proxy}" + Style.RESET_ALL)
            connector = aiohttp.TCPConnector(ssl=False, force_close=True)
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                # 1. Get nonce
                auth_nonce = await self.get_signature_nonce(session, address, proxy_config)
                if not auth_nonce:
                    return
                
                # 2. Sign complete message
                signature = self.sign_message(private_key, auth_nonce)
                if not signature:
                    return
                
                # 3. Authorize registration
                success = await self.authorize(session, address, signature, proxy_config)
                if success:
                    with open('wallets.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{address},{private_key}\n")
        except Exception as e:
            logger.error(Fore.RED + f"✗ Registration process failed: {str(e)}" + Style.RESET_ALL)

    async def start(self, concurrent_tasks: int = 2):
        """Start registration bot"""
        logger.info(Fore.CYAN + f"⚡ Starting bot (concurrent tasks: {concurrent_tasks})" + Style.RESET_ALL)
        while self.proxies:
            try:
                tasks = []
                for _ in range(min(concurrent_tasks, len(self.proxies))):
                    if not self.proxies:
                        break
                    proxy = self.proxies.pop(0)
                    tasks.append(self.process_registration(proxy))
                if tasks:
                    await asyncio.gather(*tasks)
                    delay = random.uniform(3, 60)
                    logger.info(Fore.YELLOW + f"⏳ Waiting {delay:.1f} seconds..." + Style.RESET_ALL)
                    await asyncio.sleep(delay)
            except Exception as e:
                logger.error(Fore.RED + f"✗ Task execution failed: {str(e)}" + Style.RESET_ALL)
                await asyncio.sleep(5)
        logger.info(Fore.GREEN + f"\n✓ Task completed! Success: {self.success_count}/{self.total_count}" + Style.RESET_ALL)

def main():
    try:
        print_logo()
        bot = InviteBot()
        
        while True:
            choice = get_menu_choice()
            
            if choice == '1':
                invite_code = input("\nEnter invite code (press Enter to cancel): ").strip()
                if not invite_code:
                    continue
                    
                bot.invite_code = invite_code
                print(Fore.GREEN + f"\n✓ Invite code set: {invite_code}" + Style.RESET_ALL)
                bot.load_proxies('proxies.txt')
                asyncio.run(bot.start())
                
            elif choice == '2':
                print(Fore.YELLOW + "\nThank you for using! Goodbye!" + Style.RESET_ALL)
                break
                
    except Exception as e:
        logger.error(Fore.RED + f"✗ Program error: {str(e)}" + Style.RESET_ALL)

if __name__ == "__main__":
    main() 