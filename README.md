# Giwa Testnet Bot - 私钥加密使用指南

## 概述
为了保护您的私钥安全，本脚本现在支持私钥加密功能。私钥将被加密存储在 `accounts_encrypted.txt` 文件中，运行机器人时需要输入密码进行解密。

## 使用步骤

### 1. 安装依赖
```bash
# 方法1: 使用requirements.txt
pip install -r requirements.txt

# 方法2: 使用安装脚本（推荐）
python install_dependencies.py

# 方法3: 手动安装SOCKS支持
pip install pysocks==1.7.1
```

### 2. 准备私钥文件
将您的私钥放入 `accounts.txt` 文件中，每行一个私钥：
```
your_private_key_1
your_private_key_2
your_private_key_3
```

### 3. 加密私钥
运行加密脚本：
```bash
python encrypt_accounts.py
```

按照提示：
- 输入加密密码（请记住此密码）
- 确认密码
- 等待加密完成

加密完成后：
- 原始 `accounts.txt` 文件将被自动删除
- 生成加密文件 `accounts_encrypted.txt`

### 4. 运行机器人
```bash
python bot.py
```

程序将：
- 检测到加密文件
- 提示输入解密密码
- 解密私钥后正常运行

## 安全特性

1. **强加密算法**: 使用 PBKDF2 + Fernet 加密
2. **随机盐值**: 每次加密都生成不同的盐值
3. **密码保护**: 没有正确密码无法解密
4. **内存安全**: 解密后的私钥仅在内存中短暂存在

## 文件说明

- `accounts.txt`: 原始私钥文件（加密后自动删除）
- `accounts_encrypted.txt`: 加密后的私钥文件
- `encrypt_accounts.py`: 加密工具脚本

## 注意事项

1. **密码安全**: 请使用强密码并妥善保管
2. **备份重要**: 建议备份加密文件和密码
3. **定期更新**: 建议定期更换密码并重新加密
4. **环境安全**: 在安全的计算机环境中进行加密操作
5. **原始文件**: 加密后原始 accounts.txt 会被自动删除

## 故障排除

### 解密失败
- 检查密码是否正确
- 确认 `accounts_encrypted.txt` 文件完整
- 重新运行加密脚本

### 找不到文件
- 确认 `accounts_encrypted.txt` 存在
- 如果没有加密文件，程序会尝试使用原始的 `accounts.txt`

## 恢复原始文件
如果需要恢复原始私钥：
1. 运行 `python encrypt_accounts.py`
2. 输入正确的密码
3. 程序会解密并显示私钥
4. 手动复制到新的 `accounts.txt` 文件
