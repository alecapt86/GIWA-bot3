#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Giwa Testnet Bot - Private Key Encryption Utility
Used to encrypt the private keys stored in accounts.txt.
"""

import os
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class AccountEncryptor:
    def __init__(self):
        self.encrypted_file = "accounts_encrypted.txt"
        self.key_file = "encryption.key"
    
    def generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Generate an encryption key from the provided password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_accounts(self, password: str):
        """Encrypt the accounts.txt file using the supplied password."""
        try:
            # Check if accounts.txt exists
            if not os.path.exists("accounts.txt"):
                print("❌ Error: accounts.txt file does not exist!")
                return False

            # Read the raw private keys
            with open("accounts.txt", "r") as f:
                accounts = [line.strip() for line in f if line.strip()]

            if not accounts:
                print("❌ Error: accounts.txt file is empty!")
                return False

            # Generate a random salt
            salt = os.urandom(16)

            # Derive a key from the password
            key = self.generate_key_from_password(password, salt)
            fernet = Fernet(key)

            # Encrypt all private keys
            encrypted_accounts = []
            for account in accounts:
                encrypted_account = fernet.encrypt(account.encode())
                encrypted_accounts.append(encrypted_account)

            # Persist the encrypted data
            with open(self.encrypted_file, "wb") as f:
                # Write the salt first
                f.write(salt)
                # Then write the number of encrypted private keys
                f.write(len(encrypted_accounts).to_bytes(4, 'big'))
                # Finally write all encrypted private keys
                for encrypted_account in encrypted_accounts:
                    f.write(len(encrypted_account).to_bytes(4, 'big'))
                    f.write(encrypted_account)

            print(f"✅ Successfully encrypted {len(accounts)} private key(s) to {self.encrypted_file}")
            print("🔐 Keep your password safe—without it the private keys cannot be decrypted!")

            # Delete the original file
            if os.path.exists("accounts.txt"):
                os.remove("accounts.txt")
                print("🗑️  Original accounts.txt file deleted")

            return True

        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return False

    def decrypt_accounts(self, password: str):
        """Decrypt the accounts_encrypted.txt file."""
        try:
            if not os.path.exists(self.encrypted_file):
                print("❌ Error: encrypted file not found!")
                return None

            with open(self.encrypted_file, "rb") as f:
                # Read the salt
                salt = f.read(16)

                # Read the number of private keys
                count_bytes = f.read(4)
                count = int.from_bytes(count_bytes, 'big')

                # Derive the key from the password
                key = self.generate_key_from_password(password, salt)
                fernet = Fernet(key)

                # Decrypt each private key
                accounts = []
                for _ in range(count):
                    # Read the length of the encrypted key
                    length_bytes = f.read(4)
                    length = int.from_bytes(length_bytes, 'big')

                    # Read the encrypted private key
                    encrypted_account = f.read(length)

                    # Decrypt the private key
                    decrypted_account = fernet.decrypt(encrypted_account).decode()
                    accounts.append(decrypted_account)

                return accounts

        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            return None

def main():
    print("🔐 Giwa Testnet Bot - Private Key Encryption Utility")
    print("=" * 50)

    encryptor = AccountEncryptor()

    # Check if an encrypted file already exists
    if os.path.exists(encryptor.encrypted_file):
        print("⚠️  Detected an existing encrypted file!")
        choice = input("Re-encrypt the private keys? (y/n): ").strip().lower()
        if choice != 'y':
            print("Operation cancelled")
            return

    # Prompt for a password
    while True:
        password = getpass.getpass("Enter an encryption password: ").strip()
        if not password:
            print("❌ Password cannot be empty!")
            continue

        confirm_password = getpass.getpass("Confirm the password: ").strip()
        if password != confirm_password:
            print("❌ Passwords do not match!")
            continue

        break

    # Perform the encryption
    if encryptor.encrypt_accounts(password):
        print("\n🎉 Encryption complete!")
        print("You can now run python bot.py to use the encrypted private keys.")
    else:
        print("\n❌ Encryption failed!")

if __name__ == "__main__":
    main()
