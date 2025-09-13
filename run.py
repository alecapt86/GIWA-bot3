#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Giwa Testnet Bot - 一键运行脚本
自动执行加密和运行流程
"""

import os
import sys
import subprocess
import time
from colorama import Fore, Style, init

# 初始化 colorama
init(autoreset=True)

class RunManager:
    def __init__(self):
        self.encrypt_script = "encrypt_accounts.py"
        self.bot_script = "bot.py"
        self.encrypted_file = "accounts_encrypted.txt"
        self.accounts_file = "accounts.txt"
    
    def print_banner(self):
        """打印欢迎横幅"""
        print(f"""
{Fore.GREEN + Style.BRIGHT}╔══════════════════════════════════════════════════════════════╗
║                    Giwa 测试网 一键运行脚本                    ║
║                        ferdie_jhovie                        ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
    
    def check_files(self):
        """检查必要文件是否存在"""
        print(f"{Fore.CYAN + Style.BRIGHT}🔍 检查文件状态...{Style.RESET_ALL}")
        
        # 检查加密脚本
        if not os.path.exists(self.encrypt_script):
            print(f"{Fore.RED + Style.BRIGHT}❌ 错误: {self.encrypt_script} 文件不存在!{Style.RESET_ALL}")
            return False
        
        # 检查机器人脚本
        if not os.path.exists(self.bot_script):
            print(f"{Fore.RED + Style.BRIGHT}❌ 错误: {self.bot_script} 文件不存在!{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.GREEN + Style.BRIGHT}✅ 所有必要文件检查完成{Style.RESET_ALL}")
        return True
    
    def check_encryption_status(self):
        """检查加密状态"""
        if os.path.exists(self.encrypted_file):
            print(f"{Fore.GREEN + Style.BRIGHT}🔐 检测到已加密文件: {self.encrypted_file}{Style.RESET_ALL}")
            return True
        elif os.path.exists(self.accounts_file):
            print(f"{Fore.YELLOW + Style.BRIGHT}⚠️  检测到原始私钥文件: {self.accounts_file}{Style.RESET_ALL}")
            return False
        else:
            print(f"{Fore.RED + Style.BRIGHT}❌ 未找到私钥文件!{Style.RESET_ALL}")
            return None
    
    def run_encryption(self):
        """运行加密脚本"""
        print(f"\n{Fore.CYAN + Style.BRIGHT}🔐 开始加密私钥...{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}正在运行: python {self.encrypt_script}{Style.RESET_ALL}")
        
        try:
            # 运行加密脚本
            result = subprocess.run([sys.executable, self.encrypt_script], 
                                  capture_output=False, 
                                  text=True, 
                                  input="", 
                                  timeout=300)  # 5分钟超时
            
            if result.returncode == 0:
                print(f"{Fore.GREEN + Style.BRIGHT}✅ 加密完成!{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED + Style.BRIGHT}❌ 加密失败!{Style.RESET_ALL}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"{Fore.RED + Style.BRIGHT}❌ 加密超时!{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}❌ 加密过程出错: {e}{Style.RESET_ALL}")
            return False
    
    def run_bot(self):
        """运行机器人脚本"""
        print(f"\n{Fore.CYAN + Style.BRIGHT}🤖 启动机器人...{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}正在运行: python {self.bot_script}{Style.RESET_ALL}")
        
        try:
            # 运行机器人脚本
            result = subprocess.run([sys.executable, self.bot_script], 
                                  capture_output=False, 
                                  text=True)
            
            if result.returncode == 0:
                print(f"{Fore.GREEN + Style.BRIGHT}✅ 机器人运行完成!{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED + Style.BRIGHT}❌ 机器人运行出错!{Style.RESET_ALL}")
                return False
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW + Style.BRIGHT}⚠️  用户中断机器人运行{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}❌ 机器人运行出错: {e}{Style.RESET_ALL}")
            return False
    
    def show_menu(self):
        """显示菜单选项"""
        print(f"\n{Fore.CYAN + Style.BRIGHT}📋 请选择操作:{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}1. 自动运行 (加密 + 启动机器人){Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}2. 仅运行加密脚本{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}3. 仅启动机器人{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}4. 退出{Style.RESET_ALL}")
        
        while True:
            try:
                choice = input(f"\n{Fore.BLUE + Style.BRIGHT}请选择 [1-4]: {Style.RESET_ALL}").strip()
                if choice in ['1', '2', '3', '4']:
                    return int(choice)
                else:
                    print(f"{Fore.RED + Style.BRIGHT}请输入 1-4 之间的数字{Style.RESET_ALL}")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW + Style.BRIGHT}程序已退出{Style.RESET_ALL}")
                sys.exit(0)
    
    def run_auto(self):
        """自动运行流程"""
        print(f"\n{Fore.CYAN + Style.BRIGHT}🚀 开始自动运行流程...{Style.RESET_ALL}")
        
        # 检查加密状态
        encryption_status = self.check_encryption_status()
        
        if encryption_status is None:
            print(f"{Fore.RED + Style.BRIGHT}❌ 未找到私钥文件，无法继续{Style.RESET_ALL}")
            return False
        
        # 如果需要加密
        if not encryption_status:
            print(f"{Fore.YELLOW + Style.BRIGHT}需要先加密私钥文件{Style.RESET_ALL}")
            if not self.run_encryption():
                return False
            print(f"{Fore.GREEN + Style.BRIGHT}等待 2 秒后启动机器人...{Style.RESET_ALL}")
            time.sleep(2)
        
        # 运行机器人
        return self.run_bot()
    
    def main(self):
        """主函数"""
        self.print_banner()
        
        # 检查文件
        if not self.check_files():
            input(f"\n{Fore.RED + Style.BRIGHT}按回车键退出...{Style.RESET_ALL}")
            return
        
        # 显示菜单
        choice = self.show_menu()
        
        if choice == 1:
            # 自动运行
            self.run_auto()
        elif choice == 2:
            # 仅加密
            self.run_encryption()
        elif choice == 3:
            # 仅运行机器人
            self.run_bot()
        elif choice == 4:
            # 退出
            print(f"{Fore.GREEN + Style.BRIGHT}👋 再见!{Style.RESET_ALL}")
            return
        
        # 等待用户确认
        input(f"\n{Fore.CYAN + Style.BRIGHT}按回车键退出...{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        manager = RunManager()
        manager.main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW + Style.BRIGHT}程序被用户中断{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED + Style.BRIGHT}程序运行出错: {e}{Style.RESET_ALL}")
