#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Giwa Testnet Bot - 私钥加密工具
用于加密 accounts.txt 中的私钥
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
        """从密码生成加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_accounts(self, password: str):
        """加密 accounts.txt 文件"""
        try:
            # 检查 accounts.txt 是否存在
            if not os.path.exists("accounts.txt"):
                print("❌ 错误: accounts.txt 文件不存在!")
                return False
            
            # 读取原始私钥
            with open("accounts.txt", "r") as f:
                accounts = [line.strip() for line in f if line.strip()]
            
            if not accounts:
                print("❌ 错误: accounts.txt 文件为空!")
                return False
            
            # 生成随机盐
            salt = os.urandom(16)
            
            # 从密码生成密钥
            key = self.generate_key_from_password(password, salt)
            fernet = Fernet(key)
            
            # 加密所有私钥
            encrypted_accounts = []
            for account in accounts:
                encrypted_account = fernet.encrypt(account.encode())
                encrypted_accounts.append(encrypted_account)
            
            # 保存加密后的数据
            with open(self.encrypted_file, "wb") as f:
                # 先写入盐
                f.write(salt)
                # 再写入加密的私钥数量
                f.write(len(encrypted_accounts).to_bytes(4, 'big'))
                # 最后写入所有加密的私钥
                for encrypted_account in encrypted_accounts:
                    f.write(len(encrypted_account).to_bytes(4, 'big'))
                    f.write(encrypted_account)
            
            print(f"✅ 成功加密 {len(accounts)} 个私钥到 {self.encrypted_file}")
            print("🔐 请妥善保管您的密码，没有密码将无法解密私钥!")
            
            # 删除原始文件
            if os.path.exists("accounts.txt"):
                os.remove("accounts.txt")
                print("🗑️  原始 accounts.txt 文件已删除")
            
            return True
            
        except Exception as e:
            print(f"❌ 加密失败: {e}")
            return False
    
    def decrypt_accounts(self, password: str):
        """解密 accounts_encrypted.txt 文件"""
        try:
            if not os.path.exists(self.encrypted_file):
                print("❌ 错误: 加密文件不存在!")
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
            print(f"❌ 解密失败: {e}")
            return None

def main():
    print("🔐 Giwa Testnet Bot - 私钥加密工具")
    print("=" * 50)
    
    encryptor = AccountEncryptor()
    
    # 检查是否已有加密文件
    if os.path.exists(encryptor.encrypted_file):
        print("⚠️  检测到已存在加密文件!")
        choice = input("是否要重新加密? (y/n): ").strip().lower()
        if choice != 'y':
            print("操作已取消")
            return
    
    # 获取密码
    while True:
        password = getpass.getpass("请输入加密密码: ").strip()
        if not password:
            print("❌ 密码不能为空!")
            continue
        
        confirm_password = getpass.getpass("请确认密码: ").strip()
        if password != confirm_password:
            print("❌ 两次输入的密码不一致!")
            continue
        
        break
    
    # 执行加密
    if encryptor.encrypt_accounts(password):
        print("\n🎉 加密完成!")
        print("现在可以运行 python bot.py 来使用加密的私钥")
    else:
        print("\n❌ 加密失败!")

if __name__ == "__main__":
    main()
