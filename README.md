# GATA Registration Bot

A Python bot for automating GATA registration process.

## Project Link
- Website: [GATA Chat](https://app.gata.xyz/chat)
- Invite Code: `ngzxbox8`

## Features
- Automated wallet creation
- Proxy support
- Multi-threaded registration
- Automatic nonce signing
- Error handling and retries
- Detailed logging

## Requirements
- Python 3.8+
- Required packages (see `requirements.txt`)

## Installation

1. Clone the repository or download the files
2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Prepare your proxy list:
   - Create a file named `proxies.txt`
   - Add your proxies one per line
   - Supported formats:
     - `http://ip:port`
     - `http://username:password@ip:port`

2. Run the bot:
```bash
python bot.py
```

3. Follow the menu options:
   - Select "Start Registration"
   - Enter the invite code when prompted
   - The bot will automatically start the registration process

## Output Files
- `bot.log`: Detailed logging information
- `successful_accounts.txt`: Successfully registered accounts with tokens
- `wallets.txt`: Created wallet addresses and private keys

## Notes
- Make sure you have a stable internet connection
- Use reliable proxies for better success rate
- Check the log file for detailed information about the registration process
- The bot includes automatic retries and error handling

## Disclaimer
This bot is for educational purposes only. Use at your own risk and ensure compliance with the platform's terms of service. 
