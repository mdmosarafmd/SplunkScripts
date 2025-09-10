# Splunk Saved Search Deletion Script

This script deletes disabled Splunk saved searches based on names provided in a text file.

## Features

- Connects to Splunk via REST API
- Reads saved search names from a text file
- Checks if each search is disabled before deletion
- Only deletes searches that are disabled
- Provides detailed logging
- Supports dry-run mode to preview actions
- Error handling and status reporting

## Requirements

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests urllib3 PyYAML
```

## Configuration

1. Copy and customize the configuration file:
```bash
cp config.yaml my_config.yaml
```

2. Edit `my_config.yaml` with your Splunk details:
```yaml
splunk:
  host: "your-splunk-server.com"
  port: 8089
  username: "your_username"
  password: "your_password"
  protocol: "https"  # http or https
  verify_ssl: false

settings:
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  dry_run: false
```

## Usage

### Basic usage with config file:
```bash
python delete_disabled_searches.py --config my_config.yaml --file searches.txt
```

### Dry run (preview what would be deleted):
```bash
python delete_disabled_searches.py --config my_config.yaml --file searches.txt --dry-run
```

### Override config values via command line:
```bash
python delete_disabled_searches.py --config my_config.yaml --file searches.txt --host different-server.com --protocol http
```

### Use default config.yaml:
```bash
python delete_disabled_searches.py --file searches.txt
```

## Input File Format

Create a text file with one saved search name per line:
```
search_name_1
search_name_2
disabled_search_example
test_search_disabled
```

## Features

### Configuration Management
- YAML-based configuration file
- Support for both HTTP and HTTPS protocols
- SSL verification control
- Command-line overrides for config values
- Configurable logging levels

### Safety Features
- Only deletes searches that are actually disabled
- Skips enabled searches with a warning
- Provides summary of actions taken
- Supports dry-run mode for testing
- Detailed logging of all operations
- Configuration validation

### Protocol Support
- HTTP and HTTPS protocols
- Configurable SSL verification
- Custom port configuration

## Configuration Options

### Splunk Settings
- `host`: Splunk server hostname or IP
- `port`: Management port (usually 8089)
- `username`: Splunk username
- `password`: Splunk password
- `protocol`: "http" or "https"
- `verify_ssl`: true/false for SSL certificate verification

### Application Settings
- `log_level`: "DEBUG", "INFO", "WARNING", or "ERROR"
- `dry_run`: true/false for default dry-run behavior

## Command Line Arguments

- `--config`: Configuration file path (default: config.yaml)
- `--file`: Text file with search names (required)
- `--dry-run`: Preview mode without actual deletion
- `--host`: Override host from config
- `--username`: Override username from config
- `--password`: Override password from config
- `--port`: Override port from config
- `--protocol`: Override protocol from config

## Output

The script provides detailed logging showing:
- Connection details (protocol, host, SSL status)
- Which searches are being processed
- Whether each search is enabled/disabled
- Which searches are deleted/skipped
- Final summary of actions taken