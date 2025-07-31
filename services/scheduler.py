import schedule
import time
import threading
import logging
from datetime import datetime
from .resource_scraper import EducationalResourceScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceScheduler:
    """
    Scheduler for automated resource updates
    """
    
    def __init__(self):
        self.scraper = EducationalResourceScraper()
        self.is_running = False
        self.scheduler_thread = None
    
    def run_weekly_update(self):
        """Run weekly resource update"""
        try:
            logger.info("Starting scheduled weekly resource update...")
            result = self.scraper.run_full_scrape()
            logger.info(f"Weekly update completed: {result}")
            
            # You could add email notifications here for admins
            # self.send_admin_notification(result)
            
        except Exception as e:
            logger.error(f"Error in weekly update: {e}")
    
    def run_daily_check(self):
        """Run daily check for critical updates"""
        try:
            logger.info("Running daily resource check...")
            
            # Check for new exam papers (more frequent during exam season)
            exam_resources = []
            
            # Quick check for new exam papers from DBE
            dbe_resources = self.scraper.scrape_dbe_resources()
            exam_resources.extend([r for r in dbe_resources if 'exam' in r['resource_type'].lower()])
            
            if exam_resources:
                logger.info(f"Found {len(exam_resources)} new exam resources")
                for resource in exam_resources:
                    self.scraper.download_file(
                        resource['url'],
                        resource['filename'],
                        resource['grade'],
                        resource['subject'],
                        resource['resource_type'],
                        resource['source']
                    )
            
        except Exception as e:
            logger.error(f"Error in daily check: {e}")
    
    def start_scheduler(self):
        """Start the scheduler in a separate thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule weekly full update (Sundays at 2 AM)
        schedule.every().sunday.at("02:00").do(self.run_weekly_update)
        
        # Schedule daily check for exam papers (every day at 6 AM)
        schedule.every().day.at("06:00").do(self.run_daily_check)
        
        self.is_running = True
        
        def run_scheduler():
            logger.info("Resource scheduler started")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            logger.info("Resource scheduler stopped")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def force_update(self):
        """Force an immediate update (for admin use)"""
        logger.info("Force update requested")
        return self.run_weekly_update()

# Global scheduler instance
resource_scheduler = ResourceScheduler()
