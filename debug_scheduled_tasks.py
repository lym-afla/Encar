#!/usr/bin/env python3
"""
Debug Scheduled Tasks
Quick debugging script to test all scheduled tasks and their Telegram notifications
"""

import asyncio
import schedule
from datetime import datetime, timedelta
from encar_monitor_api import EncarMonitorAPI

async def debug_all_tasks():
    """Debug all scheduled tasks"""
    print("🔍 SCHEDULED TASKS DEBUGGER")
    print("=" * 50)
    
    # Initialize monitor
    monitor = EncarMonitorAPI()
    
    try:
        print("\n1️⃣ TESTING CURRENT SCHEDULE SETUP")
        print("-" * 30)
        
        # Set up the same schedules as in start_monitoring()
        schedule.clear()
        
        # Get config values
        interval_minutes = monitor.config['monitoring']['check_interval_minutes']
        quick_scan_interval = monitor.config['monitoring'].get('quick_scan_interval_minutes', 5)
        
        # Set up schedules exactly like in start_monitoring()
        schedule.every(interval_minutes).minutes.do(lambda: print("⏱️ Regular monitoring would run now"))
        schedule.every(quick_scan_interval).minutes.do(lambda: print("⚡ Quick scan would run now"))
        schedule.every().day.at("22:00").do(lambda: print("📊 Daily summary would run now"))
        schedule.every(6).hours.do(lambda: print("🔍 Closure scan would run now"))
        schedule.every().sunday.at("02:00").do(lambda: print("🧹 Weekly cleanup would run now"))
        
        # Show current schedule status
        jobs = schedule.jobs
        print(f"📅 Total scheduled jobs: {len(jobs)}")
        for i, job in enumerate(jobs, 1):
            print(f"  {i}. Next run: {job.next_run} | Function: {job.job}")
        
        print("\n2️⃣ TESTING TELEGRAM NOTIFICATIONS")
        print("-" * 30)
        
        # Test if Telegram is working
        print("🧪 Testing basic Telegram connectivity...")
        try:
            test_msg = "🧪 Testing scheduled tasks debugging - this message confirms Telegram is working!"
            monitor.notifier.send_monitoring_status("Debug Test", test_msg, send_to_telegram=True)
            print("✅ Basic Telegram test sent")
        except Exception as e:
            print(f"❌ Telegram test failed: {e}")
            return
        
        print("\n3️⃣ TESTING INDIVIDUAL SCHEDULED TASKS")
        print("-" * 30)
        
        # Test each scheduled task individually
        await monitor.test_scheduled_tasks()
        
        print("\n4️⃣ SCHEDULE TIMING ANALYSIS")
        print("-" * 30)
        
        now = datetime.now()
        print(f"🕐 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Day of week: {now.strftime('%A')}")
        
        # Check when next scheduled events would occur
        for job in schedule.jobs:
            time_until = job.next_run - now
            hours = int(time_until.total_seconds() / 3600)
            minutes = int((time_until.total_seconds() % 3600) / 60)
            print(f"⏰ Next '{job.job}' in: {hours}h {minutes}m ({job.next_run.strftime('%Y-%m-%d %H:%M:%S')})")
        
        print("\n5️⃣ RECOMMENDATIONS")
        print("-" * 30)
        
        # Check if any tasks should have run recently
        daily_summary_today = now.replace(hour=22, minute=0, second=0, microsecond=0)
        if now > daily_summary_today and now < daily_summary_today + timedelta(days=1):
            print("💡 Daily summary should have run today at 22:00")
        
        # Check closure scan (every 6 hours from start)
        print("💡 Closure scans run every 6 hours from when the service starts")
        print("💡 Weekly cleanup runs every Sunday at 02:00")
        
        print("\n6️⃣ DEBUGGING TIPS")
        print("-" * 30)
        print("🔍 To debug in production:")
        print("   1. Check logs: sudo journalctl -u encar-monitor -f")
        print("   2. Look for: 'Executing scheduled...' messages") 
        print("   3. Check service status: sudo systemctl status encar-monitor")
        print("   4. Monitor Telegram for notifications")
        
        print("\n✅ DEBUGGING COMPLETE")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    finally:
        # Cleanup
        await monitor.cleanup_scraper()

if __name__ == "__main__":
    asyncio.run(debug_all_tasks())
