#!/usr/bin/env python3
"""
Splunk Universal Forwarder Script Input - CSV to JSON Converter
Real-time CSV data ingestion script for Splunk UF script-based inputs.
Monitors CSV files and outputs new records as JSON events to stdout.
"""

import os
import sys
import csv
import json
import time
import glob
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

class SplunkCSVInput:
    def __init__(self, data_dir: str = "data", state_dir: str = "state", 
                 poll_interval: int = 10, sourcetype: str = "csv_data"):
        """
        Initialize the Splunk CSV input script.
        
        Args:
            data_dir: Directory to monitor for CSV files
            state_dir: Directory to store state files
            poll_interval: Seconds between file checks
            sourcetype: Splunk sourcetype for events
        """
        self.data_dir = Path(data_dir)
        self.state_dir = Path(state_dir)
        self.poll_interval = poll_interval
        self.sourcetype = sourcetype
        
        # Create state directory if it doesn't exist
        self.state_dir.mkdir(exist_ok=True)
        
        # Setup logging to stderr (stdout is reserved for Splunk events)
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Track processed files and their states
        self.file_states = {}
        self.load_state()
    
    def load_state(self) -> None:
        """Load processing state from disk."""
        state_file = self.state_dir / "csv_state.json"
        try:
            if state_file.exists():
                with open(state_file, 'r') as f:
                    self.file_states = json.load(f)
                self.logger.info(f"Loaded state for {len(self.file_states)} files")
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
            self.file_states = {}
    
    def save_state(self) -> None:
        """Save processing state to disk."""
        state_file = self.state_dir / "csv_state.json"
        try:
            with open(state_file, 'w') as f:
                json.dump(self.file_states, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file for change detection."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Error hashing file {file_path}: {e}")
            return ""
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if file needs processing based on modification time and hash."""
        file_str = str(file_path)
        
        try:
            stat = file_path.stat()
            current_mtime = stat.st_mtime
            current_size = stat.st_size
            current_hash = self.get_file_hash(file_path)
            
            if file_str not in self.file_states:
                # New file
                self.file_states[file_str] = {
                    "last_mtime": current_mtime,
                    "last_size": current_size,
                    "last_hash": current_hash,
                    "last_row": 0
                }
                return True
            
            state = self.file_states[file_str]
            
            # Check if file has been modified
            if (current_mtime != state["last_mtime"] or 
                current_size != state["last_size"] or 
                current_hash != state["last_hash"]):
                
                # File has changed, update state
                state["last_mtime"] = current_mtime
                state["last_size"] = current_size
                state["last_hash"] = current_hash
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking file {file_path}: {e}")
            return False
    
    def process_csv_file(self, file_path: Path) -> int:
        """
        Process CSV file and output new records as JSON events.
        
        Returns:
            Number of new records processed
        """
        file_str = str(file_path)
        processed_count = 0
        
        try:
            # Get the last processed row number
            last_row = self.file_states.get(file_str, {}).get("last_row", 0)
            current_row = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                
                for row in csv_reader:
                    current_row += 1
                    
                    # Skip already processed rows
                    if current_row <= last_row:
                        continue
                    
                    # Create Splunk event
                    event = self.create_splunk_event(row, file_path.name)
                    
                    # Output to stdout for Splunk consumption
                    print(json.dumps(event), flush=True)
                    processed_count += 1
                
                # Update last processed row
                if file_str in self.file_states:
                    self.file_states[file_str]["last_row"] = current_row
                
        except Exception as e:
            self.logger.error(f"Error processing CSV file {file_path}: {e}")
        
        return processed_count
    
    def create_splunk_event(self, csv_row: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """
        Create Splunk event from CSV row.
        
        Args:
            csv_row: Dictionary representing CSV row
            source_file: Source CSV filename
            
        Returns:
            Splunk-formatted event
        """
        # Try to extract timestamp from data or use current time
        event_time = self.extract_timestamp(csv_row)
        
        return {
            "time": event_time,
            "source": source_file,
            "sourcetype": self.sourcetype,
            "event": csv_row
        }
    
    def extract_timestamp(self, csv_row: Dict[str, Any]) -> float:
        """
        Extract timestamp from CSV row data.
        Looks for common timestamp field names.
        
        Args:
            csv_row: Dictionary representing CSV row
            
        Returns:
            Unix timestamp (float)
        """
        timestamp_fields = ['timestamp', 'time', 'datetime', 'date', 'created_at', 'updated_at']
        
        for field in timestamp_fields:
            if field in csv_row and csv_row[field]:
                try:
                    # Try common timestamp formats
                    timestamp_str = str(csv_row[field]).strip()
                    
                    # Try parsing various formats
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d %H:%M:%S.%f',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S.%f',
                        '%Y-%m-%dT%H:%M:%SZ',
                        '%Y-%m-%d',
                        '%m/%d/%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M:%S'
                    ]
                    
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(timestamp_str, fmt)
                            return dt.timestamp()
                        except ValueError:
                            continue
                            
                    # Try parsing as Unix timestamp
                    return float(timestamp_str)
                    
                except (ValueError, TypeError):
                    continue
        
        # Default to current time if no valid timestamp found
        return datetime.now().timestamp()
    
    def scan_csv_files(self) -> List[Path]:
        """Scan data directory for CSV files."""
        csv_files = []
        try:
            if self.data_dir.exists():
                csv_files = list(self.data_dir.glob("*.csv"))
                self.logger.debug(f"Found {len(csv_files)} CSV files")
        except Exception as e:
            self.logger.error(f"Error scanning directory {self.data_dir}: {e}")
        
        return csv_files
    
    def run_once(self) -> None:
        """Run one iteration of file processing."""
        csv_files = self.scan_csv_files()
        total_processed = 0
        
        for csv_file in csv_files:
            if self.should_process_file(csv_file):
                self.logger.info(f"Processing {csv_file.name}")
                count = self.process_csv_file(csv_file)
                total_processed += count
                self.logger.info(f"Processed {count} new records from {csv_file.name}")
        
        if total_processed > 0:
            self.save_state()
            self.logger.info(f"Total records processed: {total_processed}")
    
    def run_continuous(self) -> None:
        """Run continuously, polling for new CSV data."""
        self.logger.info(f"Starting continuous CSV monitoring on {self.data_dir}")
        self.logger.info(f"Poll interval: {self.poll_interval} seconds")
        
        try:
            while True:
                self.run_once()
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down CSV input script")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            sys.exit(1)

def main():
    """Main entry point for Splunk script input."""
    
    # Get the script's directory to determine app path
    script_dir = Path(__file__).parent
    app_dir = script_dir.parent
    
    # Configuration from environment variables with Splunk-aware defaults
    data_dir = os.getenv('CSV_DATA_DIR', str(app_dir / 'data'))
    state_dir = os.getenv('CSV_STATE_DIR', str(app_dir / 'state'))
    poll_interval = int(os.getenv('CSV_POLL_INTERVAL', '10'))
    sourcetype = os.getenv('CSV_SOURCETYPE', 'csv_data')
    run_mode = os.getenv('CSV_RUN_MODE', 'continuous')  # 'continuous' or 'once'
    
    # Initialize the CSV input processor
    csv_input = SplunkCSVInput(
        data_dir=data_dir,
        state_dir=state_dir,
        poll_interval=poll_interval,
        sourcetype=sourcetype
    )
    
    if run_mode == 'once':
        # Run once (useful for testing)
        csv_input.run_once()
    else:
        # Run continuously (normal operation)
        csv_input.run_continuous()

if __name__ == "__main__":
    main()