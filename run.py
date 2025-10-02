#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Giwa Testnet Bot - One-Click Runner Script
Automatically executes the encryption and bot workflows.
"""

import os
import sys
import subprocess
import time
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class RunManager:
    def __init__(self):
        self.encrypt_script = "encrypt_accounts.py"
        self.bot_script = "bot.py"
        self.encrypted_file = "accounts_encrypted.txt"
        self.accounts_file = "accounts.txt"
    
    def print_banner(self):
        """Print the welcome banner."""
        print(f"""
{Fore.GREEN + Style.BRIGHT}╔══════════════════════════════════════════════════════════════╗
║                    Giwa Testnet One-Click Runner              ║
║                        ferdie_jhovie                        ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)

    def check_files(self):
        """Check that all required files exist."""
        print(f"{Fore.CYAN + Style.BRIGHT}🔍 Checking file status...{Style.RESET_ALL}")

        # Check encryption script
        if not os.path.exists(self.encrypt_script):
            print(f"{Fore.RED + Style.BRIGHT}❌ Error: {self.encrypt_script} is missing!{Style.RESET_ALL}")
            return False

        # Check bot script
        if not os.path.exists(self.bot_script):
            print(f"{Fore.RED + Style.BRIGHT}❌ Error: {self.bot_script} is missing!{Style.RESET_ALL}")
            return False

        print(f"{Fore.GREEN + Style.BRIGHT}✅ Required files verified{Style.RESET_ALL}")
        return True

    def check_encryption_status(self):
        """Check whether the private keys are already encrypted."""
        if os.path.exists(self.encrypted_file):
            print(f"{Fore.GREEN + Style.BRIGHT}🔐 Detected encrypted file: {self.encrypted_file}{Style.RESET_ALL}")
            return True
        elif os.path.exists(self.accounts_file):
            print(f"{Fore.YELLOW + Style.BRIGHT}⚠️  Detected raw private key file: {self.accounts_file}{Style.RESET_ALL}")
            return False
        else:
            print(f"{Fore.RED + Style.BRIGHT}❌ No private key file found!{Style.RESET_ALL}")
            return None

    def run_encryption(self):
        """Execute the encryption script."""
        print(f"\n{Fore.CYAN + Style.BRIGHT}🔐 Starting private key encryption...{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}Running: python {self.encrypt_script}{Style.RESET_ALL}")
        
        try:
            # Run encryption script
            result = subprocess.run([sys.executable, self.encrypt_script],
                                  capture_output=False,
                                  text=True,
                                  input="",
                                  timeout=300)  # 5 minute timeout

            if result.returncode == 0:
                print(f"{Fore.GREEN + Style.BRIGHT}✅ Encryption completed!{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED + Style.BRIGHT}❌ Encryption failed!{Style.RESET_ALL}")
                return False

        except subprocess.TimeoutExpired:
            print(f"{Fore.RED + Style.BRIGHT}❌ Encryption timed out!{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}❌ Error during encryption: {e}{Style.RESET_ALL}")
            return False

    def run_bot(self):
        """Execute the trading bot script."""
        print(f"\n{Fore.CYAN + Style.BRIGHT}🤖 Launching the bot...{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}Running: python {self.bot_script}{Style.RESET_ALL}")
        
        try:
            # Run bot script
            result = subprocess.run([sys.executable, self.bot_script],
                                  capture_output=False,
                                  text=True)

            if result.returncode == 0:
                print(f"{Fore.GREEN + Style.BRIGHT}✅ Bot finished successfully!{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED + Style.BRIGHT}❌ Bot encountered an error!{Style.RESET_ALL}")
                return False

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW + Style.BRIGHT}⚠️  Bot execution interrupted by user{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}❌ Error while running the bot: {e}{Style.RESET_ALL}")
            return False


    def show_menu(self):
        """Display the main menu."""
        print(f"\n{Fore.CYAN + Style.BRIGHT}📋 Select an option:{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}1. Auto run (encrypt + launch bot){Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}2. Run encryption only{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}3. Launch bot only{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}4. Exit{Style.RESET_ALL}")

        while True:
            try:
                choice = input(f"\n{Fore.BLUE + Style.BRIGHT}Choose [1-4]: {Style.RESET_ALL}").strip()
                if choice in ['1', '2', '3', '4']:
                    return int(choice)
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter a number between 1 and 4{Style.RESET_ALL}")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW + Style.BRIGHT}Program exited by user{Style.RESET_ALL}")
                sys.exit(0)

    def run_auto(self):
        """Run the automated workflow."""
        print(f"\n{Fore.CYAN + Style.BRIGHT}🚀 Starting automated workflow...{Style.RESET_ALL}")

        # Check encryption status
        encryption_status = self.check_encryption_status()

        if encryption_status is None:
            print(f"{Fore.RED + Style.BRIGHT}❌ Private key file not found, cannot continue{Style.RESET_ALL}")
            return False

        # Encrypt if required
        if not encryption_status:
            print(f"{Fore.YELLOW + Style.BRIGHT}Private keys must be encrypted first{Style.RESET_ALL}")
            if not self.run_encryption():
                return False
            print(f"{Fore.GREEN + Style.BRIGHT}Starting the bot in 2 seconds...{Style.RESET_ALL}")
            time.sleep(2)

        # Launch the bot
        return self.run_bot()

    def main(self):
        """Entry point for the runner."""
        self.print_banner()

        # Verify files
        if not self.check_files():
            input(f"\n{Fore.RED + Style.BRIGHT}Press Enter to exit...{Style.RESET_ALL}")
            return

        # Show menu
        choice = self.show_menu()

        if choice == 1:
            # Auto run
            self.run_auto()
        elif choice == 2:
            # Encryption only
            self.run_encryption()
        elif choice == 3:
            # Bot only
            self.run_bot()
        elif choice == 4:
            # Exit
            print(f"{Fore.GREEN + Style.BRIGHT}👋 Goodbye!{Style.RESET_ALL}")
            return

        # Wait for user confirmation
        input(f"\n{Fore.CYAN + Style.BRIGHT}Press Enter to exit...{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        manager = RunManager()
        manager.main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW + Style.BRIGHT}Program interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED + Style.BRIGHT}Program encountered an error: {e}{Style.RESET_ALL}")
