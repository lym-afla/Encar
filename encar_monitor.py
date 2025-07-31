#!/usr/bin/env python3
"""
DEPRECATED: Legacy browser-based monitoring system
This module is deprecated and will be removed in future versions.
Use encar_monitor_api.py for API-based monitoring instead.

Encar Mercedes-Benz GLE Coupe Monitoring System
Monitors new car listings and sends alerts for potential purchases.
"""

import warnings
warnings.warn(
    "encar_monitor.py is deprecated. Use encar_monitor_api.py for API-based monitoring.",
    DeprecationWarning,
    stacklevel=2
)

import asyncio
import logging
import schedule
import time
import yaml
from datetime import datetime, timedelta
from typing import List, Dict
import signal
import sys
import os

from encar_scraper import EncarScraper
from data_storage import EncarDatabase
from notification import NotificationManager

class EncarMonitor:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Encar monitoring system."""
        self.config_path = config_path
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.scraper = EncarScraper(config_path)
        self.database = EncarDatabase(self.config['database']['filename'])
        self.notifier = NotificationManager(config_path)
        
        # Monitoring state
        self.is_running = False
        self.start_time = datetime.now()
        self.check_count = 0
        self.total_new_listings = 0
        
        # Set up logging
        self.setup_logging()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('encar_monitor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.is_running = False
        sys.exit(0)
    
    async def run_monitoring_cycle(self):
        """Run a single monitoring cycle with the new architecture."""
        try:
            self.logger.info("Starting monitoring cycle...")
            self.check_count += 1
            
            # Check if this is the first run (database is empty)
            is_first_run = self.database.is_first_run()
            
            if is_first_run:
                self.logger.info("🆕 First run detected - performing initial database population")
                await self.run_initial_population()
                return
            
            # Regular monitoring scan
            max_pages = self.config['monitoring']['max_pages_to_scan']
            listings = await self.scraper.scrape_multiple_pages(max_pages)
            
            if not listings:
                self.logger.warning("No listings found in this cycle")
                self.database.log_monitoring_action("scan_completed", "No listings found", 0, 0)
                return
            
            # Process listings with the new architecture
            new_count = 0
            updated_count = 0
            total_scanned = len(listings)
            
            for listing in listings:
                result = self.database.save_listing(listing, self.config)
                if result == 'new':
                    new_count += 1
                elif result == 'updated':
                    updated_count += 1
            
            # Get truly new listings for notifications
            truly_new_listings = self.database.get_truly_new_listings(self.config)
            recent_registrations = self.database.get_recent_registrations(7)  # Last 7 days
            
            # Log monitoring action
            self.database.log_monitoring_action(
                "scan_completed", 
                f"Scanned {total_scanned} listings, {new_count} new, {updated_count} updated. Truly new: {len(truly_new_listings)}",
                len(truly_new_listings),
                total_scanned
            )
            
            # Send notifications for truly new listings
            if truly_new_listings:
                summary_stats = {
                    'total_checked': total_scanned,
                    'coupe_count': len(listings),
                    'cycle_number': self.check_count,
                    'truly_new': len(truly_new_listings),
                    'recent_registrations': len(recent_registrations)
                }
                
                self.notifier.send_batch_alert(truly_new_listings, summary_stats)
                self.logger.info(f"Sent notifications for {len(truly_new_listings)} truly new listings")
                self.total_new_listings += len(truly_new_listings)
            
            # Also check for immediate alerts (very fresh listings)
            immediate_threshold = self.config['new_listing_criteria'].get('immediate_alert_views', 10)
            immediate_alerts = [l for l in truly_new_listings if l.get('views', 0) <= immediate_threshold]
            
            if immediate_alerts:
                for listing in immediate_alerts:
                    self.notifier.send_new_listing_alert(listing)
                    self.logger.info(f"Immediate alert: {listing['title']} ({listing['views']} views)")
            
            # Log summary
            self.logger.info(
                f"Cycle {self.check_count} completed: "
                f"{total_scanned} scanned, {new_count} new in DB, {len(truly_new_listings)} truly new, "
                f"{len(recent_registrations)} recent registrations"
            )
            
        except Exception as e:
            error_msg = f"Error in monitoring cycle: {e}"
            self.logger.error(error_msg)
            self.notifier.send_error_alert(str(e), "monitoring_cycle")
            self.database.log_monitoring_action("error", error_msg, 0, 0)
    
    async def run_initial_population(self):
        """Run initial database population with comprehensive scraping."""
        try:
            self.logger.info("🔄 Starting initial database population...")
            self.notifier.send_monitoring_status("INITIAL_POPULATION", "Populating database with existing listings")
            
            # Use detailed scraping for initial population
            max_pages = self.config['monitoring'].get('initial_population_pages', 20)
            self.logger.info(f"Scanning {max_pages} pages for initial population...")
            
            listings = await self.scraper.scrape_with_details(max_pages, is_initial_population=True)
            
            if not listings:
                self.logger.warning("No listings found during initial population")
                return
            
            # Save all listings to database
            saved_count = 0
            for listing in listings:
                result = self.database.save_listing(listing, self.config)
                if result == 'new':
                    saved_count += 1
            
            # Mark initial population as complete
            self.database.mark_initial_population_complete()
            
            # Log the initial population
            self.database.log_monitoring_action(
                "initial_population_completed",
                f"Populated database with {saved_count} listings from {max_pages} pages",
                saved_count,
                len(listings)
            )
            
            self.logger.info(f"✅ Initial population completed: {saved_count} listings saved")
            self.notifier.send_monitoring_status(
                "POPULATION_COMPLETE", 
                f"Database populated with {saved_count} listings. Monitoring will begin on next cycle."
            )
            
        except Exception as e:
            error_msg = f"Error during initial population: {e}"
            self.logger.error(error_msg)
            self.notifier.send_error_alert(str(e), "initial_population")
    
    async def run_quick_scan(self):
        """Run a quick scan of just the first page for very new listings."""
        try:
            self.logger.info("Running quick scan...")
            
            # Quick scan of first page only
            listings = await self.scraper.get_quick_scan()
            
            new_count = 0  # Initialize before conditional block
            if listings:
                for listing in listings:
                    result = self.database.save_listing(listing, self.config)
                    if result == 'new':
                        new_count += 1
                
                # Check for truly new listings
                truly_new = self.database.get_truly_new_listings(self.config)
                
                # Send immediate alerts for very fresh listings
                immediate_threshold = self.config['new_listing_criteria'].get('immediate_alert_views', 10)
                for listing in truly_new:
                    if listing.get('views', 0) <= immediate_threshold:
                        self.notifier.send_new_listing_alert(listing)
                        self.logger.info(f"Quick scan alert: {listing['title']} ({listing['views']} views)")
            
            self.database.log_monitoring_action(
                "quick_scan", 
                f"Found {len(listings) if listings else 0} listings, {new_count} new", 
                new_count,
                len(listings) if listings else 0
            )
            
        except Exception as e:
            self.logger.error(f"Error in quick scan: {e}")
            self.notifier.send_error_alert(str(e), "quick_scan")
    
    def cleanup_old_data(self):
        """Clean up old data from database."""
        try:
            backup_days = self.config['database']['backup_days']
            self.database.cleanup_old_data(backup_days)
            self.logger.info(f"Cleaned up data older than {backup_days} days")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up data: {e}")
    
    def generate_daily_summary(self):
        """Generate and send enhanced daily summary."""
        try:
            stats = self.database.get_statistics()
            stats['uptime'] = str(datetime.now() - self.start_time)
            stats['total_cycles'] = self.check_count
            stats['new_listings_found'] = self.total_new_listings
            
            # Enhanced summary with new metrics
            summary = f"\n📈 DAILY ENCAR MONITORING SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            summary += f"{'='*60}\n"
            summary += f"🔍 Monitoring Stats:\n"
            summary += f"   • Total monitoring cycles: {stats['total_cycles']}\n"
            summary += f"   • System uptime: {stats['uptime']}\n"
            summary += f"   • Last check: {stats.get('last_check', 'N/A')}\n"
            summary += f"\n📊 Database Stats:\n"
            summary += f"   • Total listings tracked: {stats.get('total_listings', 0)}\n"
            summary += f"   • Coupe listings: {stats.get('coupe_listings', 0)}\n"
            summary += f"   • Truly new listings: {stats.get('truly_new_listings', 0)}\n"
            summary += f"   • Recent registrations (7 days): {stats.get('recent_registrations', 0)}\n"
            summary += f"   • Low view listings: {stats.get('low_view_listings', 0)}\n"
            if stats.get('avg_registration_age_days'):
                summary += f"   • Avg registration age: {stats['avg_registration_age_days']} days\n"
            summary += f"\n🚗 New Findings Today:\n"
            summary += f"   • New listings discovered: {stats['new_listings_found']}\n"
            summary += f"{'='*60}\n"
            
            self.notifier.send_console_alert(summary)
            self.logger.info("Enhanced daily summary generated")
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
    
    def get_status(self) -> Dict:
        """Get current monitoring status with enhanced metrics."""
        uptime = datetime.now() - self.start_time
        db_stats = self.database.get_statistics()
        
        return {
            'is_running': self.is_running,
            'uptime': str(uptime),
            'checks_completed': self.check_count,
            'new_listings_found': self.total_new_listings,
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'database_stats': db_stats,
            'is_first_run': self.database.is_first_run(),
            'monitoring_mode': 'initial_population' if self.database.is_first_run() else 'regular_monitoring'
        }
    
    def print_status(self):
        """Print current status to console with enhanced information."""
        status = self.get_status()
        
        print(f"\n🔍 ENCAR MONITOR STATUS")
        print(f"{'='*50}")
        print(f"Status: {'🟢 RUNNING' if status['is_running'] else '🔴 STOPPED'}")
        print(f"Mode: {status['monitoring_mode'].replace('_', ' ').title()}")
        print(f"Uptime: {status['uptime']}")
        print(f"Checks completed: {status['checks_completed']}")
        print(f"New listings found: {status['new_listings_found']}")
        print(f"Last check: {status['last_check']}")
        
        db_stats = status['database_stats']
        print(f"\n📊 Database Stats:")
        print(f"  Total listings: {db_stats.get('total_listings', 0)}")
        print(f"  Coupe listings: {db_stats.get('coupe_listings', 0)}")
        print(f"  Truly new: {db_stats.get('truly_new_listings', 0)}")
        print(f"  Recent registrations: {db_stats.get('recent_registrations', 0)}")
        print(f"  Low view listings: {db_stats.get('low_view_listings', 0)}")
        if db_stats.get('avg_registration_age_days'):
            print(f"  Avg reg age: {db_stats['avg_registration_age_days']} days")
        print(f"{'='*50}\n")
    
    def start_scheduled_monitoring(self):
        """Start the scheduled monitoring system."""
        self.logger.info("Starting Encar monitoring system...")
        self.notifier.send_monitoring_status("STARTING", "Initializing monitoring system")
        
        # Set up monitoring schedule
        interval = self.config['monitoring']['check_interval_minutes']
        schedule.every(interval).minutes.do(self.run_monitoring_job)
        
        # Set up daily tasks
        schedule.every().day.at("08:00").do(self.daily_summary_job)
        schedule.every().day.at("02:00").do(self.cleanup_job)
        
        # Set up quick scans (every 5 minutes)
        schedule.every(5).minutes.do(self.quick_scan_job)
        
        self.is_running = True
        self.logger.info(f"Monitoring started with {interval}-minute intervals")
        self.notifier.send_monitoring_status("STARTED", f"Checking every {interval} minutes")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        finally:
            self.is_running = False
            self.notifier.send_monitoring_status("STOPPED", "Monitoring system shut down")
    
    def run_monitoring_job(self):
        """Wrapper for async monitoring cycle."""
        try:
            asyncio.run(self.run_monitoring_cycle())
        except Exception as e:
            self.logger.error(f"Error in monitoring job: {e}")
    
    def quick_scan_job(self):
        """Wrapper for async quick scan."""
        try:
            asyncio.run(self.run_quick_scan())
        except Exception as e:
            self.logger.error(f"Error in quick scan job: {e}")
    
    def daily_summary_job(self):
        """Daily summary job."""
        self.generate_daily_summary()
    
    def cleanup_job(self):
        """Daily cleanup job."""
        self.cleanup_old_data()
    
    async def run_single_check(self):
        """Run a single monitoring check (for testing) with new architecture."""
        self.logger.info("Running single monitoring check...")
        
        if self.database.is_first_run():
            self.logger.info("First run - will perform initial population")
            await self.run_initial_population()
        else:
            await self.run_monitoring_cycle()
            
        await self.run_quick_scan()
        self.print_status()

# CLI Interface
def main():
    """Main entry point for the monitoring system."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Encar Mercedes-Benz GLE Coupe Monitor')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--mode', choices=['monitor', 'test', 'status', 'export'], 
                       default='monitor', help='Operation mode')
    parser.add_argument('--quick', action='store_true', help='Run quick scan only')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = EncarMonitor(args.config)
    
    if args.mode == 'monitor':
        if args.quick:
            asyncio.run(monitor.run_quick_scan())
        else:
            monitor.start_scheduled_monitoring()
    
    elif args.mode == 'test':
        print("🧪 Running test monitoring cycle...")
        asyncio.run(monitor.run_single_check())
        print("✅ Test completed!")
    
    elif args.mode == 'status':
        monitor.print_status()
    
    elif args.mode == 'export':
        filename = monitor.database.export_to_csv()
        if filename:
            print(f"✅ Data exported to {filename}")
        else:
            print("❌ Export failed")

if __name__ == "__main__":
    main()