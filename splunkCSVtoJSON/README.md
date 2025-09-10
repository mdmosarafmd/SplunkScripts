# CSV to Splunk JSON Converter

A Python script that reads CSV files from a data directory, converts them to JSON format, and indexes them in Splunk using the HTTP Event Collector (HEC).

## Features

- Reads all CSV files from a specified directory
- Converts CSV data to Splunk-compatible JSON format
- Saves JSON files locally for backup/review
- Sends data directly to Splunk via HTTP Event Collector
- Configurable via command line arguments or environment variables
- Comprehensive logging

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
The script will automatically use configuration from `config.py` and attempt to forward data to Splunk:
```bash
python csv_to_splunk.py
```

### With Custom Parameters
```bash
python csv_to_splunk.py --splunk-host your-splunk-server.com --splunk-token your-hec-token --protocol https
```

### JSON Conversion Only (No Splunk Forwarding)
To skip Splunk forwarding, don't provide host/token or set them to empty:
```bash
python csv_to_splunk.py --splunk-host "" --splunk-token ""
```

### Command Line Arguments

- `--data-dir`: Directory containing CSV files (default: "data")
- `--output-dir`: Directory to save JSON files (default: "json_output")  
- `--splunk-host`: Splunk server hostname or IP (default: "localhost")
- `--splunk-port`: Splunk HEC port (default: 8088)
- `--splunk-token`: Splunk HTTP Event Collector token
- `--index`: Target Splunk index name (default: "testdata")
- `--protocol`: Protocol to use - http or https (default: "http")

### Environment Variables

You can also configure the script using environment variables:

```bash
export SPLUNK_HOST=your-splunk-server.com
export SPLUNK_PORT=8088
export SPLUNK_TOKEN=your-hec-token
export SPLUNK_INDEX=csv_data
export SPLUNK_PROTOCOL=http
export DATA_DIR=./csv_files
export OUTPUT_DIR=./json_files
export LOG_LEVEL=INFO
```

## Directory Structure

```
splunkCSVtoJSON/
├── csv_to_splunk.py      # Main script
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── data/                 # Place CSV files here
└── json_output/         # Generated JSON files
```

## Splunk Configuration

To use the Splunk integration, you need to:

1. Enable HTTP Event Collector in Splunk
2. Create an HEC token
3. Configure the target index

## Configuration

The script uses `config.py` for default settings. Current defaults:
- **SPLUNK_HOST**: localhost
- **SPLUNK_PORT**: 8088
- **SPLUNK_TOKEN**: b69e8871-8135-4ca4-a631-8a44ee7b1af9
- **SPLUNK_INDEX**: testdata
- **SPLUNK_PROTOCOL**: http
- **DATA_DIR**: data
- **OUTPUT_DIR**: json_output

## Protocol Selection

The script supports both HTTP and HTTPS protocols:
- **HTTP**: Default, typically used for local/development Splunk instances
- **HTTPS**: Use for production environments with SSL-enabled Splunk

Set via:
- Config: `SPLUNK_PROTOCOL = 'https'`
- Environment: `export SPLUNK_PROTOCOL=https`
- Command line: `--protocol https`

## Example

1. Place your CSV files in the `data/` directory
2. Run the script with default config:
```bash
python csv_to_splunk.py
```

Or with custom settings:
```bash
python csv_to_splunk.py --splunk-host splunk.example.com --splunk-token abcd1234-5678-90ef --protocol https
```

The script will:
- Read all CSV files from the `data/` directory
- Convert each file to JSON format
- Save JSON files to `json_output/` directory
- Send the data to your Splunk instance using the specified protocol