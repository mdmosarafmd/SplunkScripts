#!/usr/bin/env python3
"""
Test script for the Splunk CSV input script
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

def create_test_csv():
    """Create test CSV files"""
    test_data_dir = Path("test_data")
    test_data_dir.mkdir(exist_ok=True)
    
    # Create test CSV file
    csv_content = """timestamp,user,action,status
2024-01-15 10:30:00,alice,login,success
2024-01-15 10:31:00,bob,view_page,success
2024-01-15 10:32:00,charlie,download,failed
2024-01-15 10:33:00,alice,logout,success
"""
    
    with open(test_data_dir / "test1.csv", "w") as f:
        f.write(csv_content)
    
    print(f"Created test CSV file: {test_data_dir / 'test1.csv'}")
    return test_data_dir

def test_script_once():
    """Test the script in 'once' mode"""
    test_data_dir = create_test_csv()
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'CSV_DATA_DIR': str(test_data_dir),
        'CSV_STATE_DIR': 'test_state',
        'CSV_RUN_MODE': 'once',
        'CSV_SOURCETYPE': 'test_csv'
    })
    
    try:
        # Run the script
        result = subprocess.run(
            ['python3', 'csvToJsonConverter/bin/splunk_csv_input.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("=== STDOUT (Splunk Events) ===")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        event = json.loads(line)
                        print(json.dumps(event, indent=2))
                    except json.JSONDecodeError:
                        print(f"Non-JSON output: {line}")
        
        print("\n=== STDERR (Log Messages) ===")
        print(result.stderr)
        
        print(f"\n=== Return Code: {result.returncode} ===")
        
        # Run again to test incremental processing
        print("\n=== Running Again (Should Process 0 Records) ===")
        result2 = subprocess.run(
            ['python3', 'csvToJsonConverter/bin/splunk_csv_input.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("STDOUT:", result2.stdout)
        print("STDERR:", result2.stderr)
        
        # Add new data to test incremental processing
        print("\n=== Adding New Data ===")
        with open(test_data_dir / "test1.csv", "a") as f:
            f.write("2024-01-15 10:34:00,dave,register,success\n")
        
        result3 = subprocess.run(
            ['python3', 'csvToJsonConverter/bin/splunk_csv_input.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("New events:")
        if result3.stdout:
            for line in result3.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        event = json.loads(line)
                        print(json.dumps(event, indent=2))
                    except json.JSONDecodeError:
                        print(f"Non-JSON output: {line}")
        
        print("Log messages:")
        print(result3.stderr)
        
    finally:
        # Cleanup
        if test_data_dir.exists():
            shutil.rmtree(test_data_dir)
        if Path("test_state").exists():
            shutil.rmtree("test_state")

if __name__ == "__main__":
    test_script_once()