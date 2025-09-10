# Splunk Saved Search Deletion Script

This Python script deletes disabled Splunk saved searches based on names provided in a text file. It uses Splunk's REST API to safely identify and remove only disabled saved searches while preserving enabled ones.

## Features

### Core Functionality
- **Safe deletion**: Only deletes searches that are actually disabled
- **Namespace-aware**: Automatically finds searches across different user/app namespaces
- **Bulk processing**: Processes multiple searches from a text file
- **Comprehensive logging**: Detailed logging with configurable levels
- **Dry-run mode**: Preview what would be deleted without making changes
- **Error handling**: Robust error handling with detailed status reporting

### Configuration Management
- **YAML-based configuration**: Centralized configuration file for all settings
- **Protocol flexibility**: Support for both HTTP and HTTPS protocols
- **SSL control**: Configurable SSL certificate verification
- **Command-line overrides**: Override any config value via command line arguments
- **Multiple environments**: Easy to maintain different configs for dev/test/prod

### Security & Safety
- **Connection validation**: Tests connectivity before processing
- **Permission handling**: Respects Splunk's namespace and permission model
- **Private search awareness**: Handles private saved searches appropriately
- **Access control**: Works within user's permission boundaries

## Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests urllib3 PyYAML
```

## Installation & Setup

1. **Clone or download** the script files
2. **Install dependencies** (see Requirements section)
3. **Configure connection details** (see Configuration section)
4. **Prepare search list** (see Input File Format section)
5. **Test with dry-run** before live execution

## Configuration

### 1. Create Configuration File

Copy and customize the configuration file:
```bash
cp config.yaml my_config.yaml
```

### 2. Edit Configuration

Edit `my_config.yaml` with your Splunk environment details:

```yaml
splunk:
  host: "your-splunk-server.com"
  port: 8089
  username: "your_username"
  password: "your_password"
  protocol: "https"  # http or https
  verify_ssl: false   # true/false for SSL certificate verification

settings:
  log_level: "INFO"   # DEBUG, INFO, WARNING, ERROR
  dry_run: false      # Default dry-run behavior
```

### Configuration Options Explained

#### Splunk Connection Settings
- **`host`**: Splunk server hostname or IP address
- **`port`**: Management port (typically 8089 for Splunk)
- **`username`**: Splunk username with appropriate permissions
- **`password`**: Splunk password
- **`protocol`**: Communication protocol ("http" or "https")
- **`verify_ssl`**: SSL certificate verification (true/false)

#### Application Settings
- **`log_level`**: Logging verbosity ("DEBUG", "INFO", "WARNING", "ERROR")
- **`dry_run`**: Default behavior for dry-run mode (true/false)

## Usage

### Basic Operations

#### 1. Dry Run (Recommended First Step)
Preview what would be deleted without making changes:
```bash
python3 delete_disabled_searches.py --config my_config.yaml --file searches.txt --dry-run
```

#### 2. Live Execution
Execute actual deletions:
```bash
python3 delete_disabled_searches.py --config my_config.yaml --file searches.txt
```

#### 3. Use Default Config
If your config file is named `config.yaml`:
```bash
python3 delete_disabled_searches.py --file searches.txt --dry-run
```

### Advanced Usage

#### Override Configuration Values
Override any config setting via command line:
```bash
# Use different server
python3 delete_disabled_searches.py --file searches.txt --host prod-splunk.company.com

# Use HTTP instead of HTTPS
python3 delete_disabled_searches.py --file searches.txt --protocol http --host dev-splunk.local

# Use different credentials
python3 delete_disabled_searches.py --file searches.txt --username serviceaccount --password newpass
```

#### Debug Mode
Enable detailed debug logging for troubleshooting:
```bash
# Create debug config
cp config.yaml debug_config.yaml
# Edit debug_config.yaml and set log_level: "DEBUG"

python3 delete_disabled_searches.py --config debug_config.yaml --file searches.txt --dry-run
```

## Command Line Arguments

### Required Arguments
- `--file`: Text file containing saved search names (one per line)

### Optional Arguments
- `--config`: Configuration file path (default: `config.yaml`)
- `--dry-run`: Preview mode - shows what would be deleted without deleting
- `--host`: Override Splunk host from config
- `--username`: Override username from config
- `--password`: Override password from config
- `--port`: Override port from config
- `--protocol`: Override protocol from config (`http` or `https`)

## Input File Format

Create a text file with one saved search name per line:

```
search_name_1
search_name_2
disabled_search_example
test_search_disabled
old_unused_search
```

### File Requirements
- **Plain text format**
- **One search name per line**
- **Exact search names** (case-sensitive)
- **No quotes or special formatting** needed
- **Empty lines ignored**

## How It Works

### 1. Connection & Validation
- Tests connectivity to Splunk server
- Validates credentials and permissions
- Confirms REST API access

### 2. Search Discovery
The script searches across multiple namespaces to find each saved search:
- User-specific namespaces (`/servicesNS/username/app/`)
- System namespaces (`/servicesNS/nobody/system/`)
- Global namespaces (`/servicesNS/-/app/`)

### 3. Status Verification
For each found search:
- Retrieves search configuration
- Checks if the search is disabled
- Skips enabled searches with a warning

### 4. Safe Deletion
For disabled searches:
- Attempts deletion using the appropriate namespace
- Handles permission and ownership requirements
- Provides detailed success/failure reporting

## Output & Logging

### Standard Output
The script provides comprehensive logging:

```
2025-09-10 17:44:24,199 - INFO - Connecting to https://localhost:8089
2025-09-10 17:44:24,199 - INFO - SSL verification: disabled
2025-09-10 17:44:24,199 - INFO - Mode: LIVE
2025-09-10 17:44:24,243 - INFO - Successfully connected to Splunk server
2025-09-10 17:44:24,244 - INFO - Found 2 saved searches to process
2025-09-10 17:44:24,244 - INFO - Processing: search_name_1
2025-09-10 17:44:24,299 - DEBUG - Found search 'search_name_1' in namespace user='-', app='search'
2025-09-10 17:44:24,369 - ERROR - Failed to delete saved search 'search_name_1' from any namespace
2025-09-10 17:44:24,550 - INFO - Summary: 0 deleted, 0 skipped (enabled), 1 not found, 1 errors
```

### Log Levels
- **DEBUG**: Detailed HTTP requests/responses, namespace attempts
- **INFO**: Standard operational information
- **WARNING**: Non-critical issues (search not found, etc.)
- **ERROR**: Deletion failures, connection issues

### Summary Report
Each run concludes with a summary:
- **Deleted**: Successfully removed searches
- **Skipped**: Enabled searches that were preserved  
- **Not Found**: Searches that don't exist
- **Errors**: Failed deletion attempts

## Limitations & Considerations

### Permission Requirements
- **User permissions**: Script runs with the provided user's permissions
- **Private searches**: Can only delete private searches you own
- **Admin access**: Admin privileges required for cross-user deletion
- **App context**: Some searches require specific app permissions

### Private Saved Searches
Private saved searches have special handling requirements:
- **Ownership**: Only the owner or admin can delete private searches
- **Namespace complexity**: May appear in global namespace but require owner context
- **Permission errors**: Will show permission-related error messages

### Performance Considerations
- **API calls**: Multiple REST API calls per search (discovery + deletion)
- **Rate limiting**: Respects Splunk's API rate limits
- **Network timeouts**: Configurable timeouts for slow connections
- **Batch processing**: Processes searches sequentially for reliability

## Troubleshooting

### Common Issues

#### 1. Connection Failures
```
ERROR - Connection error: [SSL: CERTIFICATE_VERIFY_FAILED]
```
**Solution**: Set `verify_ssl: false` in config or use `http` protocol

#### 2. Permission Denied
```
ERROR - Failed to delete saved search 'name': HTTP 403
```
**Solutions**: 
- Use admin account
- Run as search owner
- Check user permissions

#### 3. Search Not Found
```
WARNING - Saved search 'name' not found in any namespace
```
**Causes**:
- Search name typo
- Search already deleted
- Insufficient permissions to see search

#### 4. Private Search Deletion Failure
```
ERROR - Failed to delete saved search 'name' from any namespace
```
**For private searches**: This is expected behavior - private searches can only be deleted by their owner or admin.

### Debug Mode
Enable debug logging to see detailed API interactions:
```bash
python3 delete_disabled_searches.py --config debug_config.yaml --file searches.txt --dry-run
```

### Verification Steps
1. **Test connection**: Verify credentials work with Splunk web UI
2. **Check permissions**: Ensure user can see and manage saved searches
3. **Verify search names**: Confirm exact spelling and case
4. **Use dry-run**: Always test with `--dry-run` first

## Security Best Practices

### Configuration Security
- **File permissions**: Restrict access to config files containing credentials
- **Environment variables**: Consider using environment variables for sensitive data
- **Version control**: Never commit config files with real credentials

### Operational Security
- **Principle of least privilege**: Use accounts with minimal required permissions
- **Audit logging**: Review script output and Splunk audit logs
- **Testing**: Always use dry-run mode in production environments
- **Backup**: Consider backing up saved searches before deletion

## Examples

### Example 1: Basic Development Workflow
```bash
# 1. Test connection and see what would be deleted
python3 delete_disabled_searches.py --file dev_searches.txt --host dev-splunk.local --dry-run

# 2. Execute deletion
python3 delete_disabled_searches.py --file dev_searches.txt --host dev-splunk.local
```

### Example 2: Production Workflow
```bash
# 1. Use production config
python3 delete_disabled_searches.py --config prod_config.yaml --file cleanup_list.txt --dry-run

# 2. Review output carefully, then execute
python3 delete_disabled_searches.py --config prod_config.yaml --file cleanup_list.txt
```

### Example 3: Troubleshooting
```bash
# Enable debug logging to troubleshoot issues
python3 delete_disabled_searches.py --config debug_config.yaml --file problem_searches.txt --dry-run
```

## Support

For issues, questions, or contributions, please refer to the script documentation and Splunk REST API documentation for additional context on saved search management.
