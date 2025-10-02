# Giwa Testnet Bot – Private Key Encryption Guide

## Overview
To keep your wallets secure, the bot supports encrypting private keys. Encrypted keys are stored in `accounts_encrypted.txt` and require your password to decrypt when the bot runs.

## Step-by-step instructions

### 1. Install dependencies
```bash
# Option 1: install everything from requirements.txt
pip install -r requirements.txt

# Option 2: run the helper installer (recommended)
python install_dependencies.py

# Option 3: manually add SOCKS support
pip install pysocks==1.7.1
```

### 2. Prepare the private key file
Place each private key on its own line in `accounts.txt`:
```text
your_private_key_1
your_private_key_2
your_private_key_3
```

### 3. Encrypt the keys
Run the encryption utility:
```bash
python encrypt_accounts.py
```

Follow the prompts:
- Enter an encryption password (store it safely).
- Confirm the password.
- Wait for the encryption process to finish.

After encryption completes:
- The original `accounts.txt` file is removed automatically.
- A new encrypted file `accounts_encrypted.txt` is created.

### 4. Run the bot
```bash
python bot.py
```

The program will:
- Detect the encrypted file.
- Ask for the decryption password.
- Decrypt the keys in memory and continue as normal.

## Security highlights

1. **Strong encryption** – PBKDF2 + Fernet provide hardened protection.
2. **Random salt** – Every encryption run uses a unique salt.
3. **Password required** – Private keys cannot be recovered without the password.
4. **In-memory safety** – Decrypted keys only exist temporarily in memory.

## File reference

- `accounts.txt`: plaintext private keys (removed after encryption).
- `accounts_encrypted.txt`: encrypted private keys.
- `encrypt_accounts.py`: CLI helper for encryption and decryption.

## Best practices

1. **Use a strong password** and store it securely.
2. **Create backups** of the encrypted file and your password.
3. **Rotate passwords periodically** and re-encrypt when needed.
4. **Work on a trusted machine** to avoid malware risks.
5. **Remember the deletion step** – the script removes the plaintext file after encryption.

## Troubleshooting

### Decryption failed
- Recheck the password.
- Confirm that `accounts_encrypted.txt` is intact.
- Re-run the encryption tool if necessary.

### File not found
- Ensure `accounts_encrypted.txt` exists.
- If it does not, the bot will fall back to `accounts.txt` if available.

## Restoring plaintext keys
If you need to recover your original keys:
1. Run `python encrypt_accounts.py`.
2. Enter the correct password.
3. The program displays the decrypted keys.
4. Manually copy them into a new `accounts.txt` file.
