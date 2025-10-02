# IRC Game Search Bot

An IRC bot that searches for games using the IGDB API and responds to channel commands.

## Features

- **Game Search**: Responds to `!game <search term>` in channels
- **Advanced Filtering**: Support for year ranges and platform filters
  - `!game Pokemon --years 2005-2008,2010 --platform n64,gameboy`
- **Admin Commands**: Private message commands for bot management
  - `!restart` (owner only)
  - `!join #channel` (admin/owner)
  - `!part #channel` (admin/owner)
  - `!help` (admin/owner)
- **Multi-channel Support**: Can join multiple channels
- **SSL Support**: Optional SSL connection to IRC servers
- **Comprehensive Logging**: Both file and console logging

## Setup

1. **Install Python 3.6+** (uses only standard library)

2. **Get IGDB API Credentials**:
   - Visit https://api-docs.igdb.com/
   - Create an account and get your Client ID and Access Token
   - Update `irc-gamebot.conf` with your credentials

3. **Configure the bot**:
   - Edit `irc-gamebot.conf` with your IRC server details
   - Set your bot nickname, channels, owner, and admins
   - Configure the perform command if needed

4. **Run the bot**:
   ```bash
   python3 irc_gamebot.py
   ```

## Configuration

The bot uses `irc-gamebot.conf` for configuration:

```ini
[DEFAULT]
server = irc.rizon.net/6667
ssl = off
bot_nick = GameSearchBot,GameSearch
channel = #devforge.games,#ireland
perform = PRIVMSG Boliver :I am here
owner = Boliver
admin = TorS

[IGDB]
client_id = your_client_id_here
access_token = your_access_token_here
```

## Usage

### Channel Commands

- `!game <search term>` - Search for games
- `!game Pokemon --years 2005-2008,2010` - Search with year filter
- `!game Pokemon --platform n64,gameboy` - Search with platform filter
- `!game Pokemon --years 2005-2008 --platform n64` - Combined filters

### Private Message Commands (Admin/Owner)

- `!restart` - Restart the bot (owner only)
- `!join #channel` - Join a channel
- `!part #channel` - Leave a channel
- `!help` - Show available commands

## IGDB API Integration

The bot uses the IGDB API v4 to search for games. It returns:
- Game name and release year
- Rating (if available)
- Platforms (if available)
- Direct link to the game on IGDB

## Logging

The bot logs to both `irc_gamebot.log` file and console with timestamps and different log levels.

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)
- Valid IGDB API credentials
