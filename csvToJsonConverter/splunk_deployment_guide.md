# Splunk Universal Forwarder CSV Input Deployment Guide

## Overview
This guide explains how to deploy the CSV to JSON converter as a script-based input for Splunk Universal Forwarder.

## Files
- `bin/splunk_csv_input.py` - Main script for real-time CSV processing
- `default/inputs.conf` - Splunk input configuration
- `default/props.conf` - Sourcetype configuration
- `bin/test_splunk_script.py` - Test script for validation
- `data/` - Directory for CSV input files
- `local/` - Directory for custom configurations

## Deployment Steps

### 1. Create Splunk App Directory Structure
```bash
# On your Splunk Universal Forwarder server
mkdir -p /opt/splunk/etc/apps/csvToJsonConverter/{bin,local,data,default,state}
```

### 2. Copy Application Files
```bash
# Copy the entire application structure
cp -r csvToJsonConverter /opt/splunk/etc/apps/

# Alternatively, copy files individually:
# Copy Python scripts
cp bin/splunk_csv_input.py /opt/splunk/etc/apps/csvToJsonConverter/bin/
cp bin/test_splunk_script.py /opt/splunk/etc/apps/csvToJsonConverter/bin/
chmod +x /opt/splunk/etc/apps/csvToJsonConverter/bin/splunk_csv_input.py

# Copy configuration files
cp default/inputs.conf /opt/splunk/etc/apps/csvToJsonConverter/default/
cp default/props.conf /opt/splunk/etc/apps/csvToJsonConverter/default/
```

### 3. Set Permissions
```bash
chown -R splunk:splunk /opt/splunk/etc/apps/csvToJsonConverter/
chmod 755 /opt/splunk/etc/apps/csvToJsonConverter/bin/splunk_csv_input.py
chmod 755 /opt/splunk/etc/apps/csvToJsonConverter/bin/test_splunk_script.py
```

### 4. Configure Python Environment
Ensure Python 3 is available and accessible to the splunk user:
```bash
# Test Python availability
sudo -u splunk python3 --version
```

### 5. Prepare Data and State Directories
```bash
# Data directory should already exist from the copy operation
# Create state directory if not present
mkdir -p /opt/splunk/etc/apps/csvToJsonConverter/state
chown splunk:splunk /opt/splunk/etc/apps/csvToJsonConverter/data
chown splunk:splunk /opt/splunk/etc/apps/csvToJsonConverter/state
```

### 6. Restart Splunk Universal Forwarder
```bash
/opt/splunk/bin/splunk restart
```

## Configuration Options

### Environment Variables
The script accepts these environment variables (set in inputs.conf):

- `CSV_DATA_DIR` - Directory containing CSV files (default: "data")
- `CSV_STATE_DIR` - Directory for state files (default: "state")
- `CSV_POLL_INTERVAL` - Seconds between checks (default: 10)
- `CSV_SOURCETYPE` - Splunk sourcetype (default: "csv_data")
- `CSV_RUN_MODE` - "continuous" or "once" (default: "continuous")

### Inputs.conf Customization
```ini
[script://./bin/splunk_csv_input.py]
disabled = false
index = testdata                 # Change target index (current default)
interval = 10                    # Change polling interval (current default)
sourcetype = csv_data            # Change sourcetype (current default) 
source = csv_script_input        # Source identifier
```

**Note:** The script automatically detects its location within the Splunk app and uses relative paths for data and state directories. Environment variables can be set at the system level if custom paths are needed:

```bash
# System-level environment variables (optional)
export CSV_DATA_DIR=/custom/data/path
export CSV_STATE_DIR=/custom/state/path  
export CSV_POLL_INTERVAL=30
export CSV_SOURCETYPE=custom_csv_data
export CSV_RUN_MODE=continuous
```

## How It Works

1. **File Monitoring**: Script monitors the data directory for CSV files
2. **Change Detection**: Uses file hash and modification time to detect changes
3. **Incremental Processing**: Only processes new/changed records
4. **State Management**: Tracks processed files and row positions
5. **JSON Output**: Outputs Splunk-compatible JSON events to stdout
6. **Timestamp Extraction**: Automatically detects timestamp fields in CSV data

## Testing

### Test the Script Manually
```bash
# Run once to test (script will auto-detect app directory)
sudo -u splunk python3 /opt/splunk/etc/apps/csvToJsonConverter/bin/splunk_csv_input.py

# Set test environment for single run
export CSV_RUN_MODE=once
sudo -u splunk python3 /opt/splunk/etc/apps/csvToJsonConverter/bin/splunk_csv_input.py

# Use the included test script
sudo -u splunk python3 /opt/splunk/etc/apps/csvToJsonConverter/bin/test_splunk_script.py
```

### Check Splunk Logs
```bash
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep csvToJsonConverter
```

### Verify Data Ingestion
In Splunk search:
```spl
index=testdata sourcetype=csv_data | head 10
```

## File Processing Flow

1. **Initial Run**: All existing CSV files are processed completely
2. **Subsequent Runs**: Only new files or changed files are processed
3. **Incremental Updates**: For modified files, only new rows are processed
4. **State Persistence**: Processing state is saved between runs

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure splunk user has read access to data directory
   - Check execute permissions on the Python script

2. **Python Not Found**
   - Verify Python 3 is installed and in PATH for splunk user
   - Consider using absolute path to Python in inputs.conf

3. **No Data Appearing**
   - Check splunkd.log for script errors
   - Verify CSV files are in the correct directory
   - Test script manually with CSV_RUN_MODE=once

4. **Memory Issues**
   - For large CSV files, consider splitting them
   - Monitor script memory usage

### Debug Mode
Add debug logging by modifying the script's logging level:
```python
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Performance Considerations

- **Large Files**: Script processes incrementally, suitable for large CSV files
- **Many Files**: Consider adjusting poll_interval for directories with many files
- **Memory Usage**: Each CSV row is processed individually to minimize memory usage
- **Disk I/O**: State files are written only when new data is processed

## Application Structure

The csvToJsonConverter application follows Splunk's standard app structure:

```
csvToJsonConverter/
├── bin/
│   ├── splunk_csv_input.py      # Main processing script
│   └── test_splunk_script.py    # Test and validation script
├── default/
│   ├── inputs.conf              # Default input configurations
│   └── props.conf               # Sourcetype and field configurations
├── local/                       # Custom/override configurations (empty by default)
├── data/                        # CSV input files directory
└── state/                       # Processing state files (created at runtime)
```

## Testing and Validation

### Using the Test Script
The included test script helps validate the setup:

```bash
# Run the test script
cd /opt/splunk/etc/apps/csvToJsonConverter
sudo -u splunk python3 bin/test_splunk_script.py
```

This test script:
- Creates sample CSV data
- Tests the processing script
- Validates JSON output format
- Checks state management

## Security Notes

- Script runs as splunk user with limited privileges
- State files contain only processing metadata, not actual data
- All file operations are within the configured data directory
- No network connections are made (data flows through Splunk's internal mechanisms)
- Application follows Splunk's security best practices for custom apps