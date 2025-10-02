# IRC Game Search Bot

An IRC bot that searches for games using the IGDB API and responds to channel commands.

Copyright (C) 2025 Boliver

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

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
- **Multiple Perform Commands**: Support for multiple IRC commands on connect (separated by semicolons)
- **Rate Limiting**: Configurable message delay to prevent flooding
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
   # Using the control script (recommended)
   ./gamebot.sh start
   
   # Or run directly
   python3 irc_gamebot.py
   ```

## Control Script

The included `gamebot.sh` script provides easy bot management:

```bash
./gamebot.sh start    # Start the bot
./gamebot.sh stop     # Stop the bot
./gamebot.sh status   # Show bot status and recent logs
./gamebot.sh restart  # Restart the bot
```

The script handles:
- Process management with PID files
- Graceful shutdown (SIGTERM then SIGKILL)
- Status checking and process info
- Log file management
- Error handling and colored output

## Configuration

The bot uses `irc-gamebot.conf` for configuration:

```ini
[DEFAULT]
server = irc.rizon.net/6667
ssl = off
bot_nick = GameSearchBot,GameSearch
channel = #devforge.games,#ireland
perform = PRIVMSG nickserv :identify password ; PRIVMSG Boliver :I am here
owner = Boliver
admin = TorS
message_delay = 1.0

[IGDB]
client_id = your_client_id_here
client_secret = your_client_secret_here
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
