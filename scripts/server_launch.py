#!/usr/bin/env python3
"""
Server-side launch script for Encar Monitor
This replaces the local launch.py for server deployment
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def print_banner():
    """Print the server banner."""
    print("\n" + "="*60)
    print("🚗 ENCAR MONITOR - SERVER MODE")
    print("="*60)
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Server Mode: Production")
    print("="*60 + "\n")

def check_service_status():
    """Check if the systemd service is running."""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'encar-monitor'], 
                               capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def print_service_menu():
    """Print the service management menu."""
    status = "🟢 RUNNING" if check_service_status() else "🔴 STOPPED"
    
    print(f"📋 SERVICE MANAGEMENT MENU (Status: {status}):")
    print("1. 🚀 Start Service")
    print("2. 🛑 Stop Service") 
    print("3. 🔄 Restart Service")
    print("4. 📊 Service Status")
    print("5. 📝 View Live Logs")
    print("6. 📋 View Recent Logs")
    print("7. 🔧 Test Configuration")
    print("8. 📈 System Health Check")
    print("9. 🛠️  Manual Test Run")
    print("10. ❌ Exit")
    print()

def run_command(command, description, capture_output=True):
    """Run a command and handle output."""
    print(f"🚀 {description}...")
    print(f"Command: {' '.join(command) if isinstance(command, list) else command}")
    print("-" * 50)
    
    try:
        if capture_output:
            result = subprocess.run(command, capture_output=True, text=True, shell=isinstance(command, str))
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.returncode == 0:
                print(f"✅ {description} completed successfully!")
            else:
                print(f"❌ {description} failed with exit code {result.returncode}")
        else:
            result = subprocess.run(command, shell=isinstance(command, str))
            print(f"✅ {description} completed!")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    """Main server launcher function."""
    parser = argparse.ArgumentParser(description='Encar Monitor Server Launcher')
    parser.add_argument('--mode', choices=['start', 'stop', 'status', 'logs'], 
                       help='Direct mode (skip menu)')
    parser.add_argument('--follow-logs', action='store_true', 
                       help='Follow logs in real time')
    
    args = parser.parse_args()
    
    # Handle direct mode commands
    if args.mode:
        if args.mode == 'start':
            run_command(['sudo', 'systemctl', 'start', 'encar-monitor'], "Starting Service")
        elif args.mode == 'stop':
            run_command(['sudo', 'systemctl', 'stop', 'encar-monitor'], "Stopping Service")
        elif args.mode == 'status':
            run_command(['sudo', 'systemctl', 'status', 'encar-monitor'], "Service Status")
        elif args.mode == 'logs':
            if args.follow_logs:
                run_command(['sudo', 'journalctl', '-u', 'encar-monitor', '-f'], "Following Logs", capture_output=False)
            else:
                run_command(['sudo', 'journalctl', '-u', 'encar-monitor', '-n', '50'], "Recent Logs")
        return
    
    print_banner()
    
    # Check if we're in the right directory
    if not os.path.exists('/opt/encar-monitor'):
        print("❌ Encar Monitor not found in /opt/encar-monitor")
        print("   Please run the installation script first.")
        return
    
    # Change to application directory
    os.chdir('/opt/encar-monitor')
    
    while True:
        print_service_menu()
        
        try:
            choice = input("Enter your choice (1-10): ").strip()
            
            if choice == '1':
                if check_service_status():
                    print("ℹ️  Service is already running")
                else:
                    run_command(['sudo', 'systemctl', 'start', 'encar-monitor'], "Starting Service")
            
            elif choice == '2':
                if not check_service_status():
                    print("ℹ️  Service is already stopped")
                else:
                    run_command(['sudo', 'systemctl', 'stop', 'encar-monitor'], "Stopping Service")
            
            elif choice == '3':
                run_command(['sudo', 'systemctl', 'restart', 'encar-monitor'], "Restarting Service")
            
            elif choice == '4':
                run_command(['sudo', 'systemctl', 'status', 'encar-monitor'], "Service Status")
            
            elif choice == '5':
                print("📝 Following live logs (Press Ctrl+C to stop)...")
                run_command(['sudo', 'journalctl', '-u', 'encar-monitor', '-f'], "Live Logs", capture_output=False)
            
            elif choice == '6':
                run_command(['sudo', 'journalctl', '-u', 'encar-monitor', '-n', '50'], "Recent Logs")
            
            elif choice == '7':
                print("🔧 Testing configuration...")
                run_command(['python3', 'venv/bin/python', '-c', 
                           'import yaml; from notification import NotificationManager; '
                           'nm = NotificationManager(); print("✅ Configuration valid")'], 
                           "Configuration Test")
            
            elif choice == '8':
                print("📈 System Health Check...")
                print("\n🔧 Service Status:")
                run_command(['sudo', 'systemctl', 'is-active', 'encar-monitor'], "Service Active Check")
                
                print("\n💾 Disk Usage:")
                run_command(['du', '-sh', '/opt/encar-monitor/*'], "Disk Usage Check")
                
                print("\n🧠 Memory Usage:")
                run_command(['ps', 'aux', '--sort=-%mem'], "Memory Usage Check")
                
                print("\n📁 File Permissions:")
                run_command(['ls', '-la', '/opt/encar-monitor/.env'], "Environment File Check")
            
            elif choice == '9':
                print("\n🛠️  MANUAL TEST OPTIONS:")
                print("1. Quick scan test")
                print("2. Database connectivity test") 
                print("3. Telegram connectivity test")
                print("4. Browser functionality test")
                
                test_choice = input("Choose test (1-4): ").strip()
                
                if test_choice == '1':
                    run_command(['./venv/bin/python', 'encar_monitor_api.py', '--mode', 'test'], "Quick Scan Test")
                elif test_choice == '2':
                    run_command(['./venv/bin/python', '-c', 
                               'from data_storage import EncarDatabase; '
                               'db = EncarDatabase(); print("✅ Database connected")'], 
                               "Database Test")
                elif test_choice == '3':
                    run_command(['./venv/bin/python', '-c', 
                               'import asyncio; from notification import NotificationManager; '
                               'nm = NotificationManager(); asyncio.run(nm.test_telegram_connection())'], 
                               "Telegram Test")
                elif test_choice == '4':
                    run_command(['./venv/bin/python', '-c', 
                               'from playwright.sync_api import sync_playwright; '
                               'p = sync_playwright().start(); p.chromium.launch(); print("✅ Browser OK")'], 
                               "Browser Test")
                else:
                    print("❌ Invalid choice")
            
            elif choice == '10':
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-10.")
            
            if choice != '5':  # Don't pause after live logs
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
