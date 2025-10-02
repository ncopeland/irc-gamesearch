#!/usr/bin/env python3
"""
IRC Game Search Bot
A bot that searches for games using the IGDB API and responds to IRC commands.

Copyright (C) 2025  Boliver

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
"""

import socket
import ssl
import time
import threading
import configparser
import re
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Optional, Tuple
import logging

class IRCGameBot:
    def __init__(self, config_file: str = "irc-gamebot.conf"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('irc_gamebot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # IRC settings
        self.server = self.config.get('DEFAULT', 'server').split('/')[0]
        self.port = int(self.config.get('DEFAULT', 'server').split('/')[1]) if '/' in self.config.get('DEFAULT', 'server') else 6667
        self.ssl_enabled = self.config.getboolean('DEFAULT', 'ssl')
        self.bot_nick = self.config.get('DEFAULT', 'bot_nick').split(',')[0]
        self.bot_alt_nick = self.config.get('DEFAULT', 'bot_nick').split(',')[1] if ',' in self.config.get('DEFAULT', 'bot_nick') else None
        self.channels = [ch.strip() for ch in self.config.get('DEFAULT', 'channel').split(',')]
        self.perform = self.config.get('DEFAULT', 'perform', fallback='')
        self.owner = self.config.get('DEFAULT', 'owner')
        self.admins = [admin.strip() for admin in self.config.get('DEFAULT', 'admin').split(',')]
        
        # IGDB API settings
        self.igdb_client_id = self.config.get('IGDB', 'client_id', fallback='')
        self.igdb_client_secret = self.config.get('IGDB', 'client_secret', fallback='')
        self.igdb_access_token = self.config.get('IGDB', 'access_token', fallback='')
        
        # Get access token if we have client credentials but no token
        if self.igdb_client_id and self.igdb_client_secret and not self.igdb_access_token:
            self.igdb_access_token = self.get_igdb_access_token()
        
        # Bot state
        self.socket = None
        self.running = False
        self.connected = False
        
        # Rate limiting
        self.last_message_time = 0
        self.message_delay = self.config.getfloat('DEFAULT', 'message_delay', fallback=1.0)  # seconds between messages
        
    def connect(self):
        """Connect to IRC server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if self.ssl_enabled:
                context = ssl.create_default_context()
                self.socket = context.wrap_socket(self.socket, server_hostname=self.server)
            
            self.socket.connect((self.server, self.port))
            self.connected = True
            self.logger.info(f"Connected to {self.server}:{self.port}")
            
            # Send initial IRC commands
            self.send(f"USER {self.bot_nick} 0 * :{self.bot_nick}")
            self.send(f"NICK {self.bot_nick}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise
    
    def send(self, message: str):
        """Send message to IRC server with rate limiting"""
        if self.socket:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_message_time
            if time_since_last < self.message_delay:
                sleep_time = self.message_delay - time_since_last
                time.sleep(sleep_time)
            
            self.socket.send(f"{message}\r\n".encode('utf-8'))
            self.last_message_time = time.time()
            self.logger.debug(f"SENT: {message}")
    
    def send_privmsg(self, target: str, message: str):
        """Send private message"""
        self.send(f"PRIVMSG {target} :{message}")
    
    def join_channel(self, channel: str):
        """Join IRC channel"""
        if not channel.startswith('#'):
            channel = '#' + channel
        self.send(f"JOIN {channel}")
        self.logger.info(f"Joined channel: {channel}")
        
        # Update config file
        if channel not in self.channels:
            self.channels.append(channel)
            self.update_config_channels()
    
    def part_channel(self, channel: str):
        """Leave IRC channel"""
        if not channel.startswith('#'):
            channel = '#' + channel
        self.send(f"PART {channel}")
        self.logger.info(f"Left channel: {channel}")
        
        # Update config file
        if channel in self.channels:
            self.channels.remove(channel)
            self.update_config_channels()
    
    def update_config_channels(self):
        """Update the channels list in the config file"""
        try:
            # Update the config object
            self.config.set('DEFAULT', 'channel', ','.join(self.channels))
            
            # Write to file
            with open('irc-gamebot.conf', 'w') as configfile:
                self.config.write(configfile)
            
            self.logger.info(f"Updated config file with channels: {', '.join(self.channels)}")
        except Exception as e:
            self.logger.error(f"Failed to update config file: {e}")
    
    def is_admin(self, nick: str) -> bool:
        """Check if user is admin or owner"""
        return nick.lower() in [admin.lower() for admin in self.admins] or nick.lower() == self.owner.lower()
    
    def is_owner(self, nick: str) -> bool:
        """Check if user is owner"""
        return nick.lower() == self.owner.lower()
    
    def get_igdb_access_token(self) -> str:
        """Get IGDB access token using client credentials"""
        try:
            url = "https://id.twitch.tv/oauth2/token"
            data = {
                'client_id': self.igdb_client_id,
                'client_secret': self.igdb_client_secret,
                'grant_type': 'client_credentials'
            }
            
            request = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode('utf-8'))
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(request) as response:
                token_data = json.loads(response.read().decode('utf-8'))
                access_token = token_data.get('access_token')
                
                if access_token:
                    self.logger.info("Successfully obtained IGDB access token")
                    return access_token
                else:
                    self.logger.error("Failed to get access token from IGDB")
                    return ""
                    
        except Exception as e:
            self.logger.error(f"Error getting IGDB access token: {e}")
            return ""
    
    def parse_game_command(self, message: str) -> Tuple[str, Dict[str, List[str]]]:
        """Parse !game command and extract search terms and filters"""
        # Remove !game prefix
        content = message[5:].strip()
        
        # Parse filters
        filters = {}
        search_terms = []
        
        # Split by common filter patterns
        parts = re.split(r'\s+--(years?|platform|p)\s+', content, flags=re.IGNORECASE)
        
        if len(parts) >= 3:
            search_terms = parts[0].strip().split()
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    filter_type = parts[i].lower()
                    filter_values = [v.strip() for v in parts[i + 1].split(',')]
                    
                    if filter_type in ['year', 'years']:
                        filters['years'] = filter_values
                    elif filter_type in ['platform', 'p']:
                        filters['platforms'] = filter_values
        else:
            search_terms = content.split()
        
        return ' '.join(search_terms), filters
    
    def search_games_igdb(self, query: str, filters: Dict[str, List[str]] = None) -> List[Dict]:
        """Search for games using IGDB API"""
        if not self.igdb_client_id or not self.igdb_access_token:
            return [{"error": "IGDB API credentials not configured"}]
        
        try:
            # Build search query
            search_query = f'search "{query}"; fields name,summary,first_release_date,platforms.name,rating,url; limit 5;'
            
            # Add year filters if specified
            if filters and 'years' in filters:
                year_conditions = []
                for year_range in filters['years']:
                    if '-' in year_range:
                        start_year, end_year = year_range.split('-')
                        year_conditions.append(f'first_release_date >= {start_year}0101 & first_release_date <= {end_year}1231')
                    else:
                        year_conditions.append(f'first_release_date >= {year_range}0101 & first_release_date <= {year_range}1231')
                
                if year_conditions:
                    search_query = f'search "{query}"; fields name,summary,first_release_date,platforms.name,rating,url; where {" | ".join(year_conditions)}; limit 5;'
            
            # Make API request
            url = "https://api.igdb.com/v4/games"
            headers = {
                'Client-ID': self.igdb_client_id,
                'Authorization': f'Bearer {self.igdb_access_token}',
                'Content-Type': 'text/plain'
            }
            
            request = urllib.request.Request(url, data=search_query.encode('utf-8'), headers=headers)
            
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
                
        except urllib.error.HTTPError as e:
            self.logger.error(f"IGDB API HTTP error: {e}")
            return [{"error": f"API error: {e.code}"}]
        except Exception as e:
            self.logger.error(f"IGDB API error: {e}")
            return [{"error": f"Search failed: {str(e)}"}]
    
    def format_game_result(self, game: Dict) -> str:
        """Format game search result for IRC"""
        if "error" in game:
            return f"Error: {game['error']}"
        
        name = game.get('name', 'Unknown')
        rating = game.get('rating', 0)
        year = game.get('first_release_date', 0)
        url = game.get('url', '')
        
        # Format year
        year_str = ""
        if year:
            year_str = f" ({year // 10000})"
        
        # Format rating
        rating_str = ""
        if rating:
            rating_str = f" | Rating: {rating:.1f}/100"
        
        # Format platforms
        platforms = game.get('platforms', [])
        platform_str = ""
        if platforms:
            platform_names = [p.get('name', '') for p in platforms if isinstance(p, dict)]
            if platform_names:
                platform_str = f" | Platforms: {', '.join(platform_names[:3])}"
        
        result = f"{name}{year_str}{rating_str}{platform_str}"
        if url:
            result += f" | {url}"
        
        return result
    
    def handle_message(self, message: str):
        """Handle incoming IRC message"""
        parts = message.split()
        if len(parts) < 3:
            return
        
        # Parse IRC message
        if parts[1] == "PRIVMSG":
            target = parts[2]
            content = ' '.join(parts[3:])[1:]  # Remove leading ':'
            
            # Extract sender
            sender = parts[0].split('!')[0][1:] if parts[0].startswith(':') else ""
            
            # Handle channel messages
            if target.startswith('#'):
                if content.startswith('!game '):
                    self.logger.info(f"Game search request from {sender} in {target}: {content}")
                    query, filters = self.parse_game_command(content)
                    
                    if query:
                        results = self.search_games_igdb(query, filters)
                        if results and len(results) > 0:
                            if "error" in results[0]:
                                self.send_privmsg(target, f"Search failed: {results[0]['error']}")
                            else:
                                self.send_privmsg(target, f"Found {len(results)} game(s) for '{query}':")
                                for i, game in enumerate(results[:3], 1):  # Show top 3
                                    formatted = self.format_game_result(game)
                                    self.send_privmsg(target, f"{i}. {formatted}")
                        else:
                            self.send_privmsg(target, f"No games found for '{query}'")
                    else:
                        self.send_privmsg(target, "Usage: !game <search term> [--years YYYY-YYYY] [--platform platform1,platform2]")
            
            # Handle private messages (admin commands)
            elif target == self.bot_nick:
                if self.is_admin(sender):
                    if content == "!restart" and self.is_owner(sender):
                        self.send_privmsg(sender, "Restarting bot...")
                        self.running = False
                        return
                    
                    elif content.startswith("!join "):
                        channel = content[6:].strip()
                        self.join_channel(channel)
                        self.send_privmsg(sender, f"Joined {channel}")
                    
                    elif content.startswith("!part "):
                        channel = content[6:].strip()
                        self.part_channel(channel)
                        self.send_privmsg(sender, f"Left {channel}")
                    
                    elif content == "!help":
                        help_msg = "Admin commands: !restart (owner only), !join #channel, !part #channel, !help"
                        self.send_privmsg(sender, help_msg)
    
    def run(self):
        """Main bot loop"""
        try:
            self.connect()
            self.running = True
            
            # Wait for registration to complete and MOTD
            registration_complete = False
            motd_complete = False
            
            # Main message loop
            while self.running:
                try:
                    data = self.socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    for line in data.strip().split('\r\n'):
                        if line:
                            self.logger.info(f"RECV: {line}")
                            
                            # Handle PING
                            if line.startswith('PING'):
                                self.send(f"PONG {line[5:]}")
                            
                            # Check for successful registration
                            elif "001" in line or "Welcome" in line:
                                registration_complete = True
                                self.logger.info("Successfully registered with IRC server")
                            
                            # Check for end of MOTD
                            elif "376" in line or "422" in line:  # End of MOTD or No MOTD
                                motd_complete = True
                                self.logger.info("MOTD complete, joining channels...")
                                
                                # Now join channels
                                for channel in self.channels:
                                    self.join_channel(channel)
                                    time.sleep(1)
                                
                                # Send perform commands
                                if self.perform:
                                    # Split by semicolon and send each command
                                    commands = [cmd.strip() for cmd in self.perform.split(';') if cmd.strip()]
                                    for cmd in commands:
                                        self.send(cmd)
                            
                            # Handle error messages
                            elif "433" in line:  # Nickname already in use
                                self.logger.warning("Nickname in use, trying alternative...")
                                if self.bot_alt_nick and self.bot_nick == self.bot_alt_nick:
                                    # Try with random number
                                    import random
                                    new_nick = f"{self.bot_nick}{random.randint(100, 999)}"
                                    self.send(f"NICK {new_nick}")
                                    self.bot_nick = new_nick
                                elif self.bot_alt_nick:
                                    self.send(f"NICK {self.bot_alt_nick}")
                                    self.bot_nick = self.bot_alt_nick
                                else:
                                    # Try with random number
                                    import random
                                    new_nick = f"{self.bot_nick}{random.randint(100, 999)}"
                                    self.send(f"NICK {new_nick}")
                                    self.bot_nick = new_nick
                            
                            elif "451" in line:  # Not registered
                                self.logger.warning("Not registered, retrying...")
                                self.send(f"USER {self.bot_nick} 0 * :{self.bot_nick}")
                                self.send(f"NICK {self.bot_nick}")
                            
                            # Handle other messages
                            else:
                                self.handle_message(line)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    break
        
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Bot error: {e}")
        finally:
            self.disconnect()
    
    def disconnect(self):
        """Disconnect from IRC server"""
        if self.socket:
            self.send("QUIT :Bot shutting down")
            self.socket.close()
            self.connected = False
            self.logger.info("Disconnected from IRC server")

def main():
    """Main entry point"""
    bot = IRCGameBot()
    bot.run()

if __name__ == "__main__":
    main()
