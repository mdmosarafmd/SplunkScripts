#!/usr/bin/env python3
"""
CSV to Splunk JSON Converter
Reads CSV files from data directory and converts them to JSON format for Splunk indexing.
"""

import os
import csv
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
import requests
from typing import Dict, List, Any, Optional
import config

class CSVToSplunkConverter:
    def __init__(self, splunk_host: str = None, splunk_port: int = 8088, 
                 splunk_token: str = None, index_name: str = "main", protocol: str = "http"):
        """
        Initialize the CSV to Splunk converter.
        
        Args:
            splunk_host: Splunk server hostname or IP
            splunk_port: Splunk HEC port (default: 8088)
            splunk_token: Splunk HTTP Event Collector token
            index_name: Target Splunk index name
            protocol: Protocol to use ('http' or 'https')
        """
        self.splunk_host = splunk_host
        self.splunk_port = splunk_port
        self.splunk_token = splunk_token
        self.index_name = index_name
        self.protocol = protocol.lower()
        self.splunk_url = f"{self.protocol}://{splunk_host}:{splunk_port}/services/collector/event" if splunk_host else None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def read_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read CSV file and convert to list of dictionaries.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of dictionaries representing CSV rows
        """
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    data.append(dict(row))
            self.logger.info(f"Successfully read {len(data)} rows from {file_path}")
        except Exception as e:
            self.logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            raise
        
        return data
    
    def csv_to_json(self, csv_data: List[Dict[str, Any]], source_file: str) -> List[Dict[str, Any]]:
        """
        Convert CSV data to Splunk JSON format.
        
        Args:
            csv_data: List of dictionaries from CSV
            source_file: Source CSV filename
            
        Returns:
            List of Splunk-formatted JSON events
        """
        splunk_events = []
        current_time = datetime.now().timestamp()
        
        for row_index, row in enumerate(csv_data):
            # Create Splunk event format
            splunk_event = {
                "time": current_time,
                "host": "csv-converter",
                "source": source_file,
                "sourcetype": "csv_data",
                "index": self.index_name,
                "event": row
            }
            splunk_events.append(splunk_event)
        
        self.logger.info(f"Converted {len(splunk_events)} rows to Splunk JSON format")
        return splunk_events
    
    def save_json_file(self, json_data: List[Dict[str, Any]], output_path: str) -> None:
        """
        Save JSON data to file.
        
        Args:
            json_data: List of JSON events
            output_path: Output file path
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)
            self.logger.info(f"JSON data saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving JSON file {output_path}: {str(e)}")
            raise
    
    def send_to_splunk(self, json_data: List[Dict[str, Any]]) -> bool:
        """
        Send JSON data to Splunk via HTTP Event Collector.
        
        Args:
            json_data: List of Splunk-formatted events
            
        Returns:
            True if successful, False otherwise
        """
        if not all([self.splunk_host, self.splunk_token]):
            self.logger.warning("Splunk host or token not configured. Skipping Splunk indexing.")
            return False
        
        headers = {
            'Authorization': f'Splunk {self.splunk_token}',
            'Content-Type': 'application/json'
        }
        
        success_count = 0
        for event in json_data:
            try:
                response = requests.post(
                    self.splunk_url,
                    headers=headers,
                    json=event,
                    verify=False if self.protocol == 'https' else None,  # Only apply verify for HTTPS
                    timeout=30
                )
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    self.logger.error(f"Failed to send event to Splunk: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.logger.error(f"Error sending event to Splunk: {str(e)}")
        
        self.logger.info(f"Successfully sent {success_count}/{len(json_data)} events to Splunk")
        return success_count == len(json_data)
    
    def process_csv_directory(self, data_dir: str = "data", output_dir: str = "json_output") -> None:
        """
        Process all CSV files in the data directory.
        
        Args:
            data_dir: Directory containing CSV files
            output_dir: Directory to save JSON files
        """
        data_path = Path(data_dir)
        output_path = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_path.mkdir(exist_ok=True)
        
        if not data_path.exists():
            self.logger.error(f"Data directory '{data_dir}' does not exist")
            return
        
        csv_files = list(data_path.glob("*.csv"))
        if not csv_files:
            self.logger.warning(f"No CSV files found in '{data_dir}' directory")
            return
        
        self.logger.info(f"Found {len(csv_files)} CSV files to process")
        
        for csv_file in csv_files:
            try:
                self.logger.info(f"Processing {csv_file.name}")
                
                # Read CSV data
                csv_data = self.read_csv_file(str(csv_file))
                
                # Convert to Splunk JSON format
                json_data = self.csv_to_json(csv_data, csv_file.name)
                
                # Save JSON file
                json_filename = output_path / f"{csv_file.stem}.json"
                self.save_json_file(json_data, str(json_filename))
                
                # Send to Splunk if configured
                if self.splunk_host and self.splunk_token:
                    self.send_to_splunk(json_data)
                
                self.logger.info(f"Successfully processed {csv_file.name}")
                
            except Exception as e:
                self.logger.error(f"Error processing {csv_file.name}: {str(e)}")
                continue

def main():
    parser = argparse.ArgumentParser(description="Convert CSV files to JSON and index in Splunk")
    parser.add_argument("--data-dir", default=config.DATA_DIR, help="Directory containing CSV files")
    parser.add_argument("--output-dir", default=config.OUTPUT_DIR, help="Directory to save JSON files")
    parser.add_argument("--splunk-host", default=config.SPLUNK_HOST, help="Splunk server hostname or IP")
    parser.add_argument("--splunk-port", type=int, default=config.SPLUNK_PORT, help="Splunk HEC port")
    parser.add_argument("--splunk-token", default=config.SPLUNK_TOKEN, help="Splunk HTTP Event Collector token")
    parser.add_argument("--index", default=config.SPLUNK_INDEX, help="Target Splunk index name")
    parser.add_argument("--protocol", default=config.SPLUNK_PROTOCOL, choices=['http', 'https'], help="Protocol to use (http or https)")
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = CSVToSplunkConverter(
        splunk_host=args.splunk_host,
        splunk_port=args.splunk_port,
        splunk_token=args.splunk_token,
        index_name=args.index,
        protocol=args.protocol
    )
    
    # Process CSV files
    converter.process_csv_directory(args.data_dir, args.output_dir)

if __name__ == "__main__":
    main()