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
        self.bridge_count = 0
        self.bridge_amount = 0
        self.min_delay = 0
        self.max_delay = 0

    def generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        """从密码生成加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def decrypt_accounts(self, password: str):
        """解密 accounts_encrypted.txt 文件"""
        try:
            if not os.path.exists(self.encrypted_file):
                self.log(f"{Fore.RED + Style.BRIGHT}错误: 加密文件 {self.encrypted_file} 不存在!{Style.RESET_ALL}")
                return None
            
            with open(self.encrypted_file, "rb") as f:
                # 读取盐
                salt = f.read(16)
                
                # 读取私钥数量
                count_bytes = f.read(4)
                count = int.from_bytes(count_bytes, 'big')
                
                # 从密码生成密钥
                key = self.generate_key_from_password(password, salt)
                fernet = Fernet(key)
                
                # 解密所有私钥
                accounts = []
                for _ in range(count):
                    # 读取加密私钥长度
                    length_bytes = f.read(4)
                    length = int.from_bytes(length_bytes, 'big')
                    
                    # 读取加密私钥
                    encrypted_account = f.read(length)
                    
                    # 解密私钥
                    decrypted_account = fernet.decrypt(encrypted_account).decode()
                    accounts.append(decrypted_account)
                
                return accounts
                
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}解密失败: {e}{Style.RESET_ALL}")
            return None

    def get_password(self):
        """获取用户输入的密码"""
        while True:
            password = getpass.getpass(f"{Fore.YELLOW + Style.BRIGHT}请输入解密密码: {Style.RESET_ALL}")
            if password:
                return password
            print(f"{Fore.RED + Style.BRIGHT}密码不能为空!{Style.RESET_ALL}")

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Giwa 测试网 {Fore.BLUE + Style.BRIGHT}自动机器人
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Giwa测试网--ferdie_jhovie{Style.RESET_ALL}
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}文件 {filename} 未找到。{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}未找到代理。{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}代理总数  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}加载代理失败: {e}{Style.RESET_ALL}")
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

            raise Exception("不支持此代理类型。")
        except Exception as e:
            if "Missing dependencies for SOCKS support" in str(e):
                raise Exception("SOCKS代理需要安装pysocks包: pip install pysocks")
            else:
                raise Exception(f"代理配置错误: {str(e)}")
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            
            return address
        except Exception as e:
            return None
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
        
    async def get_web3_with_check(self, address: str, network: dict, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(network["rpc_url"], request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries:
                    self.log(
                        f"{Fore.YELLOW+Style.BRIGHT}     连接尝试 {attempt + 1}/{retries}: {str(e)}{Style.RESET_ALL}"
                    )
                    await asyncio.sleep(3)
                    continue
                self.log(
                    f"{Fore.RED+Style.BRIGHT}     连接RPC失败: {str(e)}{Style.RESET_ALL}"
                )
                return None
        
    async def get_token_balance(self, address: str, network: dict, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, network, use_proxy)
            
            if web3 is None:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     消息 :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Web3连接失败 {Style.RESET_ALL}"
                )
                return None

            balance = web3.eth.get_balance(address)
            token_balance = balance / (10**18)

            return token_balance
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     消息 :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
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
            except Exception as e:
                pass
            await asyncio.sleep(2 ** attempt)
        raise Exception("在最大重试次数后未找到交易哈希")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                pass
            await asyncio.sleep(2 ** attempt)
        raise Exception("在最大重试次数后未找到交易收据")
    
    async def perform_deposit(self, account: str, address: str, network: dict, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, network, use_proxy)
            
            if web3 is None:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     消息 :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Web3连接失败 {Style.RESET_ALL}"
                )
                return None, None

            amount_to_wei = web3.to_wei(self.bridge_amount, "ether")

            token_contract = web3.eth.contract(address=web3.to_checksum_address(network["contract"]), abi=network["abi"])
            deposit_data = token_contract.functions.depositTransaction(address, amount_to_wei, 21000, False, b'')

            estimated_gas = deposit_data.estimate_gas({"from":address, "value":amount_to_wei})
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
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     消息 :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
    
    async def perform_withdraw(self, account: str, address: str, network: dict, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, network, use_proxy)
            
            if web3 is None:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     消息 :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Web3连接失败 {Style.RESET_ALL}"
                )
                return None, None

            amount_to_wei = web3.to_wei(self.bridge_amount, "ether")

            token_contract = web3.eth.contract(address=web3.to_checksum_address(network["contract"]), abi=network["abi"])
            withdraw_data = token_contract.functions.initiateWithdrawal(address, 21000, b'')

            estimated_gas = withdraw_data.estimate_gas({"from":address, "value":amount_to_wei})
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
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     消息 :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def print_timer(self):
        for remaining in range(random.randint(self.min_delay, self.max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}等待{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}秒后进行下一笔交易...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_bridge_question(self):
        while True:
            try:
                bridge_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}桥接次数 -> {Style.RESET_ALL}").strip())
                if bridge_count > 0:
                    self.bridge_count = bridge_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}请输入正数。{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}输入无效。请输入数字。{Style.RESET_ALL}")

        while True:
            try:
                bridge_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}输入 ETH 数量 -> {Style.RESET_ALL}").strip())
                if bridge_amount > 0:
                    self.bridge_amount = bridge_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}数量必须大于0。{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}输入无效。请输入数字。{Style.RESET_ALL}")

    def print_delay_question(self):
        while True:
            try:
                min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}每笔交易最小延迟 -> {Style.RESET_ALL}").strip())
                if min_delay >= 0:
                    self.min_delay = min_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}最小延迟必须 >= 0。{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}输入无效。请输入数字。{Style.RESET_ALL}")

        while True:
            try:
                max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}每笔交易最大延迟 -> {Style.RESET_ALL}").strip())
                if max_delay >= min_delay:
                    self.max_delay = max_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}最大延迟必须 >= 最小延迟。{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}输入无效。请输入数字。{Style.RESET_ALL}")

    def print_question(self):
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}选择选项:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. 从 Sepolia 桥接到 Giwa{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. 从 Giwa 桥接到 Sepolia{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. 随机桥接{Style.RESET_ALL}")
                option = int(input(f"{Fore.BLUE + Style.BRIGHT}请选择 [1/2/3] -> {Style.RESET_ALL}").strip())

                if option in [1, 2, 3]:
                    option_type = (
                        "从 Sepolia 桥接到 Giwa" if option == 1 else 
                        "从 Giwa 桥接到 Sepolia" if option == 2 else 
                        "随机桥接"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}已选择 {option_type}。{Style.RESET_ALL}")

                    self.print_bridge_question()
                    self.print_delay_question()
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}请输入 1、2 或 3。{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}输入无效。请输入数字 (1, 2, 或 3)。{Style.RESET_ALL}")

        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. 使用代理运行{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. 不使用代理运行{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}请选择 [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = "使用" if proxy_choice == 1 else "不使用"
                    print(f"{Fore.GREEN + Style.BRIGHT}已选择{proxy_type}代理运行。{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}请输入 1 或 2。{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}输入无效。请输入数字 (1 或 2)。{Style.RESET_ALL}")

        rotate_proxy = False
        if proxy_choice == 1:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}轮换无效代理? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate_proxy in ["y", "n"]:
                    rotate_proxy = rotate_proxy == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}输入无效。请输入 'y' 或 'n'。{Style.RESET_ALL}")

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
                f"{Fore.CYAN+Style.BRIGHT}状态    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} 连接未返回 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}代理     :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    await asyncio.sleep(1)
                    continue

                return False

            return True
        
    async def process_perform_deposit(self, account: str, address: str, network: dict, use_proxy: bool):
        tx_hash, block_number = await self.perform_deposit(account, address, network, use_proxy)
        if tx_hash and block_number:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} 成功 {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     区块   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     交易哈希 :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     浏览器:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {network['explorer']}{tx_hash} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} 链上操作失败 {Style.RESET_ALL}"
            )
        
    async def process_perform_withdraw(self, account: str, address: str, network: dict, use_proxy: bool):
        tx_hash, block_number = await self.perform_withdraw(account, address, network, use_proxy)
        if tx_hash and block_number:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} 成功 {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     区块   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     交易哈希 :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     浏览器:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {network['explorer']}{tx_hash} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} 链上操作失败 {Style.RESET_ALL}"
            )
        
    async def process_option_1(self, account: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}     配对    :{Style.RESET_ALL}"
            f"{Fore.BLUE+Style.BRIGHT} 从 Sepolia 到 Giwa {Style.RESET_ALL}"
        )
        
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}     数量  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.bridge_amount} ETH {Style.RESET_ALL}"
        )

        balance = await self.get_token_balance(address, self.L1_NETWORK, use_proxy)
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}     余额 :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} ETH {Style.RESET_ALL}"
        )

        if balance is None:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} 获取 ETH 代币余额失败 {Style.RESET_ALL}"
            )
            return

        if balance <= self.bridge_amount:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} ETH 代币余额不足 {Style.RESET_ALL}"
            )
            return

        await self.process_perform_deposit(account, address, self.L1_NETWORK, use_proxy)
        
    async def process_option_2(self, account: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}     配对    :{Style.RESET_ALL}"
            f"{Fore.BLUE+Style.BRIGHT} 从 Giwa 到 Sepolia {Style.RESET_ALL}"
        )

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}     数量  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.bridge_amount} ETH {Style.RESET_ALL}"
        )

        balance = await self.get_token_balance(address, self.L2_NETWORK, use_proxy)
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}     余额 :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} ETH {Style.RESET_ALL}"
        )

        if balance is None:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} 获取 ETH 代币余额失败 {Style.RESET_ALL}"
            )
            return

        if balance <= self.bridge_amount:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Status  :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} ETH 代币余额不足 {Style.RESET_ALL}"
            )
            return

        await self.process_perform_withdraw(account, address, self.L2_NETWORK, use_proxy)

    async def process_accounts(self, account: str, address: str, option: int, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:

            if option == 1:
                self.log(f"{Fore.CYAN+Style.BRIGHT}桥接    :{Style.RESET_ALL}")
                for i in range(self.bridge_count):
                    self.log(
                        f"{Fore.MAGENTA+Style.BRIGHT}   ● {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT} 共 {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{self.bridge_count}{Style.RESET_ALL}                           "
                    )
                    await self.process_option_1(account, address, use_proxy)
                    await self.print_timer()

            elif option == 2:
                self.log(f"{Fore.CYAN+Style.BRIGHT}桥接    :{Style.RESET_ALL}")
                for i in range(self.bridge_count):
                    self.log(
                        f"{Fore.MAGENTA+Style.BRIGHT}   ● {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT} 共 {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{self.bridge_count}{Style.RESET_ALL}                           "
                    )
                    await self.process_option_2(account, address, use_proxy)
                    await self.print_timer()

            elif option == 3:
                self.log(f"{Fore.CYAN+Style.BRIGHT}桥接    :{Style.RESET_ALL}")
                for i in range(self.bridge_count):
                    self.log(
                        f"{Fore.MAGENTA+Style.BRIGHT}   ● {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT} 共 {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{self.bridge_count}{Style.RESET_ALL}                           "
                    )

                    bridge = random.choice([self.process_option_1, self.process_option_2])
                    await bridge(account, address, use_proxy)
                    await self.print_timer()

    async def main(self):
        try:
            # 检查是否存在加密文件
            if os.path.exists(self.encrypted_file):
                self.log(f"{Fore.GREEN + Style.BRIGHT}检测到加密文件，需要密码解密{Style.RESET_ALL}")
                password = self.get_password()
                accounts = self.decrypt_accounts(password)
                if accounts is None:
                    self.log(f"{Fore.RED + Style.BRIGHT}解密失败，程序退出{Style.RESET_ALL}")
                    return
                self.log(f"{Fore.GREEN + Style.BRIGHT}成功解密 {len(accounts)} 个私钥{Style.RESET_ALL}")
            else:
                # 检查是否存在原始文件
                if os.path.exists('accounts.txt'):
                    self.log(f"{Fore.YELLOW + Style.BRIGHT}未找到加密文件，使用原始 accounts.txt{Style.RESET_ALL}")
                    with open('accounts.txt', 'r') as file:
                        accounts = [line.strip() for line in file if line.strip()]
                else:
                    self.log(f"{Fore.RED + Style.BRIGHT}未找到 accounts.txt 或 {self.encrypted_file}{Style.RESET_ALL}")
                    return
            
            option, proxy_choice, rotate_proxy = self.print_question()

            while True:
                use_proxy = True if proxy_choice == 1 else False

                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}账户总数: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies()
                
                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}状态    :{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} 私钥无效或库版本不支持 {Style.RESET_ALL}"
                            )
                            continue
                        
                        await self.process_accounts(account, address, option, use_proxy, rotate_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ 等待{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}所有账户已处理完毕。{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}文件 'accounts.txt' 未找到。{Style.RESET_ALL}")
            return
        except ( Exception, ValueError ) as e:
            self.log(f"{Fore.RED+Style.BRIGHT}错误: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Giwa()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ 退出 ] Giwa 测试网 - 机器人{Style.RESET_ALL}                                       "                              
        )
