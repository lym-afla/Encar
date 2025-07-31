#!/usr/bin/env python3
"""
Encar Monitoring System Launcher
Simple menu-driven interface for the monitoring system.
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """Print the system banner."""
    print("\n" + "="*60)
    print("🚗 ENCAR MERCEDES-BENZ GLE COUPE MONITORING SYSTEM")
    print("="*60)
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Version: 1.0.0")
    print("="*60 + "\n")

def print_menu():
    """Print the main menu."""
    print("📋 MAIN MENU:")
    print("1. 🔍 Start Continuous Monitoring")
    print("2. 🧪 Run Test Cycle")
    print("3. ⚡ Quick Scan (First Page Only)")
    print("4. 📊 Check System Status")
    print("5. 📁 Export Data to CSV")
    print("6. 🛠️  Test Browser & Tooltip Extraction")
    print("7. ⚙️  System Information")
    print("8. 📖 View Configuration")
    print("9. ❌ Exit")
    print()

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🚀 {description}...")
    print(f"Command: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=False)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
    except Exception as e:
        print(f"❌ Error running command: {e}")
    
    print("-" * 50)
    input("Press Enter to continue...")

def check_environment():
    """Check if the environment is properly set up."""
    print("🔧 Checking Environment...")
    
    # Check if we're in virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Warning: Not running in virtual environment")
        print("   Run: .\\encar_venv\\Scripts\\activate.ps1")
        return False
    
    # Check if required files exist
    required_files = [
        'config.yaml',
        'encar_monitor.py',
        'encar_scraper.py',
        'data_storage.py',
        'notification.py',
        'utils.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ Environment check passed!")
    return True

def view_config():
    """Display current configuration."""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        print("📖 CURRENT CONFIGURATION:")
        print("-" * 50)
        print(config_content)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error reading config: {e}")
    
    input("Press Enter to continue...")

def main():
    """Main launcher function."""
    print_banner()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        input("Press Enter to exit...")
        return
    
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (1-9): ").strip()
            
            if choice == '1':
                print("\n🔄 Starting continuous monitoring...")
                print("⚠️  This will run indefinitely until stopped with Ctrl+C")
                confirm = input("Continue? (y/N): ").lower()
                if confirm == 'y':
                    run_command("python encar_monitor.py", "Continuous Monitoring")
            
            elif choice == '2':
                run_command("python encar_monitor.py --mode test", "Test Cycle")
            
            elif choice == '3':
                run_command("python encar_monitor.py --mode monitor --quick", "Quick Scan")
            
            elif choice == '4':
                run_command("python encar_monitor.py --mode status", "System Status Check")
            
            elif choice == '5':
                run_command("python encar_monitor.py --mode export", "Data Export")
            
            elif choice == '6':
                print("\n🛠️  TESTING MENU:")
                print("1. Test Browser Functionality")
                print("2. Test Tooltip Extraction")
                print("3. Test All Components")
                
                test_choice = input("Choose test (1-3): ").strip()
                
                if test_choice == '1':
                    run_command("python utils.py --test browser", "Browser Test")
                elif test_choice == '2':
                    run_command("python utils.py --test tooltip", "Tooltip Test")
                elif test_choice == '3':
                    run_command("python utils.py --test all", "All Tests")
                else:
                    print("❌ Invalid choice")
            
            elif choice == '7':
                run_command("python utils.py --info", "System Information")
            
            elif choice == '8':
                view_config()
            
            elif choice == '9':
                print("\n👋 Goodbye! Happy car hunting!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-9.")
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()