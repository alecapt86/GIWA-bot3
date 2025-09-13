# Giwa Testnet Bot - 自动桥接机器人

一个用于 Giwa 测试网的自动化桥接机器人，支持私钥加密、代理自动检测和多种桥接模式。

## ✨ 主要功能

- 🔐 **私钥加密保护** - 使用密码加密私钥，提高安全性
- 🌐 **智能代理检测** - 自动检测并使用代理（如果可用）
- 🌉 **多种桥接模式** - 支持 Sepolia ↔ Giwa 双向桥接
- 🔄 **随机桥接** - 随机选择桥接方向
- 👥 **多账户支持** - 批量处理多个钱包
- ⚡ **一键运行** - 简化的运行流程

## 📋 系统要求

- Python 3.8 或更高版本
- Windows/Linux/macOS
- 稳定的网络连接

## 🚀 快速开始

### 1. 下载项目
```bash
git clone https://github.com/sdohuajia/GIWA-bot.git
cd GIWA-bot
```

### 2. 安装依赖
```bash
# 方法1: 使用 requirements.txt
pip install -r requirements.txt

# 方法2: 手动安装 SOCKS 支持（如果遇到代理问题）
pip install pysocks==1.7.1
```

### 3. 准备配置文件

#### 📝 私钥文件 (`accounts.txt`)
将您的私钥放入 `accounts.txt` 文件中，每行一个：
```
your_private_key_1
your_private_key_2
your_private_key_3
```

#### 🌐 代理文件 (`proxy.txt`) - 可选
如果需要使用代理，将代理信息放入 `proxy.txt` 文件中：
```
# HTTP 代理
http://proxy_ip:port
http://username:password@proxy_ip:port

# SOCKS 代理
socks5://proxy_ip:port
socks5://username:password@proxy_ip:port
```

### 4. 运行机器人

#### 方法1: 一键运行（推荐）
```bash
python run.py
```

#### 方法2: 直接运行
```bash
python bot.py
```

## 🔐 私钥加密使用流程

### 首次使用 - 加密私钥
1. 将私钥放入 `accounts.txt` 文件
2. 运行加密脚本：
   ```bash
   python encrypt_accounts.py
   ```
3. 输入加密密码（请记住此密码）
4. 确认密码
5. 等待加密完成

### 使用加密私钥运行
1. 运行机器人：
   ```bash
   python run.py
   ```
2. 选择 "1. 自动运行"
3. 输入解密密码
4. 程序自动解密并运行

## 🎯 使用流程详解

### 1. 启动程序
```bash
python run.py
```

### 2. 选择运行模式
程序会显示菜单：
```
╔══════════════════════════════════════════════════════════════╗
║                    Giwa 测试网 一键运行脚本                    ║
║                        ferdie_jhovie                        ║
╚══════════════════════════════════════════════════════════════╝

📋 请选择操作:
1. 自动运行 (加密 + 启动机器人)
2. 仅运行加密脚本
3. 仅启动机器人
4. 退出
```

### 3. 选择桥接类型
```
选择选项:
1. 从 Sepolia 桥接到 Giwa
2. 从 Giwa 桥接到 Sepolia
3. 随机桥接
```

### 4. 输入参数
- **桥接次数**: 每个账户要执行的桥接次数
- **ETH 数量**: 每次桥接的 ETH 数量
- **最小延迟**: 每笔交易之间的最小等待时间（秒）
- **最大延迟**: 每笔交易之间的最大等待时间（秒）

### 5. 代理设置
程序会自动检测：
- 如果存在 `proxy.txt` 文件 → 自动使用代理
- 如果不存在 `proxy.txt` 文件 → 直接连接

### 6. 开始执行
程序会：
1. 加载并解密私钥（如果已加密）
2. 检测代理设置
3. 逐个处理每个账户
4. 显示详细的执行日志

## 📊 运行示例

```
[ 09/13/25 16:15:31 WIB ] | 检测到代理文件，将使用代理运行
[ 09/13/25 16:15:31 WIB ] | 轮换无效代理? [y/n] -> y
[ 09/13/25 16:15:31 WIB ] | 账户总数: 3
[ 09/13/25 16:15:31 WIB ] | =========================[ 0x1234...5678 ]=========================
[ 09/13/25 16:15:31 WIB ] |      配对    : 从 Sepolia 到 Giwa
[ 09/13/25 16:15:31 WIB ] |      数量  : 0.001 ETH
[ 09/13/25 16:15:31 WIB ] |      余额 : 0.05 ETH
[ 09/13/25 16:15:31 WIB ] |     Status  : 成功
[ 09/13/25 16:15:31 WIB ] |     交易哈希 : 0xabcd...efgh
```

## 🔧 高级配置

### 代理推荐
如果您需要可靠的代理服务，推荐使用 **Nstproxy**：
- 价格实惠（从 $0.1/GB）
- 全球覆盖
- 轮换控制
- 反封禁技术

🔗 [Nstproxy.com](https://www.nstproxy.com/?utm_source=vonssy) | [Telegram](https://t.me/nstproxy) | [Discord](https://discord.gg/5jjWCAmvng) | [Github](https://github.com/Nstproxy)  
👉 使用代码 **VONSSY** 获得 **10% 折扣**

### 依赖包管理
如果遇到依赖问题，可以手动检查：
```bash
# 检查包版本
pip show web3 eth-account

# 重新安装特定版本
pip uninstall web3 eth-account
pip install web3==7.11.1 eth-account==0.13.7
```

## 🛠️ 故障排除

### 常见问题

1. **"Missing dependencies for SOCKS support"**
   ```bash
   pip install pysocks==1.7.1
   ```

2. **"解密失败"**
   - 检查密码是否正确
   - 确认 `accounts_encrypted.txt` 文件完整

3. **"连接RPC失败"**
   - 检查网络连接
   - 尝试更换代理
   - 检查 RPC 节点状态

4. **"私钥无效"**
   - 检查私钥格式
   - 确认私钥长度正确

### 日志分析
程序会显示详细的日志信息，包括：
- 连接状态
- 交易哈希
- 错误信息
- 余额信息

## 📁 文件结构

```
GIWA-bot/
├── bot.py                    # 主程序
├── run.py                    # 一键运行脚本
├── encrypt_accounts.py       # 私钥加密脚本
├── accounts.txt              # 原始私钥文件
├── accounts_encrypted.txt    # 加密私钥文件
├── proxy.txt                 # 代理配置文件
├── requirements.txt          # 依赖包列表
├── README.md                 # 使用说明
└── ENCRYPTION_GUIDE.md       # 加密使用指南
```

## ⚠️ 安全提醒

1. **私钥安全**: 请妥善保管您的私钥和加密密码
2. **环境安全**: 在安全的计算机环境中运行
3. **备份重要**: 建议备份加密文件和密码
4. **定期更新**: 建议定期更换密码并重新加密

## 📞 支持

如果您遇到问题或有建议，请：
1. 检查本文档的故障排除部分
2. 查看 `ENCRYPTION_GUIDE.md` 了解加密功能
3. 检查日志输出获取详细错误信息

---

**开发者**: ferdie_jhovie  
**版本**: 2.0 (支持私钥加密)  
