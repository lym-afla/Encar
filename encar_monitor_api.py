#!/usr/bin/env python3
"""
Encar Monitor API - Fast API-based monitoring
Uses the hybrid API client for reliable and fast monitoring
"""

import asyncio
import logging
import schedule
import yaml
import signal
import sys
import io
import os
import re
from datetime import datetime, timedelta
from typing import Dict
from dotenv import load_dotenv
from encar_scraper_api import EncarScraperAPI
from data_storage import EncarDatabase
from notification import NotificationManager
from closure_scanner import ClosureScanner

class EncarMonitorAPI:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the API-based monitoring system"""
        # Load environment variables first
        load_dotenv()
        
        # Load and process config with environment variable substitution
        self.config = self._load_config_with_env_substitution(config_path)
        
        # Set up logging
        # Configure console output encoding for Windows
        if sys.platform == "win32":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s',
            handlers=[
                logging.FileHandler('logs/encar_monitor.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ],
            force=True  # Override any existing configuration
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.database = EncarDatabase(self.config['database']['filename'])
        self.notifier = NotificationManager(config_path)
        self.scraper = None
        self.closure_scanner = ClosureScanner(self.config)
        
        # Monitoring state
        self.running = True
        self.start_time = None
        self.check_count = 0
        self.new_listings_found = 0
        self.last_check = None
        
        # Performance metrics
        self.scan_times = []
        self.api_success_rate = 0
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def _load_config_with_env_substitution(self, config_path: str) -> Dict:
        """Load config file with environment variable substitution"""
        try:
            # Read config file
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Replace environment variable placeholders
            config_content = self._substitute_env_vars(config_content)
            
            # Parse the config
            config = yaml.safe_load(config_content)
            
            # Ensure numeric values are properly typed
            if 'monitoring' in config:
                monitoring = config['monitoring']
                # Convert string interval values to integers
                if 'check_interval_minutes' in monitoring:
                    monitoring['check_interval_minutes'] = int(monitoring['check_interval_minutes'])
                if 'quick_scan_interval_minutes' in monitoring:
                    monitoring['quick_scan_interval_minutes'] = int(monitoring['quick_scan_interval_minutes'])
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            # Return a minimal config to prevent crash
            return {
                'monitoring': {
                    'check_interval_minutes': 15,
                    'quick_scan_interval_minutes': 5
                },
                'database': {'filename': 'data/encar_listings.db'},
                'browser': {'headless': True}
            }
    
    def _substitute_env_vars(self, config_content: str) -> str:
        """Replace ${VARIABLE_NAME} placeholders with environment variables."""
        def replace_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                # For production, use defaults if env var not found
                defaults = {
                    'CHECK_INTERVAL_MINUTES': '15',
                    'QUICK_SCAN_INTERVAL_MINUTES': '5'
                }
                return defaults.get(var_name, match.group(0))
            return env_value
        
        # Pattern to match ${VARIABLE_NAME}
        pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
        return re.sub(pattern, replace_var, config_content)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info("🛑 Shutdown signal received, stopping monitor...")
        self.running = False
    
    async def initialize_scraper(self) -> bool:
        """Initialize the API-based scraper"""
        try:
            self.scraper = EncarScraperAPI(self.config)
            await self.scraper.__aenter__()
            
            # Test connectivity
            if await self.scraper.test_api_connectivity():
                self.logger.info("✅ API scraper initialized successfully")
                return True
            else:
                self.logger.error("❌ API scraper connectivity test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize scraper: {e}")
            return False
    
    async def cleanup_scraper(self):
        """Clean up the scraper"""
        if self.scraper:
            try:
                # Ensure the API client session is properly closed
                if hasattr(self.scraper, 'api_client') and self.scraper.api_client:
                    await self.scraper.api_client.cleanup_sessions()
                            
                await self.scraper.__aexit__(None, None, None)
            except Exception as e:
                self.logger.warning(f"⚠️ Error during scraper cleanup: {e}")
    
    async def cleanup_scraper_sessions(self):
        """Clean up any unclosed sessions in the API client"""
        try:
            if self.scraper and hasattr(self.scraper, 'api_client') and self.scraper.api_client:
                await self.scraper.api_client.cleanup_sessions()
                self.logger.debug("🧹 Session cleanup completed")
        except Exception as e:
            self.logger.warning(f"⚠️ Error during session cleanup: {e}")
    
    async def run_monitoring_cycle(self):
        """Run a single monitoring cycle with API-based approach"""
        try:
            self.logger.info("🔄 Starting API monitoring cycle...")
            start_time = datetime.now()
            
            self.check_count += 1
            
            # Check if this is the first run (database is empty)
            is_first_run = self.database.is_first_run()
            
            if is_first_run:
                self.logger.info("🆕 First run detected - performing initial database population")
                await self.run_initial_population()
            else:
                self.logger.info("🔍 Regular monitoring scan")
                await self.run_regular_monitoring()
            
            # Update performance metrics
            scan_time = (datetime.now() - start_time).total_seconds()
            self.scan_times.append(scan_time)
            if len(self.scan_times) > 10:  # Keep last 10 scan times
                self.scan_times.pop(0)
            
            self.last_check = datetime.now()
            self.logger.info(f"✅ Monitoring cycle completed in {scan_time:.1f}s")
            
            # Periodic session cleanup to prevent unclosed sessions
            if self.check_count % 10 == 0:  # Every 10 cycles
                await self.cleanup_scraper_sessions()
            
        except Exception as e:
            self.logger.error(f"❌ Error in monitoring cycle: {e}")
    
    async def run_initial_population(self):
        """Populate database with existing listings on first run"""
        try:
            self.logger.info("📊 Starting initial population with API...")
            
            # Get smart page count based on total available
            total_count = await self.scraper.get_total_available_count()
            self.logger.info(f"📈 Total vehicles available: {total_count}")
            
            # Calculate optimal pages for initial scan
            initial_config = self.config['monitoring']['initial_scan']
            max_pages = initial_config['max_pages']
            min_pages = initial_config['min_pages']
            target_coverage = initial_config.get('target_coverage', 0.8)
            
            optimal_pages = min(max_pages, max(min_pages, int((total_count * target_coverage) / 20)))
            
            self.logger.info(f"🎯 Scanning {optimal_pages} pages for initial population")
            
            # Apply filters for initial population from config
            filters = {
                'year_min': int(self.config['search']['year_range'].split('..')[0][:4]),  # Extract year from "202100.."
                'price_max': int(self.config['search']['price_range'].split('..')[1]) / 100  # Convert "..9000" to 90
            }
            
            # Get listings using API with filters
            listings = await self.scraper.scrape_with_filters(filters=filters, max_pages=optimal_pages)
            
            if listings:
                # Save all listings to database
                saved_count = 0
                for listing in listings:
                    try:
                        result = self.database.save_listing(listing, self.config)
                        if result == 'new':
                            saved_count += 1
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not save listing {listing.get('id', 'unknown')}: {e}")
                
                self.logger.info(f"✅ Initial population completed: {saved_count} listings saved")
                
                # Send summary notification
                self.notifier.send_monitoring_status(
                    f"🆕 Initial Population Complete",
                    f"Saved {saved_count} coupe listings from {len(listings)} total listings"
                )
            else:
                self.logger.warning("⚠️ No listings found during initial population")
                
        except Exception as e:
            self.logger.error(f"❌ Error in initial population: {e}")
    
    async def run_regular_monitoring(self):
        """Run regular monitoring for new listings"""
        try:
            # Get smart page count for regular monitoring
            regular_config = self.config['monitoring']['regular_scan']
            base_pages = regular_config['base_pages']
            
            self.logger.info(f"🔍 Regular scan: checking first {base_pages} pages...")
            
            # Apply filters for regular monitoring from config
            filters = {
                'year_min': int(self.config['search']['year_range'].split('..')[0][:4]),  # Extract year from "202100.."
                'price_max': int(self.config['search']['price_range'].split('..')[1]) / 100  # Convert "..9000" to 90
            }
            
            # Get recent listings using API with filters
            listings = await self.scraper.scrape_with_filters(filters=filters, max_pages=base_pages)
            
            if not listings:
                self.logger.warning("⚠️ No listings found in regular scan")
                return
            
            # Process listings and find new ones
            new_count = 0
            
            notifications_sent = 0
            enhanced_listings = []
            
            for listing in listings:
                try:
                    result = self.database.save_listing(listing, self.config)
                    if result == 'new':
                        new_count += 1
                        
                        # Send immediate notification if worthy (no timezone dependency)
                        if self.is_listing_notification_worthy(listing):
                            try:
                                self.notifier.send_new_listing_alert(listing)
                                notifications_sent += 1
                                self.logger.info(f"📱 Sent immediate notification for car {listing['car_id']}")
                                enhanced_listings.append(listing)  # Track for enhancement
                            except Exception as e:
                                self.logger.warning(f"⚠️ Could not send notification for {listing.get('car_id', 'unknown')}: {e}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not process listing {listing.get('id', 'unknown')}: {e}")
            
            self.new_listings_found += new_count
            self.logger.info(f"🔍 Regular scan: {len(listings)} listings, {new_count} new, {notifications_sent} notifications sent")
                
            
            # Enhance notified listings with detailed data (for database improvement)
            if len(enhanced_listings) > 0:
                enhance_count = min(5, len(enhanced_listings))
                self.logger.info(f"🔍 Processing {enhance_count} notified listings for enhanced data")
                enhanced_data = await self.scraper.get_views_registration_and_lease_batch(enhanced_listings[:enhance_count])
                
                # Save enhanced data to database
                for listing in enhanced_data:
                    try:
                        self.database.save_listing(listing, self.config)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not save enhanced listing {listing.get('car_id', 'unknown')}: {e}")
            
            # # Adaptive page increase if finding many new listings
            # if regular_config.get('adaptive_increase', False) and new_count > 5:
            #     additional_pages = min(3, regular_config.get('max_adaptive_pages', 8) - base_pages)
            #     if additional_pages > 0:
            #         self.logger.info(f"📈 High new listing activity, scanning {additional_pages} additional pages")
            #         additional_listings = await self.scraper.scrape_with_filters(filters=filters, max_pages=additional_pages)
            #         # Process additional listings...
                    
        except Exception as e:
            self.logger.error(f"❌ Error in regular monitoring: {e}")
    
    def is_listing_notification_worthy(self, listing: Dict) -> bool:
        """Determine if a listing should trigger a notification"""
        
        # Must be a coupe
        if not listing.get('is_coupe', False):
            return False
        
        # Check criteria from config
        criteria = self.config.get('new_listing_criteria', {})
        
        # Very fresh (low views)
        max_views = criteria.get('immediate_alert_max_views', 10)
        if listing.get('views', 0) <= max_views:
            return True
        
        # Recent registration
        max_age_days = criteria.get('max_registration_age_days', 30)
        days_since_reg = listing.get('days_since_registration')
        if days_since_reg is not None and days_since_reg <= max_age_days:
            return True
        
        return False
    
    async def run_quick_scan(self):
        """Run a quick scan for very recent listings"""
        try:
            self.logger.info("⚡ Running quick scan...")
            
            # Initialize scraper
            if not await self.initialize_scraper():
                self.logger.error("❌ Failed to initialize API scraper")
                return
            
            # Apply filters for quick scan from config
            filters = {
                'year_min': int(self.config['search']['year_range'].split('..')[0][:4]),  # Extract year from "202100.."
                'price_max': int(self.config['search']['price_range'].split('..')[1]) / 100  # Convert "..9000" to 90
            }
            
            # Quick scan of first page only with filters
            listings = await self.scraper.scrape_with_filters(filters=filters, max_pages=1)
            
            if listings:
                new_count = 0
                notifications_sent = 0
                
                for listing in listings:
                    result = self.database.save_listing(listing, self.config)
                    if result == 'new':
                        new_count += 1
                        
                        # Send immediate notification if worthy (no timezone dependency)
                        if self.is_listing_notification_worthy(listing):
                            try:
                                self.notifier.send_new_listing_alert(listing)
                                notifications_sent += 1
                                self.logger.info(f"📱 Sent immediate notification for car {listing['car_id']}")
                            except Exception as e:
                                self.logger.warning(f"⚠️ Could not send notification for {listing.get('car_id', 'unknown')}: {e}")
                
                self.logger.info(f"⚡ Quick scan: {len(listings)} listings, {new_count} new, {notifications_sent} notifications sent")
            else:
                self.logger.info("⚡ Quick scan: no listings found")
            
            # Session cleanup after quick scan to prevent accumulation
            await self.cleanup_scraper_sessions()
                
        except Exception as e:
            self.logger.error(f"❌ Error in quick scan: {e}")
            # Cleanup even on error
            try:
                await self.cleanup_scraper_sessions()
            except:
                pass
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            # Get database stats
            db_stats = self.database.get_statistics()
            
            # Get API status
            api_status = await self.scraper.get_api_status() if self.scraper else {'api_working': False}
            
            # Calculate uptime
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            
            # Calculate average scan time
            avg_scan_time = sum(self.scan_times) / len(self.scan_times) if self.scan_times else 0
            
            status = {
                'running': self.running,
                'uptime': str(uptime),
                'checks_completed': self.check_count,
                'new_listings_found': self.new_listings_found,
                'last_check': self.last_check.isoformat() if self.last_check else None,
                'average_scan_time': f"{avg_scan_time:.1f}s",
                'api_status': api_status,
                'database_stats': db_stats
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ Error getting system status: {e}")
            return {'error': str(e)}
    
    async def print_status(self):
        """Print current system status"""
        await self._print_status_async()
    
    async def _print_status_async(self):
        """Async version of print status"""
        status = await self.get_system_status()
        
        print("\n🔍 ENCAR API MONITOR STATUS")
        print("=" * 50)
        print(f"Status: {'🟢 RUNNING' if status.get('running') else '🔴 STOPPED'}")
        print(f"Uptime: {status.get('uptime', 'N/A')}")
        print(f"Checks completed: {status.get('checks_completed', 0)}")
        print(f"New listings found: {status.get('new_listings_found', 0)}")
        print(f"Last check: {status.get('last_check', 'Never')}")
        print(f"Average scan time: {status.get('average_scan_time', 'N/A')}")
        
        api_status = status.get('api_status', {})
        print(f"API Status: {'🟢 Working' if api_status.get('api_working') else '🔴 Error'}")
        
        db_stats = status.get('database_stats', {})
        print(f"📊 Database Stats:")
        print(f"  Total listings: {db_stats.get('total_listings', 0)}")
        print(f"  Coupe listings: {db_stats.get('coupe_listings', 0)}")
        print(f"  Truly new: {db_stats.get('truly_new', 0)}")
        print("=" * 50)
    
    async def start_monitoring(self):
        """Start the continuous monitoring system"""
        try:
            self.logger.info("🚀 Starting Encar API Monitor...")
            self.start_time = datetime.now()
            
            # Initialize scraper
            if not await self.initialize_scraper():
                self.logger.error("❌ Failed to initialize API scraper")
                return
            
            # Initial monitoring cycle
            await self.run_monitoring_cycle()
            
            # Set up scheduled monitoring
            schedule.clear()
            
            # Regular monitoring based on config
            interval_minutes = self.config['monitoring']['check_interval_minutes']
            schedule.every(interval_minutes).minutes.do(lambda: asyncio.create_task(self.run_monitoring_cycle()))
            
            # Quick scans every 5 minutes (with config fallback)
            quick_scan_interval = self.config['monitoring'].get('quick_scan_interval_minutes', 5)
            schedule.every(quick_scan_interval).minutes.do(lambda: asyncio.create_task(self.run_quick_scan()))
            
            # Daily summary at 10 PM
            schedule.every().day.at("22:00").do(lambda: asyncio.create_task(self.send_daily_summary()))
            
            # Closure scanning every 6 hours
            schedule.every(6).hours.do(lambda: asyncio.create_task(self.run_closure_scan()))
            
            # Weekly cleanup on Sunday at 2 AM
            schedule.every().sunday.at("02:00").do(lambda: asyncio.create_task(self.cleanup_old_data()))
            
            self.logger.info(f"⏰ Scheduled monitoring: every {interval_minutes} minutes")
            self.logger.info("✅ Monitor started successfully!")
            
            # Send startup notification to Telegram            
            startup_msg = f"""🚀 Encar Monitor Started
=========================
📅 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
⏰ Check interval: Every {interval_minutes} minutes
🔍 Quick scans: Every {quick_scan_interval} minutes
📊 Daily summary: 22:00
🔒 Closure scans: Every 6 hours
🧹 Weekly cleanup: Sundays at 02:00

System is now monitoring for new GLE Coupe listings! 🚗"""

            self.notifier.send_monitoring_status("STARTED", startup_msg, send_to_telegram=True)
            
            # Main monitoring loop
            self.logger.info("🔄 Starting main scheduling loop...")
            loop_count = 0
            while self.running:
                # Run any pending scheduled tasks
                schedule.run_pending()
                
                # Log scheduled tasks status every 10 minutes for debugging
                loop_count += 1
                if loop_count % 20 == 0:  # Every 20 loops (10 minutes)
                    jobs = schedule.jobs
                    self.logger.debug(f"📅 Active scheduled jobs: {len(jobs)}")
                    for job in jobs:
                        func_name = getattr(job.job_func, '__name__', str(job.job_func))
                        self.logger.debug(f"  - Next run: {job.next_run} | Job: {func_name}")
                
                await asyncio.sleep(30)  # Check every 30 seconds

            # Send shutdown notification to Telegram
            shutdown_msg = f"""🛑 Encar Monitor Stopped
========================
📅 Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⏱️ Runtime: {datetime.now() - self.start_time if self.start_time else 'Unknown'}
📊 Total checks performed: {self.check_count}
🆕 New listings found: {self.new_listings_found}

Monitor has been shut down."""
            
            self.notifier.send_monitoring_status("STOPPED", shutdown_msg, send_to_telegram=True)
                
        except Exception as e:
            self.logger.error(f"❌ Error in monitoring system: {e}")
            # Send error notification to Telegram
            error_msg = f"""❌ Critical Monitor Error
=======================
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 Checks completed: {self.check_count}
⚠️ Error: {str(e)}

The monitoring system encountered a critical error and may need attention."""
            
            self.notifier.send_monitoring_status("ERROR", error_msg, send_to_telegram=True)
        finally:
            await self.cleanup_scraper()
            self.logger.info("🛑 Monitor stopped")
    
    async def send_daily_summary(self):
        """Send daily summary of activity"""
        try:
            self.logger.info("📊 Executing scheduled daily summary...")
            
            # Get recent stats
            stats = self.database.get_statistics()
            closure_stats = self.database.get_closure_statistics()
            
            # Get recent listings (last 24 hours)
            recent_listings = self.database.get_recent_listings(hours=24)
            
            # Calculate average scan time safely
            avg_scan_time = sum(self.scan_times)/len(self.scan_times) if self.scan_times else 0
            
            summary_msg = f"""📊 Daily Encar Monitor Summary
==================================
🕐 Period: Last 24 hours  
📈 Total checks: {self.check_count}
🆕 New listings: {len(recent_listings)}
⚡ Average scan time: {avg_scan_time:.1f}s
🎯 Database total: {stats.get('total_listings', 0)} listings

🔒 Closure Statistics:
- Active listings: {closure_stats.get('active_listings', 0)}
- Closed listings: {closure_stats.get('closed_listings', 0)}
- Closure rate: {closure_stats.get('closure_rate', '0%')}

System running since: {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'Unknown'}"""
            
            # Send via all notification methods including Telegram
            self.notifier.send_monitoring_status("Daily Summary", summary_msg, send_to_telegram=True)
            self.logger.info("✅ Daily summary sent successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error sending daily summary: {e}")
            # Send error notification to Telegram
            error_msg = f"❌ Daily summary failed at {datetime.now().strftime('%H:%M:%S')}: {str(e)}"
            self.notifier.send_monitoring_status("Daily Summary Error", error_msg, send_to_telegram=True)
    
    async def run_closure_scan(self):
        """Run closure detection scan on older listings"""
        try:
            self.logger.info("🔍 Executing scheduled closure scan...")
            
            # Scan listings older than 3 days, limit to 50 per scan
            results = await self.closure_scanner.scan_listings_for_closure(
                max_listings=50,
                max_age_days=3
            )
            
            # Always send notification about closure scan results
            msg = f"""🔒 Closure Scan Results
=====================
📊 Checked: {results['total_checked']} listings
🔒 Closed found: {results['closed_found']}
✅ Still active: {results['still_active']}
❌ Errors: {results['errors']}
🕐 Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # Send notification to Telegram (always, regardless of results)
            self.notifier.send_monitoring_status("Closure Scan", msg, send_to_telegram=True)
                
            self.logger.info(f"✅ Closure scan completed: {results['closed_found']} closed listings found")
            
        except Exception as e:
            self.logger.error(f"❌ Error during closure scan: {e}")
            # Send error notification to Telegram
            error_msg = f"❌ Closure scan failed at {datetime.now().strftime('%H:%M:%S')}: {str(e)}"
            self.notifier.send_monitoring_status("Closure Scan Error", error_msg, send_to_telegram=True)
    
    async def cleanup_old_data(self):
        """Clean up old data from database"""
        try:
            self.logger.info("🧹 Executing scheduled weekly cleanup...")
            
            days_to_keep = self.config['database']['backup_days']
            removed_count = self.database.cleanup_old_listings(days_to_keep)
            
            # Send Telegram notification about cleanup
            cleanup_msg = f"""🧹 Weekly Database Cleanup
==========================
📊 Removed listings older than {days_to_keep} days
🗑️ Records deleted: {removed_count}
🕐 Cleanup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Database maintenance completed successfully."""
            
            self.notifier.send_monitoring_status("Weekly Cleanup", cleanup_msg, send_to_telegram=True)
            self.logger.info(f"✅ Cleanup completed: removed {removed_count} old listings")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")
            # Send error notification to Telegram
            error_msg = f"❌ Weekly cleanup failed at {datetime.now().strftime('%H:%M:%S')}: {str(e)}"
            self.notifier.send_monitoring_status("Weekly Cleanup Error", error_msg, send_to_telegram=True)

    async def test_scheduled_tasks(self):
        """Test all scheduled tasks manually"""
        self.logger.info("🧪 Testing all scheduled tasks...")
        
        try:
            # Test daily summary
            self.logger.info("Testing daily summary...")
            await self.send_daily_summary()
            
            # Test closure scan
            self.logger.info("Testing closure scan...")
            await self.run_closure_scan()
            
            # Test weekly cleanup
            self.logger.info("Testing weekly cleanup...")
            await self.cleanup_old_data()
            
            self.logger.info("✅ All scheduled tasks tested successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error testing scheduled tasks: {e}")


async def test_api_monitor():
    """Test the API-based monitoring system"""
    print("🧪 Testing Encar API Monitor...")
    
    monitor = EncarMonitorAPI()
    
    try:
        # Test scraper initialization
        print("\n🔧 Testing scraper initialization...")
        if await monitor.initialize_scraper():
            print("✅ Scraper initialized successfully")
        else:
            print("❌ Scraper initialization failed")
            return
        
        # Test monitoring cycle
        print("\n🔄 Testing monitoring cycle...")
        await monitor.run_monitoring_cycle()
        
        # Print status
        print("\n📊 System status:")
        await monitor.print_status()
        
        print("\n✅ API monitor test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await monitor.cleanup_scraper()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Encar API Monitor')
    parser.add_argument('--mode', choices=['start', 'test', 'status', 'closure', 'test-schedule'], default='start',
                       help='Operation mode')
    parser.add_argument('--config', default='config.yaml',
                       help='Configuration file path')
    parser.add_argument('--quick', action='store_true', help='Run quick scan only')
    parser.add_argument('--max-listings', type=int, help='Max listings to check for closure scan')
    parser.add_argument('--max-age', type=int, default=7, help='Max age in days for closure scan')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        asyncio.run(test_api_monitor())
    elif args.mode == 'status':
        monitor = EncarMonitorAPI(args.config)
        asyncio.run(monitor.print_status())
    elif args.mode == 'closure':
        # Run closure scan
        async def run_closure():
            monitor = EncarMonitorAPI(args.config)
            results = await monitor.closure_scanner.scan_listings_for_closure(
                max_listings=args.max_listings,
                max_age_days=args.max_age
            )
            print(f"\n🔍 Closure scan completed:")
            print(f"   - Total checked: {results['total_checked']}")
            print(f"   - Closed found: {results['closed_found']}")
            print(f"   - Still active: {results['still_active']}")
            print(f"   - Errors: {results['errors']}")
        
        asyncio.run(run_closure())
    elif args.mode == 'test-schedule':
        # Test scheduled tasks
        async def test_scheduled():
            monitor = EncarMonitorAPI(args.config)
            await monitor.test_scheduled_tasks()
        
        asyncio.run(test_scheduled())
    else:  # start
        monitor = EncarMonitorAPI(args.config)
        if args.quick:
            asyncio.run(monitor.run_quick_scan())
        else:
            asyncio.run(monitor.start_monitoring())


if __name__ == "__main__":
    main() 