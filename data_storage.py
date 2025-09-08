import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from monetary_utils import parse_korean_price

class EncarDatabase:
    def __init__(self, db_path: str = "encar_listings.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self):
        """Get a database connection for manual queries"""
        return sqlite3.connect(self.db_path)
        
    def init_database(self):
        """Create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create listings table with updated schema using 만원 consistently
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS listings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        car_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        model TEXT,
                        year INTEGER,
                        price REAL,  -- Price in millions
                        mileage INTEGER,  -- Mileage as integer
                        views INTEGER,
                        registration_date TEXT,
                        listing_url TEXT,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_coupe BOOLEAN DEFAULT 0,
                        is_new_listing BOOLEAN DEFAULT 1,
                        is_truly_new BOOLEAN DEFAULT 1,  -- Based on registration date + not in DB
                        days_since_registration INTEGER,
                        -- Lease-related columns (all in millions)
                        is_lease BOOLEAN DEFAULT 0,
                        true_price REAL,  -- Total cost in millions (same as price for purchases, calculated for leases)
                        lease_deposit REAL,  -- Initial deposit in millions
                        lease_monthly_payment REAL,  -- Monthly payment in millions
                        lease_term_months INTEGER,  -- Lease term in months
                        lease_total_monthly_cost REAL,  -- Total of all monthly payments in millions
                        final_payment REAL,  -- Final payment at end of lease in millions
                        -- Closure tracking
                        is_closed BOOLEAN DEFAULT 0,  -- Flag for closed/withdrawn listings
                        closure_detected_at TIMESTAMP,  -- When closure was detected
                        closure_type TEXT  -- Type: 'withdrawn', 'sold', 'error_404', etc.
                                   )
                ''')
                
                # Create monitoring log table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitoring_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        action TEXT,
                        details TEXT,
                        new_listings_found INTEGER DEFAULT 0,
                        total_listings_scanned INTEGER DEFAULT 0
                    )
                ''')
                
                # Create system state table for tracking first run, etc.
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_state (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
                # Apply any needed schema updates
                self._apply_schema_updates(cursor)
                conn.commit()
                
                logging.info("Database initialized successfully")
                
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise
    
    def _apply_schema_updates(self, cursor):
        """Apply any needed schema updates for existing databases"""
        try:
            # Check if closure columns exist
            cursor.execute("PRAGMA table_info(listings)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add closure tracking columns if they don't exist
            if 'is_closed' not in columns:
                logging.info("Adding closure tracking columns...")
                cursor.execute("ALTER TABLE listings ADD COLUMN is_closed BOOLEAN DEFAULT 0")
                cursor.execute("ALTER TABLE listings ADD COLUMN closure_detected_at TIMESTAMP")
                cursor.execute("ALTER TABLE listings ADD COLUMN closure_type TEXT")
                logging.info("✅ Closure tracking columns added")
                
        except Exception as e:
            logging.warning(f"Schema update failed (this may be normal for new databases): {e}")
    
    def is_first_run(self) -> bool:
        """Check if this is the first run (database is empty)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM listings")
                count = cursor.fetchone()[0]
                return count == 0
        except Exception as e:
            logging.error(f"Error checking first run: {e}")
            return True
    
    def mark_initial_population_complete(self):
        """Mark that initial database population is complete."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO system_state (key, value)
                    VALUES (?, ?)
                ''', ('initial_population_complete', datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logging.error(f"Error marking initial population complete: {e}")
    
    def parse_registration_date(self, reg_date_str: str) -> Optional[datetime]:
        """Parse Korean registration date string to datetime object."""
        if not reg_date_str:
            return None
        
        try:
            # Handle format like "2025/06/24"
            if '/' in reg_date_str:
                return datetime.strptime(reg_date_str, '%Y/%m/%d')
            # Handle other possible formats
            elif '-' in reg_date_str:
                return datetime.strptime(reg_date_str, '%Y-%m-%d')
            else:
                return None
        except Exception as e:
            logging.warning(f"Could not parse registration date '{reg_date_str}': {e}")
            return None
    
    def calculate_days_since_registration(self, reg_date_str: str) -> Optional[int]:
        """Calculate days since registration date."""
        reg_date = self.parse_registration_date(reg_date_str)
        if reg_date:
            days_diff = (datetime.now() - reg_date).days
            return days_diff
        return None
    
    def parse_price_to_numeric(self, price_value) -> Optional[float]:
        """
        Parse price value and return in millions format.
        
        Args:
            price_value: Price in various formats
            
        Returns:
            Price in millions as float, or None if parsing fails
        """
        if not price_value:
            return None
        
        try:
            # Use the updated monetary utilities
            return parse_korean_price(price_value)
            
        except Exception as e:
            logging.warning(f"Could not parse price '{price_value}': {e}")
            return None
    
    def is_truly_new_listing(self, listing_data: Dict, config: Dict) -> bool:
        """
        Determine if a listing is truly "new" based on the new architecture:
        1. Not in database (primary)
        2. Recent registration date (secondary) 
        3. Low view count (tertiary)
        """
        criteria = config.get('new_listing_criteria', {})
        
        # Check if it exists in database
        if self.listing_exists(listing_data['car_id']):
            return False  # Already seen, not new
        
        # Check registration date recency
        max_age_days = criteria.get('max_registration_age_days', 30)
        days_since_reg = self.calculate_days_since_registration(
            listing_data.get('registration_date', '')
        )
        
        if days_since_reg is not None:
            if days_since_reg > max_age_days:
                # Too old registration, not truly new
                return False
        
        # Check view count (additional indicator)
        max_views = criteria.get('max_views_for_new', 100)
        views = listing_data.get('views', 0)
        
        # If we have both recent registration AND low views, it's definitely new
        if days_since_reg is not None and days_since_reg <= 7 and views <= max_views:
            return True
        
        # If no registration date but very low views, might be new
        if days_since_reg is None and views <= criteria.get('immediate_alert_views', 10):
            return True
        
        # If recent registration but higher views, still consider new
        if days_since_reg is not None and days_since_reg <= max_age_days:
            return True
        
        return False
    
    def listing_exists(self, car_id: str) -> bool:
        """Check if a listing already exists in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM listings WHERE car_id = ?", (car_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking if listing exists: {e}")
            return False
    
    def save_listing(self, listing_data: Dict, config: Dict = None) -> str:
        """
        Save or update a car listing with lease support.
        Returns: 'new', 'updated', or 'existing'
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if listing already exists
                cursor.execute("SELECT id, views, registration_date, days_since_registration, price FROM listings WHERE car_id = ?", 
                             (listing_data['car_id'],))
                row = cursor.fetchone()
                existing = None
                if row:
                    existing = {
                        'id': row[0],
                        'views': row[1], 
                        'registration_date': row[2],
                        'days_since_registration': row[3],
                        'price': row[4]
                    }
                
                # Parse additional data
                days_since_reg = self.calculate_days_since_registration(listing_data.get('registration_date', ''))
                price_millions = self.parse_price_to_numeric(listing_data.get('price', ''))
                
                # Extract lease information
                is_lease = listing_data.get('is_lease', False)
                lease_info = listing_data.get('lease_info', {})
                
                # Extract lease components with new variable naming
                estimated_price = lease_info.get('estimated_price') if lease_info else None  # Previously 'true_price'
                total_cost = lease_info.get('total_cost') if lease_info else None  # This will be mapped to 'true_price' in DB
                lease_deposit = lease_info.get('deposit') if lease_info else None
                lease_monthly_payment = lease_info.get('monthly_payment') if lease_info else None
                lease_term_months = lease_info.get('lease_term_months') if lease_info else None
                final_payment = lease_info.get('final_payment') if lease_info else None
                
                # Calculate total monthly cost if we have monthly payment and term
                if lease_monthly_payment and lease_term_months:
                    lease_total_monthly_cost = lease_monthly_payment * lease_term_months
                else:
                    lease_total_monthly_cost = lease_info.get('total_monthly_cost') if lease_info else None
                
                # Map variables to database columns:
                # - estimated_price -> price (for lease vehicles)
                # - total_cost -> true_price (for lease vehicles)
                # - For non-lease vehicles, use price_millions for both price and true_price
                db_price = estimated_price if is_lease and estimated_price is not None else price_millions
                db_true_price = total_cost if is_lease and total_cost is not None else price_millions
                
                # Determine if truly new (only if config provided)
                is_truly_new = False
                if config and not existing:
                    is_truly_new = self.is_truly_new_listing(listing_data, config)
                
                if existing:
                    # Check if this is an API-only update (no browser data)
                    is_api_only_update = (
                        listing_data.get('api_source', False) and 
                        listing_data.get('views', 0) == 0 and 
                        not listing_data.get('registration_date')
                    )
                    
                    if is_api_only_update and (existing['views'] > 0 or existing['registration_date']):
                        # Preserve existing browser-extracted data
                        self.logger.debug(f"Preserving browser data for {listing_data['car_id']}: views={existing['views']}, reg_date={existing['registration_date']}")
                        preserve_views = existing['views']
                        preserve_registration_date = existing['registration_date']
                        preserve_days_since_reg = existing['days_since_registration']
                    else:
                        # Use new data (normal browser update or first-time data)
                        preserve_views = listing_data['views']
                        preserve_registration_date = listing_data['registration_date']
                        preserve_days_since_reg = days_since_reg
                    
                    # Update existing listing
                    cursor.execute('''
                        UPDATE listings SET 
                            title = ?, model = ?, year = ?, price = ?, mileage = ?,
                            views = ?, registration_date = ?, listing_url = ?, 
                            last_updated = CURRENT_TIMESTAMP, 
                            is_coupe = ?, days_since_registration = ?,
                            is_lease = ?, true_price = ?, lease_deposit = ?, 
                            lease_monthly_payment = ?, lease_term_months = ?, 
                            lease_total_monthly_cost = ?, final_payment = ?
                        WHERE car_id = ?
                    ''', (
                        listing_data['title'], listing_data['model'], 
                        listing_data['year'], db_price,  # Use mapped price
                        listing_data['mileage'], preserve_views,
                        preserve_registration_date, listing_data['listing_url'],
                        listing_data['is_coupe'], preserve_days_since_reg,
                        is_lease, db_true_price, lease_deposit,  # Use mapped true_price
                        lease_monthly_payment, lease_term_months,
                        lease_total_monthly_cost, final_payment,
                        listing_data['car_id']
                    ))
                    
                    conn.commit()
                    return 'updated'
                    
                else:
                    # Insert new listing
                    cursor.execute('''
                        INSERT INTO listings (
                            car_id, title, model, year, price, mileage, views,
                            registration_date, listing_url, is_coupe, is_truly_new, 
                            days_since_registration, is_lease, true_price,
                                                                      lease_deposit, lease_monthly_payment, lease_term_months,
                                          lease_total_monthly_cost, final_payment
                                      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        listing_data['car_id'], listing_data['title'], 
                        listing_data['model'], listing_data['year'],
                        db_price, listing_data['mileage'],  # Use mapped price
                        listing_data['views'], listing_data['registration_date'],
                        listing_data['listing_url'], listing_data['is_coupe'], 
                        is_truly_new, days_since_reg, is_lease, db_true_price,  # Use mapped true_price
                                                              lease_deposit, lease_monthly_payment, lease_term_months,
                                      lease_total_monthly_cost, final_payment
                    ))
                    
                    conn.commit()
                    return 'new'
                    
        except Exception as e:
            logging.error(f"Error saving listing {listing_data.get('car_id', 'unknown')}: {e}")
            return 'error'
    
    def update_listing_data(self, car_id: str, views: int = None, registration_date: str = None, 
                           is_lease: bool = None, lease_info: Dict = None) -> bool:
        """
        Update specific fields for an existing listing.
        Used for enhancing existing listings with missing data.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if listing exists
                cursor.execute("SELECT id FROM listings WHERE car_id = ?", (car_id,))
                if not cursor.fetchone():
                    logging.warning(f"Listing {car_id} not found for update")
                    return False
                
                # Build update query dynamically based on provided fields
                update_fields = []
                update_values = []
                
                if views is not None:
                    update_fields.append("views = ?")
                    update_values.append(views)
                
                if registration_date is not None:
                    update_fields.append("registration_date = ?")
                    update_values.append(registration_date)
                    # Recalculate days since registration
                    days_since_reg = self.calculate_days_since_registration(registration_date)
                    if days_since_reg is not None:
                        update_fields.append("days_since_registration = ?")
                        update_values.append(days_since_reg)
                
                if is_lease is not None:
                    update_fields.append("is_lease = ?")
                    update_values.append(is_lease)
                
                if lease_info is not None:
                    # Extract lease components with new variable naming
                    estimated_price = lease_info.get('estimated_price')  # Previously 'true_price'
                    total_cost = lease_info.get('total_cost')  # This will be mapped to 'true_price' in DB
                    lease_deposit = lease_info.get('deposit')
                    lease_monthly_payment = lease_info.get('monthly_payment')
                    lease_term_months = lease_info.get('lease_term_months')
                    lease_total_monthly_cost = lease_info.get('total_monthly_cost')
                    final_payment = lease_info.get('final_payment')
                    
                    # Map variables to database columns
                    if estimated_price is not None:
                        update_fields.append("price = ?")
                        update_values.append(estimated_price)
                    
                    if total_cost is not None:
                        update_fields.append("true_price = ?")
                        update_values.append(total_cost)
                    
                    if lease_deposit is not None:
                        update_fields.append("lease_deposit = ?")
                        update_values.append(lease_deposit)
                    
                    if lease_monthly_payment is not None:
                        update_fields.append("lease_monthly_payment = ?")
                        update_values.append(lease_monthly_payment)
                    
                    if lease_term_months is not None:
                        update_fields.append("lease_term_months = ?")
                        update_values.append(lease_term_months)
                    
                    if lease_total_monthly_cost is not None:
                        update_fields.append("lease_total_monthly_cost = ?")
                        update_values.append(lease_total_monthly_cost)
                    
                    if final_payment is not None:
                        update_fields.append("final_payment = ?")
                        update_values.append(final_payment)
                
                # Always update the last_updated timestamp
                update_fields.append("last_updated = CURRENT_TIMESTAMP")
                
                if not update_fields:
                    logging.warning(f"No fields to update for {car_id}")
                    return False
                
                # Execute update
                update_query = f"UPDATE listings SET {', '.join(update_fields)} WHERE car_id = ?"
                update_values.append(car_id)
                
                cursor.execute(update_query, update_values)
                conn.commit()
                
                logging.debug(f"Updated listing {car_id} with fields: {update_fields}")
                return True
                
        except Exception as e:
            logging.error(f"Error updating listing {car_id}: {e}")
            return False
    
    def mark_listing_closed(self, car_id: str, closure_type: str = 'withdrawn') -> bool:
        """
        Mark a listing as closed/withdrawn.
        
        Args:
            car_id: The car ID to mark as closed
            closure_type: Type of closure ('withdrawn', 'sold', 'error_404', 'access_denied', etc.)
        
        Returns:
            True if successfully marked as closed, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if listing exists
                cursor.execute("SELECT id FROM listings WHERE car_id = ?", (car_id,))
                if not cursor.fetchone():
                    logging.warning(f"Listing {car_id} not found for closure marking")
                    return False
                
                # Update closure status
                cursor.execute("""
                    UPDATE listings 
                    SET is_closed = 1,
                        closure_detected_at = CURRENT_TIMESTAMP,
                        closure_type = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE car_id = ?
                """, (closure_type, car_id))
                
                conn.commit()
                logging.info(f"✅ Marked listing {car_id} as closed ({closure_type})")
                return True
                
        except Exception as e:
            logging.error(f"Error marking listing {car_id} as closed: {e}")
            return False
    
    def get_active_listings(self) -> List[Dict]:
        """Get all active (non-closed) listings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT car_id, title, listing_url, price, views, registration_date,
                           is_lease, first_seen, last_updated
                    FROM listings 
                    WHERE is_closed = 0
                    ORDER BY first_seen DESC
                """)
                
                rows = cursor.fetchall()
                
                listings = []
                for row in rows:
                    listing = {
                        'car_id': row[0],
                        'title': row[1],
                        'listing_url': row[2],
                        'price': row[3],
                        'views': row[4],
                        'registration_date': row[5],
                        'is_lease': bool(row[6]),
                        'first_seen': row[7],
                        'last_updated': row[8]
                    }
                    listings.append(listing)
                
                return listings
                
        except Exception as e:
            logging.error(f"Error getting active listings: {e}")
            return []
    
    def get_closure_statistics(self) -> Dict:
        """Get statistics about closed listings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total listings
                cursor.execute("SELECT COUNT(*) FROM listings")
                total_listings = cursor.fetchone()[0]
                
                # Active listings
                cursor.execute("SELECT COUNT(*) FROM listings WHERE is_closed = 0")
                active_listings = cursor.fetchone()[0]
                
                # Closed listings
                cursor.execute("SELECT COUNT(*) FROM listings WHERE is_closed = 1")
                closed_listings = cursor.fetchone()[0]
                
                # Closed by type
                cursor.execute("""
                    SELECT closure_type, COUNT(*) 
                    FROM listings 
                    WHERE is_closed = 1 
                    GROUP BY closure_type
                """)
                closure_types = dict(cursor.fetchall())
                
                return {
                    'total_listings': total_listings,
                    'active_listings': active_listings,
                    'closed_listings': closed_listings,
                    'closure_rate': f"{(closed_listings/total_listings*100):.1f}%" if total_listings > 0 else "0%",
                    'closure_types': closure_types
                }
                
        except Exception as e:
            logging.error(f"Error getting closure statistics: {e}")
            return {}
    
    def get_truly_new_listings(self, config: Dict = None, minutes_threshold: int = 15) -> List[Dict]:
        """Get listings that are truly new based on recent first_seen timestamp."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get listings that were first seen within the last X minutes AND are truly new
                # This ensures we only get listings from the current monitoring cycle
                threshold_time = datetime.now() - timedelta(minutes=minutes_threshold)
                
                cursor.execute('''
                    SELECT * FROM listings 
                    WHERE is_truly_new = 1 
                      AND is_coupe = 1 
                      AND first_seen >= ?
                      AND is_closed = 0
                    ORDER BY first_seen DESC
                ''', (threshold_time.strftime('%Y-%m-%d %H:%M:%S'),))
                
                columns = [description[0] for description in cursor.description]
                listings = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Mark these listings as no longer "truly new" to avoid duplicate notifications
                if listings:
                    car_ids = [listing['car_id'] for listing in listings]
                    placeholders = ','.join(['?' for _ in car_ids])
                    cursor.execute(f'''
                        UPDATE listings 
                        SET is_truly_new = 0
                        WHERE car_id IN ({placeholders})
                    ''', car_ids)
                    conn.commit()
                    
                    self.logger.info(f"📝 Marked {len(listings)} listings as processed (no longer truly new)")
                
                return listings
                
        except Exception as e:
            logging.error(f"Error retrieving truly new listings: {e}")
            return []
    
    def get_recent_registrations(self, max_days: int = 7) -> List[Dict]:
        """Get listings with recent registration dates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM listings 
                    WHERE days_since_registration <= ? AND is_coupe = 1 
                    ORDER BY registration_date_parsed DESC
                ''', (max_days,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Error retrieving recent registrations: {e}")
            return []
    
    def get_new_listings(self, max_views: int = 5) -> List[Dict]:
        """Get listings that are considered 'new' based on view count (legacy method)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM listings 
                    WHERE views <= ? AND is_coupe = 1 
                    ORDER BY first_seen DESC
                ''', (max_views,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Error retrieving new listings: {e}")
            return []
    
    def get_coupe_listings(self) -> List[Dict]:
        """Get all coupe listings."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM listings 
                    WHERE is_coupe = 1 
                    ORDER BY last_updated DESC
                ''')
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Error retrieving coupe listings: {e}")
            return []
    
    def log_monitoring_action(self, action: str, details: str = "", new_listings: int = 0, total_scanned: int = 0):
        """Log monitoring activity with enhanced tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO monitoring_log (action, details, new_listings_found, total_listings_scanned)
                    VALUES (?, ?, ?, ?)
                ''', (action, details, new_listings, total_scanned))
                conn.commit()
                
        except Exception as e:
            logging.error(f"Error logging monitoring action: {e}")
    
    def cleanup_old_data(self, days: int = 30):
        """Remove old listings and logs."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean old listings that are no longer relevant
                cursor.execute('''
                    DELETE FROM listings 
                    WHERE last_updated < ? AND views > 100 AND is_truly_new = 0
                ''', (cutoff_date,))
                
                # Clean old monitoring logs
                cursor.execute('''
                    DELETE FROM monitoring_log 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                conn.commit()
                logging.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")
    
    def get_statistics(self) -> Dict:
        """Get monitoring statistics with enhanced metrics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total listings
                cursor.execute("SELECT COUNT(*) FROM listings")
                stats['total_listings'] = cursor.fetchone()[0]
                
                # Coupe listings
                cursor.execute("SELECT COUNT(*) FROM listings WHERE is_coupe = 1")
                stats['coupe_listings'] = cursor.fetchone()[0]
                
                # Truly new listings
                cursor.execute("SELECT COUNT(*) FROM listings WHERE is_truly_new = 1 AND is_coupe = 1")
                stats['truly_new_listings'] = cursor.fetchone()[0]
                
                # Recent registrations (last 7 days)
                cursor.execute("SELECT COUNT(*) FROM listings WHERE days_since_registration <= 7 AND is_coupe = 1")
                stats['recent_registrations'] = cursor.fetchone()[0]
                
                # Low view listings
                cursor.execute("SELECT COUNT(*) FROM listings WHERE views <= 10 AND is_coupe = 1")
                stats['low_view_listings'] = cursor.fetchone()[0]
                
                # Last monitoring run
                cursor.execute("SELECT MAX(timestamp) FROM monitoring_log")
                stats['last_check'] = cursor.fetchone()[0]
                
                # Average registration age
                cursor.execute("SELECT AVG(days_since_registration) FROM listings WHERE is_coupe = 1 AND days_since_registration IS NOT NULL")
                avg_age = cursor.fetchone()[0]
                stats['avg_registration_age_days'] = round(avg_age, 1) if avg_age else None
                
                return stats
                
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return {}
    
    # def export_to_csv(self, filename: str = None) -> str:
    #     """Export database to CSV file."""
    #     try:
    #         if not filename:
    #             filename = f"encar_listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
    #         with sqlite3.connect(self.db_path) as conn:
    #             df = pd.read_sql_query("""
    #                 SELECT 
    #                     car_id, title, model, year, price, mileage, views,
    #                     registration_date, listing_url, is_coupe, is_lease,
    #                     true_price, lease_deposit, lease_monthly_payment, lease_term_months,
    #                     first_seen, last_updated
    #                 FROM listings 
    #                 WHERE is_coupe = 1
    #                 ORDER BY last_updated DESC
    #             """, conn)
                
    #             df.to_csv(filename, index=False, encoding='utf-8-sig')
                
    #             print(f"✅ Exported {len(df)} listings to {filename}")
    #             return filename
                
    #     except Exception as e:
    #         logging.error(f"Error exporting to CSV: {e}")
    #         return None

    # ===== CONSOLIDATED DATABASE QUERY OPERATIONS =====
    
    def get_database_deals(self, deal_type: str = "all", limit: int = 5) -> List[Dict]:
        """
        Get deals from database (consolidated from database_deals.py)
        
        Args:
            deal_type: "lease_only", "purchase_only", "best_value", "recent", "all"
            limit: Maximum number of results
            
        Returns:
            List of deal dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if deal_type == "lease_only":
                    cursor.execute("""
                        SELECT title, price_numeric, true_price, car_id, year,
                               lease_deposit, lease_monthly_payment, lease_term_months
                        FROM listings 
                        WHERE is_lease = 1 AND is_coupe = 1
                        ORDER BY true_price ASC
                        LIMIT ?
                    """, (limit,))
                    
                elif deal_type == "purchase_only":
                    cursor.execute("""
                        SELECT title, price_numeric, true_price, car_id, year
                        FROM listings 
                        WHERE is_lease = 0 AND is_coupe = 1
                        ORDER BY true_price ASC
                        LIMIT ?
                    """, (limit,))
                    
                elif deal_type == "best_value":
                    cursor.execute("""
                        SELECT title, price_numeric, true_price, is_lease, car_id, year,
                               lease_deposit, lease_monthly_payment, lease_term_months
                        FROM listings 
                        WHERE is_coupe = 1 AND true_price IS NOT NULL
                        ORDER BY true_price ASC
                        LIMIT ?
                    """, (limit,))
                    
                elif deal_type == "recent":
                    cursor.execute("""
                        SELECT title, price_numeric, true_price, is_lease, car_id, year,
                               lease_deposit, lease_monthly_payment, lease_term_months
                        FROM listings 
                        WHERE is_coupe = 1 AND year >= 202200
                        ORDER BY true_price ASC
                        LIMIT ?
                    """, (limit,))
                    
                else:  # all
                    cursor.execute("""
                        SELECT title, price_numeric, true_price, is_lease, car_id, year,
                               lease_deposit, lease_monthly_payment, lease_term_months
                        FROM listings 
                        WHERE is_coupe = 1
                        ORDER BY true_price ASC
                        LIMIT ?
                    """, (limit,))
                
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                deals = []
                for row in results:
                    if deal_type == "lease_only":
                        title, price_numeric, true_price, car_id, year, deposit, monthly, term = row
                        deals.append({
                            'title': title,
                            'price_numeric': price_numeric,
                            'true_price': true_price,
                            'car_id': car_id,
                            'year': year,
                            'is_lease': True,
                            'lease_deposit': deposit,
                            'lease_monthly_payment': monthly,
                            'lease_term_months': term
                        })
                    elif deal_type == "purchase_only":
                        title, price_numeric, true_price, car_id, year = row
                        deals.append({
                            'title': title,
                            'price_numeric': price_numeric,
                            'true_price': true_price,
                            'car_id': car_id,
                            'year': year,
                            'is_lease': False
                        })
                    else:  # Mixed results
                        title, price_numeric, true_price, is_lease, car_id, year, deposit, monthly, term = row
                        deals.append({
                            'title': title,
                            'price_numeric': price_numeric,
                            'true_price': true_price,
                            'is_lease': bool(is_lease),
                            'car_id': car_id,
                            'year': year,
                            'lease_deposit': deposit,
                            'lease_monthly_payment': monthly,
                            'lease_term_months': term
                        })
                
                return deals
                
        except Exception as e:
            logging.error(f"Error getting database deals: {e}")
            return []
    
    def get_enhanced_database_analysis(self) -> Dict:
        """
        Get comprehensive database analysis (consolidated from database_query_enhanced.py)
        
        Returns:
            Dictionary with analysis results
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                analysis = {}
                
                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM listings WHERE is_coupe = 1")
                coupe_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM listings WHERE is_lease = 1 AND is_coupe = 1")
                lease_count = cursor.fetchone()[0]
                
                purchase_count = coupe_count - lease_count
                
                analysis['basic_counts'] = {
                    'total_coupes': coupe_count,
                    'lease_vehicles': lease_count,
                    'purchase_vehicles': purchase_count
                }
                
                # Year distribution
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN year > 10000 THEN CAST(year/100 AS INTEGER)
                            ELSE year 
                        END as display_year, 
                        COUNT(*) 
                    FROM listings 
                    WHERE is_coupe = 1 
                    GROUP BY display_year
                    ORDER BY display_year DESC
                """)
                analysis['year_distribution'] = dict(cursor.fetchall())
                
                # Price ranges using true_price
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN true_price < 5000 THEN 'Under 5000만원'
                            WHEN true_price < 7000 THEN '5000-7000만원'
                            WHEN true_price < 9000 THEN '7000-9000만원'
                            ELSE 'Over 9000만원'
                        END as price_range,
                        COUNT(*)
                    FROM listings 
                    WHERE is_coupe = 1 AND true_price IS NOT NULL
                    GROUP BY 
                        CASE 
                            WHEN true_price < 5000 THEN 'Under 5000만원'
                            WHEN true_price < 7000 THEN '5000-7000만원'
                            WHEN true_price < 9000 THEN '7000-9000만원'
                            ELSE 'Over 9000만원'
                        END
                    ORDER BY MIN(true_price)
                """)
                analysis['price_distribution'] = dict(cursor.fetchall())
                
                # Lease vehicle analysis
                if lease_count > 0:
                    cursor.execute("""
                        SELECT 
                            AVG(price_numeric) as avg_listed_price,
                            AVG(true_price) as avg_true_cost,
                            AVG(lease_deposit) as avg_deposit,
                            AVG(lease_monthly_payment) as avg_monthly,
                            AVG(lease_term_months) as avg_term
                        FROM listings 
                        WHERE is_lease = 1 AND is_coupe = 1
                    """)
                    result = cursor.fetchone()
                    if result and result[0]:
                        avg_listed, avg_true, avg_deposit, avg_monthly, avg_term = result
                        analysis['lease_analysis'] = {
                            'avg_listed_price': avg_listed,
                            'avg_true_cost': avg_true,
                            'avg_cost_increase': avg_true - avg_listed,
                            'avg_deposit': avg_deposit,
                            'avg_monthly_payment': avg_monthly,
                            'avg_term_months': avg_term
                        }
                
                # Recent additions
                cursor.execute("""
                    SELECT title, price_numeric, true_price, is_lease, car_id, year, views, registration_date
                    FROM listings 
                    WHERE is_coupe = 1 
                    ORDER BY id DESC 
                    LIMIT 5
                """)
                recent_additions = []
                for row in cursor.fetchall():
                    title, price_numeric, true_price, is_lease, car_id, year, views, reg_date = row
                    recent_additions.append({
                        'title': title,
                        'price_numeric': price_numeric,
                        'true_price': true_price,
                        'is_lease': bool(is_lease),
                        'car_id': car_id,
                        'year': year,
                        'views': views,
                        'registration_date': reg_date
                    })
                analysis['recent_additions'] = recent_additions
                
                return analysis
                
        except Exception as e:
            logging.error(f"Error getting enhanced database analysis: {e}")
            return {}
    
    def print_database_analysis(self, analysis: Dict = None):
        """Print formatted database analysis"""
        if analysis is None:
            analysis = self.get_enhanced_database_analysis()
        
        print("\n=== DATABASE ANALYSIS ===")
        
        # Basic counts
        basic = analysis.get('basic_counts', {})
        print(f"📊 Total coupe vehicles: {basic.get('total_coupes', 0)}")
        print(f"🏪 Purchase vehicles: {basic.get('purchase_vehicles', 0)}")
        print(f"🚗 Lease vehicles: {basic.get('lease_vehicles', 0)}")
        print()
        
        # Year distribution
        print("📅 BY YEAR:")
        year_dist = analysis.get('year_distribution', {})
        for year, count in year_dist.items():
            print(f"   {year}: {count} vehicles")
        print()
        
        # Price ranges
        print("💰 BY TRUE PRICE RANGE:")
        price_dist = analysis.get('price_distribution', {})
        for price_range, count in price_dist.items():
            print(f"   {price_range}: {count} vehicles")
        print()
        
        # Lease analysis
        lease_analysis = analysis.get('lease_analysis')
        if lease_analysis:
            print("🚗 LEASE VEHICLE ANALYSIS:")
            print(f"   Average listed price: {lease_analysis['avg_listed_price']:,.0f}만원")
            print(f"   Average true cost: {lease_analysis['avg_true_cost']:,.0f}만원")
            print(f"   Average cost increase: {lease_analysis['avg_cost_increase']:,.0f}만원")
            if lease_analysis['avg_deposit']:
                print(f"   Average deposit: {lease_analysis['avg_deposit']:,.0f}만원")
            if lease_analysis['avg_monthly_payment']:
                print(f"   Average monthly: {lease_analysis['avg_monthly_payment']:,.0f}만원")
            if lease_analysis['avg_term_months']:
                print(f"   Average term: {lease_analysis['avg_term_months']:.0f} months")
            print()
        
        # Recent additions
        print("🕒 MOST RECENT ADDITIONS (Top 5):")
        recent = analysis.get('recent_additions', [])
        for i, vehicle in enumerate(recent, 1):
            year = vehicle['year']
            display_year = int(year / 100) if year and year > 10000 else year
            lease_flag = "🚗 LEASE" if vehicle['is_lease'] else "🏪 PURCHASE"
            
            print(f"   {i}. {vehicle['title']} ({display_year})")
            
            if vehicle['is_lease'] and vehicle['true_price'] and vehicle['price_numeric'] and vehicle['true_price'] != vehicle['price_numeric']:
                print(f"      {lease_flag} - Listed: {vehicle['price_numeric']:,.0f}만원 → True: {vehicle['true_price']:,.0f}만원")
            elif vehicle['price_numeric']:
                print(f"      {lease_flag} - {vehicle['price_numeric']:,.0f}만원")
            else:
                print(f"      {lease_flag} - Price N/A")
            
            print(f"      🔗 https://fem.encar.com/cars/detail/{vehicle['car_id']}")
            print()

    def get_recent_listings(self, hours: int = 24) -> List[Dict]:
        """Get listings added in the last N hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate the cutoff time
                cutoff_time = datetime.now() - timedelta(hours=hours)
                cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
                
                cursor.execute('''
                    SELECT car_id, title, model, year, price, mileage, views, 
                           registration_date, listing_url, first_seen, is_coupe, is_lease
                    FROM listings 
                    WHERE first_seen >= ?
                    ORDER BY first_seen DESC
                ''', (cutoff_str,))
                
                rows = cursor.fetchall()
                listings = []
                
                for row in rows:
                    listing = {
                        'car_id': row[0],
                        'title': row[1],
                        'model': row[2],
                        'year': row[3],
                        'price': row[4],
                        'mileage': row[5],
                        'views': row[6],
                        'registration_date': row[7],
                        'listing_url': row[8],
                        'first_seen': row[9],
                        'is_coupe': bool(row[10]),
                        'is_lease': bool(row[11])
                    }
                    listings.append(listing)
                
                self.logger.debug(f"Found {len(listings)} listings in last {hours} hours")
                return listings
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting recent listings: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error getting recent listings: {e}")
            return []

    def cleanup_old_listings(self, days_to_keep: int = 90) -> int:
        """Remove listings older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate cutoff date
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
                
                # Count records to be deleted
                cursor.execute('''
                    SELECT COUNT(*) FROM listings 
                    WHERE first_seen < ?
                ''', (cutoff_str,))
                
                count_to_delete = cursor.fetchone()[0]
                
                if count_to_delete > 0:
                    # Delete old records
                    cursor.execute('''
                        DELETE FROM listings 
                        WHERE first_seen < ?
                    ''', (cutoff_str,))
                    
                    conn.commit()
                    self.logger.info(f"Cleaned up {count_to_delete} old listings (older than {days_to_keep} days)")
                else:
                    self.logger.info("No old listings to clean up")
                
                return count_to_delete
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error during cleanup: {e}")
            return 0
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return 0