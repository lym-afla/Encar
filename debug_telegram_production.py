#!/usr/bin/env python3
"""
Debug script for Telegram notifications on production server
Run this to diagnose why Telegram notifications aren't working
"""

import os
import sys
import yaml
import re
import asyncio
import aiohttp
from dotenv import load_dotenv

def check_environment_setup():
    """Check if environment variables are properly set"""
    print("🔍 Checking Environment Setup...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check critical environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print(f"📋 Environment Variables:")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ Set' if bot_token else '❌ NOT SET'}")
    if bot_token:
        print(f"   Token length: {len(bot_token)} chars")
        print(f"   Token format: {'✅ Valid' if ':' in bot_token else '❌ Invalid format'}")
    
    print(f"   TELEGRAM_CHAT_ID: {'✅ Set' if chat_id else '❌ NOT SET'}")
    if chat_id:
        print(f"   Chat ID: {chat_id}")
        try:
            int(chat_id)
            print("   Format: ✅ Valid numeric")
        except ValueError:
            print("   Format: ❌ Should be numeric")
    
    print()
    return bot_token, chat_id

def load_and_check_config():
    """Load config and check notification settings"""
    print("⚙️ Checking Configuration...")
    print("=" * 50)
    
    try:
        # Load environment first
        load_dotenv()
        
        # Find config file
        config_path = 'config.yaml'
        if not os.path.exists(config_path):
            config_path = 'config.template.yaml'
        
        print(f"📄 Loading config from: {config_path}")
        
        # Read and substitute environment variables
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # Apply environment variable substitution
        def substitute_env_vars(content):
            def replace_var(match):
                var_name = match.group(1)
                env_value = os.getenv(var_name)
                if env_value is None:
                    print(f"⚠️ Warning: Environment variable {var_name} not found")
                    return match.group(0)
                return env_value
            
            pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
            return re.sub(pattern, replace_var, content)
        
        config_content = substitute_env_vars(config_content)
        config = yaml.safe_load(config_content)
        
        # Check notifications configuration
        if 'notifications' not in config:
            print("❌ No 'notifications' section in config!")
            return None
        
        notifications = config['notifications']
        print(f"📊 Notification Configuration:")
        print(f"   Enabled: {notifications.get('enabled', False)}")
        print(f"   Methods: {notifications.get('methods', [])}")
        
        if 'telegram' in notifications.get('methods', []):
            telegram_config = notifications.get('telegram', {})
            print(f"   Telegram enabled: {telegram_config.get('enabled', False)}")
            print(f"   Bot token configured: {'✅' if telegram_config.get('bot_token') else '❌'}")
            print(f"   Chat ID configured: {'✅' if telegram_config.get('chat_id') else '❌'}")
            
            # Show actual values after substitution
            bot_token = telegram_config.get('bot_token', '')
            chat_id = telegram_config.get('chat_id', '')
            
            if bot_token.startswith('${'):
                print(f"   ⚠️ Bot token still has placeholder: {bot_token}")
            if chat_id.startswith('${'):
                print(f"   ⚠️ Chat ID still has placeholder: {chat_id}")
        else:
            print("   ❌ Telegram not in notification methods!")
        
        print()
        return config
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

async def test_telegram_api_direct(bot_token, chat_id):
    """Test Telegram API directly"""
    print("🧪 Testing Telegram API Directly...")
    print("=" * 50)
    
    if not bot_token or not chat_id:
        print("❌ Missing bot token or chat ID")
        return False
    
    try:
        # Test bot info
        print("📡 Testing bot info...")
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    bot_info = await response.json()
                    print(f"✅ Bot connected: {bot_info['result']['first_name']} (@{bot_info['result']['username']})")
                else:
                    error_text = await response.text()
                    print(f"❌ Bot info failed ({response.status}): {error_text}")
                    return False
        
        # Test send message
        print("📬 Testing message sending...")
        message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        test_message = f"""🧪 Encar Monitor Test
========================
📅 Time: {os.popen('date').read().strip()}
🖥️ Server: Production test
📊 Status: Testing notifications

This is a test message from your Encar monitoring service!"""
        
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'HTML'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(message_url, json=payload, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Test message sent successfully!")
                    print(f"   Message ID: {result['result']['message_id']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Message sending failed ({response.status}): {error_text}")
                    return False
    
    except Exception as e:
        print(f"❌ Error testing Telegram API: {e}")
        return False

def test_notification_manager():
    """Test the NotificationManager class"""
    print("🔧 Testing NotificationManager...")
    print("=" * 50)
    
    try:
        # Import after environment is loaded
        from notification import NotificationManager
        
        # Initialize with config
        config_path = 'config.yaml' if os.path.exists('config.yaml') else 'config.template.yaml'
        notifier = NotificationManager(config_path)
        
        print("✅ NotificationManager created successfully")
        
        # Check if telegram is enabled
        if hasattr(notifier, 'notification_config'):
            methods = notifier.notification_config.get('methods', [])
            print(f"   Configured methods: {methods}")
            
            if 'telegram' in methods:
                print("✅ Telegram method is configured")
                
                # Try to send a test status
                print("📤 Sending test monitoring status...")
                notifier.send_monitoring_status(
                    "TEST", 
                    "This is a test notification from production debugging", 
                    send_to_telegram=True
                )
                print("✅ Test status sent (check logs for any errors)")
                
            else:
                print("❌ Telegram not in configured methods")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing NotificationManager: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main debugging function"""
    print("🚀 Encar Monitor - Telegram Debug Tool")
    print("=" * 60)
    print()
    
    # Step 1: Check environment
    bot_token, chat_id = check_environment_setup()
    
    # Step 2: Check configuration
    config = load_and_check_config()
    
    # Step 3: Test Telegram API directly
    if bot_token and chat_id:
        telegram_works = await test_telegram_api_direct(bot_token, chat_id)
        print()
    else:
        telegram_works = False
        print("⚠️ Skipping direct Telegram test - missing credentials")
        print()
    
    # Step 4: Test NotificationManager
    nm_works = test_notification_manager()
    print()
    
    # Summary
    print("📋 Debug Summary")
    print("=" * 50)
    print(f"Environment setup: {'✅' if bot_token and chat_id else '❌'}")
    print(f"Config loading: {'✅' if config else '❌'}")
    print(f"Direct Telegram API: {'✅' if telegram_works else '❌'}")
    print(f"NotificationManager: {'✅' if nm_works else '❌'}")
    print()
    
    if telegram_works and nm_works:
        print("✅ All tests passed! Telegram notifications should work.")
        print("   If service startup notifications still don't arrive:")
        print("   1. Check service logs: sudo journalctl -u encar-monitor -f")
        print("   2. Restart service: sudo systemctl restart encar-monitor")
    else:
        print("❌ Some tests failed. Fix the issues above before proceeding.")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
