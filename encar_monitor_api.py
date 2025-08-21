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
from datetime import datetime, timedelta
from typing import Dict
from encar_scraper_api import EncarScraperAPI
from data_storage import EncarDatabase
from notification import NotificationManager

class EncarMonitorAPI:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the API-based monitoring system"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Set up logging
        # Configure console output encoding for Windows
        if sys.platform == "win32":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s',
            handlers=[
                logging.FileHandler('encar_monitor.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ],
            force=True  # Override any existing configuration
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.database = EncarDatabase(self.config['database']['filename'])
        self.notifier = NotificationManager(config_path)
        self.scraper = None
        
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
                await self.scraper.__aexit__(None, None, None)
            except Exception as e:
                self.logger.warning(f"⚠️ Error during scraper cleanup: {e}")
    
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
            processed_listings = []
            
            for listing in listings:
                try:
                    result = self.database.save_listing(listing, self.config)
                    if result == 'new':
                        new_count += 1
                        processed_listings.append(listing)
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not process listing {listing.get('id', 'unknown')}: {e}")
            
            self.new_listings_found += new_count
            
            # Check for truly new listings (registration date based)
            truly_new_listings = self.database.get_truly_new_listings(self.config)
            
            if truly_new_listings:
                self.logger.info(f"🎯 Found {len(truly_new_listings)} truly new listings!")
                
                # Enhance new listings with views/registration data (selective)
                enhanced_listings = await self.scraper.get_views_registration_and_lease_batch(truly_new_listings[:5])
                
                # Save enhanced data to database
                for listing in enhanced_listings:
                    try:
                        self.database.save_listing(listing, self.config)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not save enhanced listing {listing.get('car_id', 'unknown')}: {e}")
                
                # Send notifications for new listings
                self.notifier.send_batch_alert(enhanced_listings)
            else:
                self.logger.info(f"📊 Scan completed: {len(listings)} listings processed, {new_count} new")
            
            # # Adaptive page increase if finding many new listings
            # if regular_config.get('adaptive_increase', False) and new_count > 5:
            #     additional_pages = min(3, regular_config.get('max_adaptive_pages', 8) - base_pages)
            #     if additional_pages > 0:
            #         self.logger.info(f"📈 High new listing activity, scanning {additional_pages} additional pages")
            #         additional_listings = await self.scraper.scrape_with_filters(filters=filters, max_pages=additional_pages)
            #         # Process additional listings...
                    
        except Exception as e:
            self.logger.error(f"❌ Error in regular monitoring: {e}")
    
    async def run_quick_scan(self):
        """Run a quick scan for very recent listings"""
        try:
            self.logger.info("⚡ Running quick scan...")
            
            # Apply filters for quick scan from config
            filters = {
                'year_min': int(self.config['search']['year_range'].split('..')[0][:4]),  # Extract year from "202100.."
                'price_max': int(self.config['search']['price_range'].split('..')[1]) / 100  # Convert "..9000" to 90
            }
            
            # Quick scan of first page only with filters
            listings = await self.scraper.scrape_with_filters(filters=filters, max_pages=1)
            
            if listings:
                new_count = 0
                for listing in listings:
                    result = self.database.save_listing(listing, self.config)
                    if result == 'new':
                        new_count += 1
                
                # Check for very fresh listings (immediate alerts)
                immediate_threshold = self.config['new_listing_criteria']['immediate_alert_max_views']
                fresh_listings = [l for l in listings if l.get('views', 0) <= immediate_threshold]
                
                if fresh_listings:
                    self.logger.info(f"🔥 Found {len(fresh_listings)} very fresh listings!")
                    # Use send_batch_alert for immediate alerts (send_immediate_alert doesn't exist)
                    self.notifier.send_batch_alert(fresh_listings)
                
                self.logger.info(f"⚡ Quick scan: {len(listings)} listings, {new_count} new")
            else:
                self.logger.info("⚡ Quick scan: no listings found")
                
        except Exception as e:
            self.logger.error(f"❌ Error in quick scan: {e}")
    
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
            
            # Quick scans every 5 minutes
            schedule.every(5).minutes.do(lambda: asyncio.create_task(self.run_quick_scan()))
            
            # Daily summary at 8 AM
            schedule.every().day.at("08:00").do(lambda: asyncio.create_task(self.send_daily_summary()))
            
            # Weekly cleanup on Sunday at 2 AM
            schedule.every().sunday.at("02:00").do(lambda: asyncio.create_task(self.cleanup_old_data()))
            
            self.logger.info(f"⏰ Scheduled monitoring: every {interval_minutes} minutes")
            self.logger.info("✅ Monitor started successfully!")
            
            # Main monitoring loop
            while self.running:
                schedule.run_pending()
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            self.logger.error(f"❌ Error in monitoring system: {e}")
        finally:
            await self.cleanup_scraper()
            self.logger.info("🛑 Monitor stopped")
    
    async def send_daily_summary(self):
        """Send daily summary of activity"""
        try:
            # Get recent stats
            stats = self.database.get_statistics()
            
            # Get recent listings (last 24 hours)
            recent_listings = self.database.get_recent_listings(hours=24)
            
            summary_msg = f"""
📊 Daily Encar Monitor Summary
==================================
🕐 Period: Last 24 hours
📈 Total checks: {self.check_count}
🆕 New listings: {len(recent_listings)}
⚡ Average scan time: {sum(self.scan_times)/len(self.scan_times):.1f}s
🎯 Database total: {stats.get('total_listings', 0)} listings
"""
            
            self.notifier.send_monitoring_status("Daily Summary", summary_msg)
            self.logger.info("📧 Daily summary sent")
            
        except Exception as e:
            self.logger.error(f"❌ Error sending daily summary: {e}")
    
    async def cleanup_old_data(self):
        """Clean up old data from database"""
        try:
            days_to_keep = self.config['database']['backup_days']
            removed_count = self.database.cleanup_old_listings(days_to_keep)
            
            self.logger.info(f"🧹 Cleanup completed: removed {removed_count} old listings")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")


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
    parser.add_argument('--mode', choices=['start', 'test', 'status'], default='start',
                       help='Operation mode')
    parser.add_argument('--config', default='config.yaml',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        asyncio.run(test_api_monitor())
    elif args.mode == 'status':
        monitor = EncarMonitorAPI(args.config)
        asyncio.run(monitor.print_status())
    else:  # start
        monitor = EncarMonitorAPI(args.config)
        asyncio.run(monitor.start_monitoring())


if __name__ == "__main__":
    main() 