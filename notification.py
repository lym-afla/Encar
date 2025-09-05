import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import List, Dict
import yaml
import time
import html
import os
import re
from dotenv import load_dotenv

class NotificationManager:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize notification manager with configuration."""
        # Load environment variables first
        load_dotenv()
        
        # Read config file
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # Replace environment variable placeholders
        config_content = self._substitute_env_vars(config_content)
        
        # Parse the config
        self.config = yaml.safe_load(config_content)
        
        self.notification_config = self.config['notifications']
        
        # Set up logging for file notifications
        if 'file' in self.notification_config['methods']:
            self.setup_file_logging()
        
        # Initialize Telegram rate limiting
        self.telegram_message_times = []
        self.last_telegram_error = None

    def _substitute_env_vars(self, config_content: str) -> str:
        """Replace ${VARIABLE_NAME} placeholders with environment variables."""
        def replace_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                print(f"Warning: Environment variable {var_name} not found, keeping placeholder")
                return match.group(0)  # Return original placeholder
            return env_value
        
        # Pattern to match ${VARIABLE_NAME}
        pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
        return re.sub(pattern, replace_var, config_content)
    
    def setup_file_logging(self):
        """Set up file logging for notifications."""
        log_file = self.notification_config['log_file']
        
        # Create file handler for notifications
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - [ENCAR ALERT] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Create logger for notifications
        self.alert_logger = logging.getLogger('encar_alerts')
        self.alert_logger.setLevel(logging.INFO)
        self.alert_logger.addHandler(file_handler)
        
        # Prevent duplicate logs in main logger
        self.alert_logger.propagate = False
    
    def send_new_listing_alert(self, listing: Dict):
        """Send alert for a single new listing."""
        if not self.notification_config['enabled']:
            return
        
        message = self.format_listing_message(listing)
        
        # Send via configured methods
        for method in self.notification_config['methods']:
            if method == 'console':
                self.send_console_alert(message)
            elif method == 'file':
                self.send_file_alert(message)
            elif method == 'telegram':
                # Handle both sync and async contexts
                try:
                    # Try to create task if we're in an async context
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(self.send_telegram_alert(message))
                except RuntimeError:
                    # No running loop, create new one
                    asyncio.run(self.send_telegram_alert(message))
            elif method == 'telegram':
                # Handle both sync and async contexts
                try:
                    # Try to create task if we're in an async context
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(self.send_telegram_alert(message))
                except RuntimeError:
                    # No running loop, create new one
                    asyncio.run(self.send_telegram_alert(message))
    
    def send_batch_alert(self, new_listings: List[Dict], summary_stats: Dict = None):
        """Send alert for multiple new listings with enhanced formatting."""
        if not self.notification_config['enabled'] or not new_listings:
            return
        
        # Create batch message with enhanced information
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"\n{'='*60}\n"
        message += f"🚗 NEW ENCAR LISTINGS ALERT - {timestamp}\n"
        message += f"{'='*60}\n"
        message += f"Found {len(new_listings)} truly new GLE Coupe listing(s)!\n\n"
        
        # Add each listing with enhanced details
        for i, listing in enumerate(new_listings, 1):
            message += f"[{i}] {self.format_listing_summary_enhanced(listing)}\n"
        
        # Add enhanced summary stats
        if summary_stats:
            message += f"\n📊 Monitoring Summary:\n"
            message += f"   • Total listings scanned: {summary_stats.get('total_checked', 'N/A')}\n"
            message += f"   • Coupe listings found: {summary_stats.get('coupe_count', 'N/A')}\n"
            message += f"   • Truly new listings: {summary_stats.get('truly_new', 'N/A')}\n"
            message += f"   • Recent registrations (7d): {summary_stats.get('recent_registrations', 'N/A')}\n"
            message += f"   • Monitoring cycle: #{summary_stats.get('cycle_number', 'N/A')}\n"
        
        message += f"\n{'='*60}\n"
        
        # Send via configured methods
        for method in self.notification_config['methods']:
            if method == 'console':
                self.send_console_alert(message)
            elif method == 'file':
                self.send_file_alert(message)
            elif method == 'telegram':
                # Handle both sync and async contexts
                try:
                    # Try to create task if we're in an async context
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(self.send_telegram_alert(message))
                except RuntimeError:
                    # No running loop, create new one
                    asyncio.run(self.send_telegram_alert(message))
    
    def format_listing_message(self, listing: Dict) -> str:
        """Format a single listing for notification with enhanced details."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"\n🚗 NEW LISTING ALERT - {timestamp}\n"
        message += f"{'='*50}\n"
        message += f"Model: {listing['title']}\n"
        
        if listing.get('year'):
            message += f"Year: {listing['year']}\n"
        
        message += f"Price: {listing['price']}\n"
        message += f"Mileage: {listing['mileage']}\n"
        message += f"Views: {listing['views']}"
        
        # Add freshness indicator
        if listing.get('views', 0) <= 10:
            message += " (🔥 VERY FRESH!)\n"
        elif listing.get('views', 0) <= 50:
            message += " (✨ Fresh)\n"
        else:
            message += "\n"
        
        # Add registration information
        if listing.get('registration_date'):
            message += f"Registration: {listing['registration_date']}"
            
            # Add days since registration if available
            if listing.get('days_since_registration') is not None:
                days = listing['days_since_registration']
                if days <= 7:
                    message += f" ({days} days ago - 🆕 RECENT!)\n"
                elif days <= 30:
                    message += f" ({days} days ago)\n"
                else:
                    message += f" ({days} days ago)\n"
            else:
                message += "\n"
        
        # Add database status
        if listing.get('is_truly_new'):
            message += "Status: 🎯 Truly New Listing\n"
        
        message += f"URL: {listing['listing_url']}\n"
        message += f"Car ID: {listing['car_id']}\n"
        message += f"{'='*50}\n"
        
        return message
    
    def format_listing_summary_enhanced(self, listing: Dict) -> str:
        """Format a listing summary for batch notifications with enhanced information."""
        summary = f"{listing['title']}"
        
        if listing.get('year'):
            summary += f" ({listing['year']})"
        
        summary += f" - {listing['price']}"
        
        # Add view count with freshness indicator
        views = listing.get('views', 0)
        if views <= 10:
            summary += f" - {views} views 🔥"
        elif views <= 50:
            summary += f" - {views} views ✨"
        else:
            summary += f" - {views} views"
        
        # Add registration information
        if listing.get('registration_date'):
            summary += f" - Reg: {listing['registration_date']}"
            
            # Add recency indicator
            if listing.get('days_since_registration') is not None:
                days = listing['days_since_registration']
                if days <= 7:
                    summary += f" ({days}d 🆕)"
                elif days <= 30:
                    summary += f" ({days}d)"
        
        # Add truly new indicator
        if listing.get('is_truly_new'):
            summary += " 🎯"
        
        summary += f"\n    URL: {listing['listing_url']}"
        
        return summary
    
    def send_console_alert(self, message: str):
        """Send alert to console."""
        print(message)
    
    def send_file_alert(self, message: str):
        """Send alert to log file."""
        if hasattr(self, 'alert_logger'):
            # Remove the timestamp from the message since logger adds its own
            clean_message = message.replace('\n', ' | ').strip()
            self.alert_logger.info(clean_message)
    
    def is_telegram_enabled(self) -> bool:
        """Check if Telegram notifications are enabled and configured."""
        if 'telegram' not in self.notification_config:
            return False
        
        telegram_config = self.notification_config['telegram']
        return (telegram_config.get('enabled', False) and 
                telegram_config.get('bot_token') and 
                telegram_config.get('chat_id') and
                telegram_config.get('bot_token') != 'YOUR_BOT_TOKEN_HERE' and
                telegram_config.get('chat_id') != 'YOUR_CHAT_ID_HERE')
    
    def can_send_telegram_message(self) -> bool:
        """Check if we can send a Telegram message (rate limiting)."""
        if not self.is_telegram_enabled():
            return False
        
        telegram_config = self.notification_config['telegram']
        max_per_minute = telegram_config.get('max_messages_per_minute', 20)
        
        # Clean old message times (older than 1 minute)
        cutoff_time = time.time() - 60
        self.telegram_message_times = [t for t in self.telegram_message_times if t > cutoff_time]
        
        # Check if we're under the rate limit
        return len(self.telegram_message_times) < max_per_minute
    
    async def send_telegram_alert(self, message: str):
        """Send alert via Telegram bot."""
        try:
            if not self.can_send_telegram_message():
                print("⚠️ Telegram rate limit reached, skipping message")
                return
            
            telegram_config = self.notification_config['telegram']
            bot_token = telegram_config['bot_token']
            chat_id = telegram_config['chat_id']
            parse_mode = telegram_config.get('parse_mode', 'HTML')
            timeout = telegram_config.get('message_timeout', 30)
            
            # Format message for Telegram
            telegram_message = self.format_telegram_message(message)
            
            # Telegram API URL
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            # Prepare payload
            payload = {
                'chat_id': chat_id,
                'text': telegram_message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': telegram_config.get('disable_web_page_preview', False)
            }
            
            # Send message
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=timeout) as response:
                    if response.status == 200:
                        # Record successful send time
                        self.telegram_message_times.append(time.time())
                        self.last_telegram_error = None
                        print("✅ Telegram message sent successfully")
                    else:
                        error_text = await response.text()
                        error_msg = f"Telegram API error {response.status}: {error_text}"
                        print(f"❌ {error_msg}")
                        self.last_telegram_error = error_msg
                        
        except asyncio.TimeoutError:
            error_msg = "Telegram message timeout"
            print(f"❌ {error_msg}")
            self.last_telegram_error = error_msg
        except Exception as e:
            error_msg = f"Telegram error: {str(e)}"
            print(f"❌ {error_msg}")
            self.last_telegram_error = error_msg
    
    def format_telegram_message(self, message: str) -> str:
        """Format message for Telegram with HTML formatting."""
        # Convert text message to Telegram HTML format
        telegram_msg = message
        
        # Replace common formatting
        telegram_msg = telegram_msg.replace("🚗 NEW LISTING ALERT", "<b>🚗 NEW LISTING ALERT</b>")
        telegram_msg = telegram_msg.replace("🚗 NEW ENCAR LISTINGS ALERT", "<b>🚗 NEW ENCAR LISTINGS ALERT</b>")
        telegram_msg = telegram_msg.replace("📊 ENHANCED ENCAR MONITORING SUMMARY", "<b>📊 ENHANCED ENCAR MONITORING SUMMARY</b>")
        telegram_msg = telegram_msg.replace("🔒 Closure Scan Results", "<b>🔒 Closure Scan Results</b>")
        
        # Format field labels
        telegram_msg = telegram_msg.replace("Model:", "<b>Model:</b>")
        telegram_msg = telegram_msg.replace("Year:", "<b>Year:</b>") 
        telegram_msg = telegram_msg.replace("Price:", "<b>Price:</b>")
        telegram_msg = telegram_msg.replace("Mileage:", "<b>Mileage:</b>")
        telegram_msg = telegram_msg.replace("Views:", "<b>Views:</b>")
        telegram_msg = telegram_msg.replace("Registration:", "<b>Registration:</b>")
        telegram_msg = telegram_msg.replace("Status:", "<b>Status:</b>")
        telegram_msg = telegram_msg.replace("URL:", "<b>URL:</b>")
        telegram_msg = telegram_msg.replace("Car ID:", "<b>Car ID:</b>")
        
        # Format special indicators
        telegram_msg = telegram_msg.replace("🔥 VERY FRESH!", "<b>🔥 VERY FRESH!</b>")
        telegram_msg = telegram_msg.replace("✨ Fresh", "<b>✨ Fresh</b>")
        telegram_msg = telegram_msg.replace("🆕 RECENT!", "<b>🆕 RECENT!</b>")
        telegram_msg = telegram_msg.replace("🎯 Truly New Listing", "<b>🎯 Truly New Listing</b>")
        
        # Escape any remaining HTML
        telegram_msg = html.escape(telegram_msg, quote=False)
        
        # Restore our HTML tags
        telegram_msg = telegram_msg.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        
        # Limit message length (Telegram has 4096 character limit)
        if len(telegram_msg) > 4000:
            telegram_msg = telegram_msg[:3990] + "\n\n... (truncated)"
        
        return telegram_msg
    
    def send_monitoring_status(self, status: str, details: str = "", send_to_telegram: bool = False):
        """Send monitoring status update with enhanced formatting."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format status with appropriate emoji
        status_emoji = {
            'STARTING': '🚀',
            'STARTED': '✅',
            'STOPPED': '🛑',
            'INITIAL_POPULATION': '📥',
            'POPULATION_COMPLETE': '✅',
            'ERROR': '❌',
            'Daily Summary': '📊'
        }
        
        emoji = status_emoji.get(status, '📊')
        
        if status == "Daily Summary" and details:
            # For daily summary, use the details as the main message
            message = details
        else:
            message = f"[{timestamp}] {emoji} MONITOR STATUS: {status}\n"
            if details:
                message += f" - {details}"
        
        # Send to console for all status updates
        if 'console' in self.notification_config['methods']:
            print(message)
        
        # Send to Telegram if requested and configured
        if send_to_telegram and 'telegram' in self.notification_config['methods']:
            try:
                # Try to create task if we're in an async context
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.send_telegram_alert(message))
            except RuntimeError:
                # No running loop, create new one
                asyncio.run(self.send_telegram_alert(message))
    
    def send_error_alert(self, error_message: str, context: str = ""):
        """Send error notification."""
        if not self.notification_config['enabled']:
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"\n❌ ENCAR MONITOR ERROR - {timestamp}\n"
        message += f"{'='*50}\n"
        message += f"Error: {error_message}\n"
        
        if context:
            message += f"Context: {context}\n"
        
        message += f"{'='*50}\n"
        
        # Send via all configured methods for errors
        for method in self.notification_config['methods']:
            if method == 'console':
                self.send_console_alert(message)
            elif method == 'file':
                self.send_file_alert(f"ERROR: {error_message} | Context: {context}")
    
    def create_enhanced_summary(self, stats: Dict) -> str:
        """Create an enhanced daily summary report with new architecture data."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        summary = f"\n📈 ENHANCED ENCAR MONITORING SUMMARY - {timestamp}\n"
        summary += f"{'='*70}\n"
        
        # System stats
        summary += f"🔍 System Performance:\n"
        summary += f"   • Total monitoring cycles: {stats.get('total_cycles', 0)}\n"
        summary += f"   • System uptime: {stats.get('uptime', 'N/A')}\n"
        summary += f"   • Last successful check: {stats.get('last_check', 'N/A')}\n"
        
        # Database stats
        summary += f"\n📊 Database Statistics:\n"
        summary += f"   • Total listings tracked: {stats.get('total_listings', 0)}\n"
        summary += f"   • Coupe listings: {stats.get('coupe_listings', 0)}\n"
        summary += f"   • Truly new listings: {stats.get('truly_new_listings', 0)}\n"
        summary += f"   • Recent registrations (7 days): {stats.get('recent_registrations', 0)}\n"
        summary += f"   • Low view listings: {stats.get('low_view_listings', 0)}\n"
        
        if stats.get('avg_registration_age_days'):
            summary += f"   • Average registration age: {stats['avg_registration_age_days']} days\n"
        
        # Discovery stats
        summary += f"\n🚗 Discovery Performance:\n"
        summary += f"   • New listings found today: {stats.get('new_listings_found', 0)}\n"
        
        # Performance indicators
        if stats.get('coupe_listings', 0) > 0:
            new_ratio = (stats.get('truly_new_listings', 0) / stats.get('coupe_listings', 1)) * 100
            summary += f"   • New listing ratio: {new_ratio:.1f}%\n"
        
        if stats.get('recent_registrations', 0) > 0:
            summary += f"   • Recent registration activity: {'🔥 High' if stats['recent_registrations'] > 5 else '📊 Normal'}\n"
        
        summary += f"\n{'='*70}\n"
        
        return summary
    
    async def test_telegram_connection(self):
        """Test Telegram bot connection."""
        if not self.is_telegram_enabled():
            print("❌ Telegram not configured or disabled")
            return False
        
        try:
            telegram_config = self.notification_config['telegram']
            bot_token = telegram_config['bot_token']
            
            # Test bot connection
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        bot_info = await response.json()
                        if bot_info.get('ok'):
                            print(f"✅ Telegram bot connected: {bot_info['result']['first_name']}")
                            
                            # Send test message
                            test_msg = "🧪 <b>Encar Monitor Test</b>\n\nTelegram notifications are working! 🎉"
                            await self.send_telegram_alert(test_msg)
                            return True
                        else:
                            print(f"❌ Telegram bot error: {bot_info}")
                            return False
                    else:
                        print(f"❌ Telegram API error: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Telegram test failed: {e}")
            return False
    
    def test_notifications(self):
        """Test notification system."""
        test_listing = {
            'car_id': 'TEST123',
            'title': 'GLE400d 4MATIC 쿠페 TEST',
            'year': 2024,
            'price': '5,000만원',
            'mileage': '5,000km',
            'views': 3,
            'registration_date': '2024/12/01',
            'listing_url': 'http://test.url',
            'is_coupe': True,
            'is_truly_new': True,
            'days_since_registration': 5
        }
        
        print("🧪 Testing notification system...")
        
        # Test regular notifications
        self.send_new_listing_alert(test_listing)
        
        # Test Telegram if configured
        if self.is_telegram_enabled():
            print("🧪 Testing Telegram notifications...")
            asyncio.run(self.test_telegram_connection())
        else:
            print("⚠️ Telegram not configured - add bot_token and chat_id to config.yaml")
        
        print("✅ Notification test completed!")

if __name__ == "__main__":
    # Test the notification system
    notifier = NotificationManager()
    notifier.test_notifications()