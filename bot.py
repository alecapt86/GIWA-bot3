from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from datetime import datetime
from colorama import *
import asyncio, random, re, os, pytz, getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from decimal import Decimal, getcontext

# ==== file logging helpers ====
ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")  # убрать цвета для файла


def _sanitize_ansi(s: str) -> str:
    try:
        return ANSI_ESCAPE_RE.sub("", s)
    except Exception:
        return s

import sys  # добавили только sys

# ВАЖНО: ставим политику сразу после импортов (до первого создания event loop)
if sys.platform.startswith('win'):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# высокая точность для расчётов ETH -> wei
getcontext().prec = 50

wib = pytz.timezone('Asia/Jakarta')

class Giwa:
    def __init__(self) -> None:
        self.encrypted_file = "accounts_encrypted.txt"
        self.L1_NETWORK = {
            "name": "Sepolia ETH",
            "rpc_url": "https://ethereum-sepolia-rpc.publicnode.com",
            "explorer": "https://sepolia.etherscan.io/tx/",
            "contract": "0x956962C34687A954e611A83619ABaA37Ce6bC78A",
            "abi": [
                {
                    "type": "function",
                    "name": "depositTransaction",
                    "stateMutability": "payable",
                    "inputs": [
                        { "internalType": "address", "name": "_to", "type": "address" },
                        { "internalType": "uint256", "name": "_value", "type": "uint256" },
                        { "internalType": "uint64", "name": "_gasLimit", "type": "uint64" },
                        { "internalType": "bool", "name": "_isCreation", "type": "bool" },
                        { "internalType": "bytes", "name": "_data", "type": "bytes" }
                    ],
                    "outputs": []
                }
            ]
        }
        self.L2_NETWORK = {
            "name": "Giwa Sepolia",
            "rpc_url": "https://sepolia-rpc.giwa.io",
            "explorer": "https://sepolia-explorer.giwa.io/tx/",
            "contract": "0x4200000000000000000000000000000000000016",
            "abi": [
                {
                    "type": "function",
                    "name": "initiateWithdrawal",
                    "stateMutability": "payable",
                    "inputs": [
                        { "internalType": "address", "name": "_target", "type": "address" },
                        { "internalType": "uint256", "name": "_gasLimit", "type": "uint256" },
                        { "internalType": "bytes", "name": "_data", "type": "bytes" }
                    ],
                    "outputs": []
                }
            ]
        }
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

        # file log
        self.log_file_path = "logs.txt"

        # --- настройки бриджа ---
        # count: можно фиксированное (bridge_count) или диапазон (bridge_count_min/max)
        self.bridge_count = 0
        self.bridge_count_min = None
        self.bridge_count_max = None

        # amount: диапазон с точностью (определяется числом знаков после точки)
        self.amount_min: Decimal | None = None
        self.amount_max: Decimal | None = None
        self.amount_scale: int | None = None  # 10**decimals

        # задержки между транзакциями
        self.min_delay = 0
        self.max_delay = 0

    # ------------------- Шифрование/аккаунты -------------------
    def generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def decrypt_accounts(self, password: str):
        try:
            if not os.path.exists(self.encrypted_file):
                self.log(f"{Fore.RED + Style.BRIGHT}Error: encrypted file {self.encrypted_file} not found!{Style.RESET_ALL}")
                return None

            with open(self.encrypted_file, "rb") as f:
                salt = f.read(16)
                count_bytes = f.read(4)
                count = int.from_bytes(count_bytes, 'big')

                key = self.generate_key_from_password(password, salt)
                fernet = Fernet(key)

                accounts = []
                for _ in range(count):
                    length_bytes = f.read(4)
                    length = int.from_bytes(length_bytes, 'big')
                    encrypted_account = f.read(length)
                    decrypted_account = fernet.decrypt(encrypted_account).decode()
                    accounts.append(decrypted_account)

                return accounts

        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Decryption failed: {e}{Style.RESET_ALL}")
            return None

    def get_password(self):
        while True:
            password = getpass.getpass(f"{Fore.YELLOW + Style.BRIGHT}Enter decryption password: {Style.RESET_ALL}")
            if password:
                return password
            print(f"{Fore.RED + Style.BRIGHT}Password cannot be empty!{Style.RESET_ALL}")

    # ------------------- Утилиты/лог -------------------
    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message: str, file_extra: str | None = None):
        """
        Печатает цветной лог в консоль и пишет «обесцвеченный» в logs.txt.
        file_extra — можно передать доп. текст, который попадет только в файл (например полный адрес).
        """
        ts = datetime.now().astimezone(wib).strftime('%x %X %Z')
        console_line = (
            f"{Fore.CYAN + Style.BRIGHT}[ {ts} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}"
        )
        print(console_line, flush=True)

        try:
            file_line = f"[ {ts} ] | " + _sanitize_ansi(message)
            if file_extra:
                file_line += " | " + file_extra
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(file_line.rstrip() + "\n")
        except Exception:
            # пишем молча, чтобы логирование в файл не ломало работу бота
            pass

    def log_file_only(self, message: str):
        """Пишет строку только в файл (без печати в консоль)."""
        ts = datetime.now().astimezone(wib).strftime('%x %X %Z')
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"[ {ts} ] | {message}\n")
        except Exception:
            pass

    def log_account_header(self, address_full: str, address_masked: str):
        """Красивый заголовок в консоль (маска), и отдельная строка в файл с полным адресом."""
        separator = "=" * 25
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {address_masked} {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}",
            file_extra=f"ACCOUNT={address_full}"
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Giwa Testnet {Fore.BLUE + Style.BRIGHT}Automation Bot
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Giwa Testnet -- ferdie_jhovie{Style.RESET_ALL}
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    # ------------------- Прокси -------------------
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} not found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]

            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No proxies detected.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Total proxies : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to load proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None
        try:
            if proxy.startswith("socks"):
                connector = ProxyConnector.from_url(proxy)
                return connector, None, None
            elif proxy.startswith("http"):
                match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
                if match:
                    username, password, host_port = match.groups()
                    clean_url = f"http://{host_port}"
                    auth = BasicAuth(username, password)
                    return None, clean_url, auth
                else:
                    return None, proxy, None
            raise Exception("Unsupported proxy type.")
        except Exception as e:
            if "Missing dependencies for SOCKS support" in str(e):
                raise Exception("SOCKS proxies require the pysocks package: pip install pysocks")
            else:
                raise Exception(f"Proxy configuration error: {str(e)}")

    # ------------------- Аккаунты/адреса -------------------
    def generate_address(self, account: str):
        try:
            account_obj = Account.from_key(account)
            address = account_obj.address
            return address
        except Exception:
            return None

    def mask_account(self, account):
        try:
            return account[:6] + '*' * 6 + account[-6:]
        except Exception:
            return None

    # ------------------- Web3 -------------------
    async def get_web3_with_check(self, address: str, network: dict, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        if use_proxy and proxy:
            # Примечание: не все провайдеры web3 учитывают этот параметр; оставляем как в исходнике
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(network["rpc_url"], request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries:
                    self.log(f"{Fore.YELLOW+Style.BRIGHT}     Connection attempt {attempt + 1}/{retries}: {str(e)}{Style.RESET_ALL}")
                    await asyncio.sleep(3)
                    continue
                self.log(f"{Fore.RED+Style.BRIGHT}     Failed to connect to RPC: {str(e)}{Style.RESET_ALL}")
                return None

    async def get_token_balance(self, address: str, network: dict, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, network, use_proxy)
            if web3 is None:
                self.log(f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} Web3 connection failed {Style.RESET_ALL}")
                return None
            balance = web3.eth.get_balance(address)
            token_balance = balance / (10**18)
            return token_balance
        except Exception as e:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}")
            return None

    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception:
                pass
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction hash not found after maximum retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception:
                pass
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction receipt not found after maximum retries")

    # ------------------- Отправка транзакций (обновлено под случайные суммы) -------------------
    async def perform_deposit(self, account: str, address: str, network: dict, use_proxy: bool, amt_eth: Decimal):
        try:
            web3 = await self.get_web3_with_check(address, network, use_proxy)
            if web3 is None:
                self.log(f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} Web3 connection failed {Style.RESET_ALL}")
                return None, None

            amount_to_wei = int((amt_eth * Decimal(10**18)).to_integral_value())

            token_contract = web3.eth.contract(address=web3.to_checksum_address(network["contract"]), abi=network["abi"])
            deposit_data = token_contract.functions.depositTransaction(address, amount_to_wei, 21000, False, b'')

            estimated_gas = deposit_data.estimate_gas({"from": address, "value": amount_to_wei})
            max_priority_fee = web3.to_wei(0.001, "gwei")
            max_fee = max_priority_fee

            deposit_tx = deposit_data.build_transaction({
                "from": address,
                "value": amount_to_wei,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": web3.eth.get_transaction_count(address, "pending"),
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, deposit_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            return tx_hash, block_number

        except Exception as e:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}")
            return None, None

    async def perform_withdraw(self, account: str, address: str, network: dict, use_proxy: bool, amt_eth: Decimal):
        try:
            web3 = await self.get_web3_with_check(address, network, use_proxy)
            if web3 is None:
                self.log(f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} Web3 connection failed {Style.RESET_ALL}")
                return None, None

            amount_to_wei = int((amt_eth * Decimal(10**18)).to_integral_value())

            token_contract = web3.eth.contract(address=web3.to_checksum_address(network["contract"]), abi=network["abi"])
            withdraw_data = token_contract.functions.initiateWithdrawal(address, 21000, b'')

            estimated_gas = withdraw_data.estimate_gas({"from": address, "value": amount_to_wei})
            max_priority_fee = web3.to_wei(0.001, "gwei")
            max_fee = max_priority_fee

            withdraw_tx = withdraw_data.build_transaction({
                "from": address,
                "value": amount_to_wei,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": web3.eth.get_transaction_count(address, "pending"),
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, withdraw_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            return tx_hash, block_number

        except Exception as e:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}")
            return None, None

    # ------------------- Рандомизация count/amount -------------------
    def get_bridge_count_for_account(self):
        if self.bridge_count_min is not None and self.bridge_count_max is not None:
            return random.randint(int(self.bridge_count_min), int(self.bridge_count_max))
        return int(self.bridge_count)

    def get_random_amount_eth(self) -> Decimal:
        """
        Возвращает случайную сумму ETH в диапазоне [amount_min, amount_max]
        с сохранением точности (число знаков после точки берётся из ввода).
        """
        if self.amount_min is None or self.amount_max is None or self.amount_scale is None:
            # Fallback — не должен срабатывать при корректном вводе.
            return Decimal("0")

        lo_int = int((self.amount_min * self.amount_scale).to_integral_value())
        hi_int = int((self.amount_max * self.amount_scale).to_integral_value())
        if lo_int > hi_int:
            lo_int, hi_int = hi_int, lo_int
        r = random.randint(lo_int, hi_int)
        return Decimal(r) / Decimal(self.amount_scale)

    # ------------------- Таймер/вопросы -------------------
    async def print_timer(self):
        for remaining in range(random.randint(self.min_delay, self.max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Waiting{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT} seconds before the next transaction...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_bridge_question(self):
        # ---- Bridge count ----
        while True:
            raw = input(f"{Fore.YELLOW + Style.BRIGHT}Bridge count -> {Style.RESET_ALL}").strip()
            try:
                m = re.match(r'^\s*(\d+)\s*-\s*(\d+)\s*$', raw)
                if m:
                    a, b = int(m.group(1)), int(m.group(2))
                    lo, hi = (a, b) if a <= b else (b, a)
                    if lo < 0:
                        print(f"{Fore.RED + Style.BRIGHT}Count must be >= 0.{Style.RESET_ALL}")
                        continue
                    self.bridge_count_min = lo
                    self.bridge_count_max = hi
                    self.bridge_count = None
                    break
                n = int(raw)
                if n < 0:
                    print(f"{Fore.RED + Style.BRIGHT}Count must be >= 0.{Style.RESET_ALL}")
                    continue
                self.bridge_count = n
                self.bridge_count_min = None
                self.bridge_count_max = None
                break
            except Exception:
                print(f"{Fore.RED + Style.BRIGHT}Enter integer or range like 1-2.{Style.RESET_ALL}")

        # ---- ETH amount (range with decimal precision) ----
        while True:
            raw_amt = input(f"{Fore.YELLOW + Style.BRIGHT}ETH amount -> {Style.RESET_ALL}").strip()
            try:
                # принимаем ',' как десятичный разделитель
                raw_amt = raw_amt.replace(',', '.')
                m = re.match(r'^\s*([0-9]*\.?[0-9]+)\s*-\s*([0-9]*\.?[0-9]+)\s*$', raw_amt)
                if not m:
                    print(f"{Fore.RED + Style.BRIGHT}Enter range like 0,1000-0,5000 or 0.1000-0.5000.{Style.RESET_ALL}")
                    continue

                a_str, b_str = m.group(1), m.group(2)

                def frac_len(s: str) -> int:
                    return len(s.split('.', 1)[1]) if '.' in s else 0

                decs = max(frac_len(a_str), frac_len(b_str))
                scale = 10 ** decs

                a = Decimal(a_str)
                b = Decimal(b_str)
                lo, hi = (a, b) if a <= b else (b, a)
                if lo < 0:
                    print(f"{Fore.RED + Style.BRIGHT}ETH amount must be >= 0.{Style.RESET_ALL}")
                    continue

                self.amount_min = lo
                self.amount_max = hi
                self.amount_scale = scale
                break
            except Exception:
                print(f"{Fore.RED + Style.BRIGHT}Invalid amount range.{Style.RESET_ALL}")

    def print_delay_question(self):
        while True:
            try:
                min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Minimum delay per transaction -> {Style.RESET_ALL}").strip())
                if min_delay >= 0:
                    self.min_delay = min_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Minimum delay must be >= 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Please enter a number.{Style.RESET_ALL}")

        while True:
            try:
                max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Maximum delay per transaction -> {Style.RESET_ALL}").strip())
                if max_delay >= self.min_delay:
                    self.max_delay = max_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Maximum delay must be >= minimum delay.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Please enter a number.{Style.RESET_ALL}")

    def print_question(self):
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Choose a bridging option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Sepolia → Giwa{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Giwa → Sepolia{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Random direction{Style.RESET_ALL}")
                option = int(input(f"{Fore.BLUE + Style.BRIGHT}Select [1/2/3] -> {Style.RESET_ALL}").strip())

                if option in [1, 2, 3]:
                    option_type = (
                        "Sepolia → Giwa" if option == 1 else
                        "Giwa → Sepolia" if option == 2 else
                        "Random direction"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Selected {option_type}.{Style.RESET_ALL}")

                    self.print_bridge_question()
                    self.print_delay_question()
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter 1, 2, or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, or 3).{Style.RESET_ALL}")

        proxy_available = os.path.exists("proxy.txt") and os.path.getsize("proxy.txt") > 0
        if proxy_available:
            print(f"{Fore.GREEN + Style.BRIGHT}Proxy file detected. Proxies will be used.{Style.RESET_ALL}")
            proxy_choice = 1
        else:
            print(f"{Fore.YELLOW + Style.BRIGHT}No proxy file detected. Using direct connection.{Style.RESET_ALL}")
            proxy_choice = 2

        rotate_proxy = False
        if proxy_choice == 1:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate invalid proxies? [y/n] -> {Style.RESET_ALL}").strip()
                if rotate_proxy in ["y", "n"]:
                    rotate_proxy = rotate_proxy == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Please enter 'y' or 'n'.{Style.RESET_ALL}")

        return option, proxy_choice, rotate_proxy

    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection did not return 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        return None

    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}")

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    await asyncio.sleep(1)
                    continue
                return False
            return True

    # ------------------- Обёртки под операции (показывают сумму) -------------------
    async def process_perform_deposit(self, account: str, address: str, network: dict, use_proxy: bool, amt_eth: Decimal):
        tx_hash, block_number = await self.perform_deposit(account, address, network, use_proxy, amt_eth)
        if tx_hash and block_number:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}")
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Block   :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}")
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Tx Hash :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}")
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Explorer:{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {network['explorer']}{tx_hash} {Style.RESET_ALL}")
            self.log_file_only(
                f"ADDR={address} | NETWORK={network['name']} | OP=DEPOSIT | AMOUNT={amt_eth} | BLOCK={block_number} | TX={tx_hash}"
            )
        else:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} On-chain operation failed {Style.RESET_ALL}")

    async def process_perform_withdraw(self, account: str, address: str, network: dict, use_proxy: bool, amt_eth: Decimal):
        tx_hash, block_number = await self.perform_withdraw(account, address, network, use_proxy, amt_eth)
        if tx_hash and block_number:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}")
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Block   :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}")
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Tx Hash :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}")
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Explorer:{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {network['explorer']}{tx_hash} {Style.RESET_ALL}")
            self.log_file_only(
                f"ADDR={address} | NETWORK={network['name']} | OP=WITHDRAW | AMOUNT={amt_eth} | BLOCK={block_number} | TX={tx_hash}"
            )
        else:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} On-chain operation failed {Style.RESET_ALL}")

    # ------------------- Маршруты (с учётом рандомной суммы) -------------------
    async def process_option_1(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}     Route    :{Style.RESET_ALL}{Fore.BLUE+Style.BRIGHT} Sepolia → Giwa {Style.RESET_ALL}")

        balance = await self.get_token_balance(address, self.L1_NETWORK, use_proxy)
        self.log(f"{Fore.CYAN+Style.BRIGHT}     Balance :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {balance} ETH {Style.RESET_ALL}")

        if balance is None:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} Failed to fetch ETH balance {Style.RESET_ALL}")
            return

        min_needed = float(self.amount_min if self.amount_min is not None else Decimal("0"))
        if balance <= min_needed:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}{Fore.YELLOW+Style.BRIGHT} Insufficient ETH balance {Style.RESET_ALL}")
            return

        amt_eth = self.get_random_amount_eth()
        self.log(f"{Fore.CYAN+Style.BRIGHT}     Amount  :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {amt_eth} ETH {Style.RESET_ALL}")
        await self.process_perform_deposit(account, address, self.L1_NETWORK, use_proxy, amt_eth)

    async def process_option_2(self, account: str, address: str, use_proxy: bool):
        self.log(f"{Fore.CYAN+Style.BRIGHT}     Route    :{Style.RESET_ALL}{Fore.BLUE+Style.BRIGHT} Giwa → Sepolia {Style.RESET_ALL}")

        balance = await self.get_token_balance(address, self.L2_NETWORK, use_proxy)
        self.log(f"{Fore.CYAN+Style.BRIGHT}     Balance :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {balance} ETH {Style.RESET_ALL}")

        if balance is None:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} Failed to fetch ETH balance {Style.RESET_ALL}")
            return

        min_needed = float(self.amount_min if self.amount_min is not None else Decimal("0"))
        if balance <= min_needed:
            self.log(f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}{Fore.YELLOW+Style.BRIGHT} Insufficient ETH balance {Style.RESET_ALL}")
            return

        amt_eth = self.get_random_amount_eth()
        self.log(f"{Fore.CYAN+Style.BRIGHT}     Amount  :{Style.RESET_ALL}{Fore.WHITE+Style.BRIGHT} {amt_eth} ETH {Style.RESET_ALL}")
        await self.process_perform_withdraw(account, address, self.L2_NETWORK, use_proxy, amt_eth)

    # ------------------- Основная обработка аккаунта -------------------
    async def process_accounts(self, account: str, address: str, option: int, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            self.log(f"{Fore.CYAN+Style.BRIGHT}Bridging :{Style.RESET_ALL}")
            count_for_this_account = self.get_bridge_count_for_account()
            for i in range(count_for_this_account):
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}   ● {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT} of {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{count_for_this_account}{Style.RESET_ALL}                           "
                )

                if option == 1:
                    await self.process_option_1(account, address, use_proxy)
                elif option == 2:
                    await self.process_option_2(account, address, use_proxy)
                else:
                    bridge = random.choice([self.process_option_1, self.process_option_2])
                    await bridge(account, address, use_proxy)

                await self.print_timer()

    # ------------------- main -------------------
    async def main(self):
        try:
            # Проверяем источники приватников
            if os.path.exists(self.encrypted_file):
                self.log(f"{Fore.GREEN + Style.BRIGHT}Encrypted file detected. Password required for decryption.{Style.RESET_ALL}")
                password = self.get_password()
                accounts = self.decrypt_accounts(password)
                if accounts is None:
                    self.log(f"{Fore.RED + Style.BRIGHT}Decryption failed, exiting.{Style.RESET_ALL}")
                    return
                self.log(f"{Fore.GREEN + Style.BRIGHT}Successfully decrypted {len(accounts)} private key(s).{Style.RESET_ALL}")
            else:
                if os.path.exists('accounts.txt'):
                    self.log(f"{Fore.YELLOW + Style.BRIGHT}Encrypted file not found; using plaintext accounts.txt.{Style.RESET_ALL}")
                    with open('accounts.txt', 'r') as file:
                        accounts = [line.strip() for line in file if line.strip()]
                else:
                    self.log(f"{Fore.RED + Style.BRIGHT}Could not find accounts.txt or {self.encrypted_file}.{Style.RESET_ALL}")
                    return

            option, proxy_choice, rotate_proxy = self.print_question()

            while True:
                use_proxy = True if proxy_choice == 1 else False
                self.clear_terminal()
                self.welcome()
                self.log(f"{Fore.GREEN + Style.BRIGHT}Total accounts: {Style.RESET_ALL}{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}")

                if use_proxy:
                    await self.load_proxies()

                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        self.log_account_header(address_full=address, address_masked=self.mask_account(address))

                        if not address:
                            self.log(f"{Fore.CYAN+Style.BRIGHT}Status   :{Style.RESET_ALL}{Fore.RED+Style.BRIGHT} Invalid private key or unsupported library version {Style.RESET_ALL}")
                            continue

                        await self.process_accounts(account, address, option, use_proxy, rotate_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Waiting{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All accounts processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' not found.{Style.RESET_ALL}")
            return
        except ( Exception, ValueError ) as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Giwa()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ Exit ] Giwa Testnet - Bot{Style.RESET_ALL}"
        )
