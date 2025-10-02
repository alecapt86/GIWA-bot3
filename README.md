# Giwa Testnet Bot - Automated Bridging Assistant

An automation script for the Giwa testnet that supports encrypted private key storage, proxy rotation, and multiple bridging modes.

## ✨ Key Features

- 🔐 **Private key protection** – Encrypt your private keys with a password for additional security.
- 🌐 **Smart proxy detection** – Automatically detects and uses proxies when available.
- 🌉 **Flexible bridging modes** – Supports both Sepolia → Giwa and Giwa → Sepolia bridging.
- 🔄 **Random bridging** – Randomly selects a direction for each run.
- 👥 **Multi-account support** – Process multiple wallets in sequence.
- ⚡ **One-click execution** – Simplified workflow via the launcher script.

## 📋 Requirements

- Python 3.8 or later
- Windows / Linux / macOS
- Stable internet connection

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/sdohuajia/GIWA-bot.git
cd GIWA-bot
```

### 2. Install dependencies
```bash
# Option 1: Install from requirements.txt
pip install -r requirements.txt

# Option 2: Manually add SOCKS support (if you encounter proxy issues)
pip install pysocks==1.7.1
```

### 3. Prepare configuration files

#### 📝 Private keys (`accounts.txt`)
Place one private key per line inside `accounts.txt`:
```text
your_private_key_1
your_private_key_2
your_private_key_3
```

#### 🌐 Proxy list (`proxy.txt`) – Optional
Populate `proxy.txt` if you need a proxy:
```text
# HTTP proxies
http://proxy_ip:port
http://username:password@proxy_ip:port

# SOCKS proxies
socks5://proxy_ip:port
socks5://username:password@proxy_ip:port
```

### 4. Run the bot

#### Option 1: One-click launcher (recommended)
```bash
python run.py
```

#### Option 2: Directly start the bot
```bash
python bot.py
```

#### Option 3: Keep it running in the background (recommended for servers)
```bash
# Install screen if needed
# Ubuntu/Debian: sudo apt install screen
# CentOS/RHEL: sudo yum install screen
# macOS: brew install screen

# Create a new screen session
screen -S giwa-bot

# Run the bot inside the session
python3 run.py

# Detach: press Ctrl+A then D (bot keeps running)
# Reattach: screen -r giwa-bot
# List sessions: screen -ls
# Terminate: screen -S giwa-bot -X quit
```

## 🔐 Private Key Encryption Workflow

### First-time setup – encrypt your keys
1. Place private keys in `accounts.txt`.
2. Run the encryption helper:
   ```bash
   python encrypt_accounts.py
   ```
3. Enter a strong password and confirm it.
4. Wait for the encryption process to finish.

### Running with encrypted keys
1. Start the launcher:
   ```bash
   python run.py
   ```
2. Choose **"1. Auto run"**.
3. Provide the decryption password when prompted.
4. The program decrypts the keys in memory and starts processing.

## 🎯 Detailed Usage Flow

### 1. Launch the program
```bash
python run.py
```

### 2. Choose a mode
The menu displays:
```text
╔══════════════════════════════════════════════════════════════╗
║                    Giwa Testnet One-Click Runner              ║
║                        ferdie_jhovie                        ║
╚══════════════════════════════════════════════════════════════╝

📋 Select an option:
1. Auto run (encrypt + launch bot)
2. Run encryption only
3. Launch bot only
4. Exit
```

### 3. Pick a bridging direction
```text
Select a bridging mode:
1. Sepolia → Giwa
2. Giwa → Sepolia
3. Random direction
```

### 4. Enter parameters
- **Number of bridges** – How many times each account should bridge.
- **ETH amount** – Amount bridged per transaction.
- **Minimum delay** – Minimum wait time between transactions (seconds).
- **Maximum delay** – Maximum wait time between transactions (seconds).

### 5. Proxy handling
The program automatically checks for proxies:
- `proxy.txt` present → proxies will be used.
- `proxy.txt` absent → direct connection.

### 6. Execution steps
The bot will:
1. Load and decrypt keys if required.
2. Detect proxy configuration.
3. Process each account in turn.
4. Print detailed logs for every action.

## 📊 Sample Output

```text
[ 09/13/25 16:15:31 WIB ] | Detected proxy file, running with proxy
[ 09/13/25 16:15:31 WIB ] | Rotate invalid proxy? [y/n] -> y
[ 09/13/25 16:15:31 WIB ] | Total accounts: 3
[ 09/13/25 16:15:31 WIB ] | =========================[ 0x1234...5678 ]=========================
[ 09/13/25 16:15:31 WIB ] |      Route   : Sepolia → Giwa
[ 09/13/25 16:15:31 WIB ] |      Amount  : 0.001 ETH
[ 09/13/25 16:15:31 WIB ] |      Balance : 0.05 ETH
[ 09/13/25 16:15:31 WIB ] |      Status  : Success
[ 09/13/25 16:15:31 WIB ] |      Tx Hash : 0xabcd...efgh
```

## 📦 Dependency Management
If you run into dependency issues, verify versions manually:
```bash
# Check package versions
pip show web3 eth-account

# Reinstall specific versions
pip uninstall web3 eth-account
pip install web3==7.11.1 eth-account==0.13.7
```

## 🖥️ Background Operations
For long-running sessions on servers, `screen` keeps the bot alive.

#### Basic screen commands
```bash
# Create a new session
screen -S giwa-bot

# List sessions
screen -ls

# Reattach to a session
screen -r giwa-bot

# Detach (keep running)
# Inside the session press: Ctrl+A then D

# Terminate a session
screen -S giwa-bot -X quit

# Force-remove dead sessions
screen -wipe
```

#### Automation helper script
Create a `start_bot.sh` script:
```bash
#!/bin/bash
# Check if the giwa-bot session already exists
if screen -list | grep -q "giwa-bot"; then
    echo "giwa-bot session found, reconnecting..."
    screen -r giwa-bot
else
    echo "Starting a new giwa-bot session..."
    screen -S giwa-bot python3 run.py
fi
```

## 🛠️ Troubleshooting

### Common issues

1. **"Missing dependencies for SOCKS support"**
   ```bash
   pip install pysocks==1.7.1
   ```

2. **"Decryption failed"**
   - Verify the password.
   - Ensure `accounts_encrypted.txt` is intact.

3. **"Unable to connect to RPC"**
   - Check your internet connection.
   - Try another proxy.
   - Confirm the RPC endpoint status.

4. **"Invalid private key"**
   - Confirm the key format.
   - Ensure the key length is correct.

### Log insights
The console output includes:
- Connection state
- Transaction hashes
- Error details
- Balance updates

## 📁 Project Structure

```text
GIWA-bot/
├── bot.py                    # Main bot logic
├── run.py                    # One-click launcher
├── encrypt_accounts.py       # Private key encryption helper
├── accounts.txt              # Plaintext private keys (deleted after encryption)
├── accounts_encrypted.txt    # Encrypted private keys
├── proxy.txt                 # Proxy configuration
├── requirements.txt          # Dependency list
├── README.md                 # This guide
└── ENCRYPTION_GUIDE.md       # Detailed encryption instructions
```

## ⚠️ Security Tips

1. **Protect your secrets** – Keep both passwords and private keys safe.
2. **Use a secure environment** – Run the bot on trusted machines only.
3. **Back up critical data** – Store encrypted files and passwords securely.
4. **Rotate credentials periodically** – Re-encrypt with new passwords from time to time.

## 📞 Support

If you need help:
1. Review the troubleshooting section above.
2. Read `ENCRYPTION_GUIDE.md` for encryption details.
3. Inspect the console logs for precise error messages.

---

**Maintainer**: ferdie_jhovie  
**Version**: 2.0 (private key encryption supported)
