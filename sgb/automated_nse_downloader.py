#!/usr/bin/env python3
"""
Automated NSE SGB Downloader
- Downloads at specified time daily
- Saves with consistent naming
- Deletes old files when new file downloads
- Robust error handling and logging
"""

import requests
import os
import logging
import schedule
import time
from datetime import datetime
import sys
from pathlib import Path
import shutil

class AutomatedNSEDownloader:
    def __init__(self, download_dir="nse_gold_data", log_dir="logs", download_time="10:30"):
        self.csv_url = "https://www.nseindia.com/api/sovereign-gold-bonds?csv=true&selectValFormat=crores"
        self.base_url = "https://www.nseindia.com"
        self.sgb_page_url = "https://www.nseindia.com/market-data/sovereign-gold-bond"
        self.download_dir = Path(download_dir)
        self.log_dir = Path(log_dir)
        self.download_time = download_time
        
     
        self.download_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        
        self.setup_logging()
        
       
        self.session = None
    
    def setup_logging(self):
        """Setup logging to both file and console"""
        self.logger = logging.getLogger('AutomatedNSEDownloader')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        
        log_file = self.log_dir / f"nse_automation_{datetime.now().strftime('%Y%m')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
       
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def create_session(self):
        """Create simple browser session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        return session
    
    def fix_csv_structure(self, raw_content):
        """Fix the malformed CSV structure and encoding"""
        try:
            self.logger.info("🔧 Processing CSV data...")
            
            
            content = raw_content
            if content.startswith('\ufeff'):
                content = content[1:]
            if content.startswith('ï»¿'):
                content = content[3:]
            
            
            content = content.replace('â\x82¹', '₹')
            content = content.replace('â¹', '₹')
            content = content.replace('â‚¹', '₹')
            
            
            lines = content.split('\n')
            data_start_index = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('"SGB'):
                    data_start_index = i
                    break
            
            if data_start_index == -1:
                self.logger.error("❌ Could not find SGB data")
                return None
            
            
            header_lines = lines[:data_start_index]
            data_lines = lines[data_start_index:]
            
            header_content = ''.join(header_lines)
            header_content = header_content.replace(' \n', '').replace('\n ', '').replace('\n', '')
            header_line = header_content.strip()
            
            
            clean_data_lines = []
            for line in data_lines:
                line = line.strip()
                if line and not line.startswith('"SYMBOL'):
                    clean_data_lines.append(line)
            
           
            fixed_csv_lines = [header_line] + clean_data_lines
            fixed_content = '\n'.join(fixed_csv_lines)
            
            fixed_content = fixed_content.replace('â\x82¹', '₹')
            fixed_content = fixed_content.replace('â¹', '₹')
            
           
            test_lines = fixed_content.split('\n')
            if test_lines:
                header = test_lines[0]
                comma_count = header.count(',')
                data_rows = len([l for l in test_lines[1:] if l.strip()])
                
                self.logger.info(f"✅ Processed CSV: {comma_count + 1} columns, {data_rows} data rows")
                
                if '₹' in header:
                    self.logger.info("✅ Currency symbols fixed")
            
            return fixed_content
            
        except Exception as e:
            self.logger.error(f"❌ CSV processing error: {str(e)}")
            return None
    
    def delete_old_files(self):
        """Delete old CSV files before downloading new one"""
        try:
            deleted_files = []
            
            
            for file_path in self.download_dir.glob("*sgb*.csv"):
                try:
                    file_path.unlink()
                    deleted_files.append(file_path.name)
                except Exception as e:
                    self.logger.warning(f"⚠️  Could not delete {file_path.name}: {e}")
            
            if deleted_files:
                self.logger.info(f"🗑️  Deleted old files: {', '.join(deleted_files)}")
            else:
                self.logger.info("📁 No old files to delete")
                
        except Exception as e:
            self.logger.error(f"❌ Error deleting old files: {str(e)}")
    
    def download_sgb_csv(self):
        """Download and process SGB CSV"""
        try:
            self.logger.info("🚀 Starting automated SGB download...")
            
            
            self.session = self.create_session()
            
            
            self.logger.info("🏠 Establishing session...")
            homepage_response = self.session.get(self.base_url, timeout=30)
            
            if homepage_response.status_code != 200:
                self.logger.error(f"❌ Homepage failed: {homepage_response.status_code}")
                return False
            
            
            sgb_response = self.session.get(self.sgb_page_url, timeout=30)
            
            if sgb_response.status_code != 200:
                self.logger.error(f"❌ SGB page failed: {sgb_response.status_code}")
                return False
            
            
            time.sleep(2)
            
            self.logger.info("📥 Downloading SGB data...")
            csv_response = self.session.get(self.csv_url, timeout=30)
            
            if csv_response.status_code != 200:
                self.logger.error(f"❌ CSV download failed: {csv_response.status_code}")
                return False
            
            
            raw_content = csv_response.text
            fixed_content = self.fix_csv_structure(raw_content)
            
            if not fixed_content:
                self.logger.error("❌ Failed to process CSV")
                return False
            
            
            self.delete_old_files()
            
        
            today = datetime.now()
            filename = f"NSE_SGB_{today.strftime('%Y%m%d')}.csv"
            filepath = self.download_dir / filename
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(fixed_content)
            
            file_size = len(fixed_content)
            lines_count = len([l for l in fixed_content.split('\n') if l.strip()])
            
            self.logger.info("✅ Download completed successfully!")
            self.logger.info(f"📁 File: {filename}")
            self.logger.info(f"📊 Size: {file_size:,} characters, {lines_count} lines")
            self.logger.info(f"💾 Location: {filepath}")
            
            
            lines = fixed_content.split('\n')
            if len(lines) >= 2:
                header = lines[0][:100] + "..." if len(lines[0]) > 100 else lines[0]
                sample = lines[1][:100] + "..." if len(lines[1]) > 100 else lines[1]
                self.logger.info(f"📋 Header: {header}")
                self.logger.info(f"📋 Sample: {sample}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Download error: {str(e)}")
            return False
    
    def scheduled_download(self):
        """Wrapper for scheduled downloads with comprehensive logging"""
        self.logger.info("=" * 80)
        self.logger.info(f"🕐 Scheduled download started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        success = self.download_sgb_csv()
        
        if success:
            self.logger.info("🎉 Scheduled download completed successfully!")
        else:
            self.logger.error("💥 Scheduled download failed!")
        
        self.logger.info("=" * 80)
        return success
    
    def start_automation(self):
        """Start the automated download system"""
        print(f"🤖 NSE SGB Automated Downloader")
        print(f"⏰ Download time: {self.download_time} daily")
        print(f"📁 Download directory: {self.download_dir.absolute()}")
        print(f"📝 Log directory: {self.log_dir.absolute()}")
        print(f"🔄 File naming: NSE_SGB_YYYYMMDD.csv")
        print(f"🗑️  Old files deleted automatically")
        print()
        
        
        schedule.every().day.at(self.download_time).do(self.scheduled_download)
        
        print(f"✅ Automation started! Next download at {self.download_time}")
        print("🔄 Running continuously... Press Ctrl+C to stop")
        print("-" * 80)
        
        
        user_input = input("Run test download now? (y/n): ").lower().strip()
        if user_input in ['y', 'yes']:
            print("\n🧪 Running test download...")
            result = self.scheduled_download()
            if result:
                print("✅ Test successful! Automation is working correctly.")
            else:
                print("❌ Test failed! Check logs above.")
            print()
        
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  
        except KeyboardInterrupt:
            self.logger.info("🛑 Automation stopped by user")
            print("\n👋 NSE SGB Downloader stopped.")

def main():
    """Main function to start automation"""
    
    
    DOWNLOAD_TIME = "23:56"     
    DOWNLOAD_DIR = "nse_sgb_data" 
    LOG_DIR = "logs"             
    
    print("🚀 NSE SGB Automation Setup")
    print("=" * 50)
    print(f"Default download time: {DOWNLOAD_TIME}")
    print(f"Default download directory: {DOWNLOAD_DIR}")
    print()
    
    
    custom_time = input(f"Enter download time (HH:MM) or press Enter for {DOWNLOAD_TIME}: ").strip()
    if custom_time and ':' in custom_time:
        try:
            
            hour, minute = custom_time.split(':')
            if 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59:
                DOWNLOAD_TIME = custom_time
                print(f"✅ Download time set to: {DOWNLOAD_TIME}")
            else:
                print(f"⚠️  Invalid time format, using default: {DOWNLOAD_TIME}")
        except:
            print(f"⚠️  Invalid time format, using default: {DOWNLOAD_TIME}")
    
    
    downloader = AutomatedNSEDownloader(
        download_dir=DOWNLOAD_DIR,
        log_dir=LOG_DIR,
        download_time=DOWNLOAD_TIME
    )
    
    downloader.start_automation()

if __name__ == "__main__":
    main()
