# modern-cli-tool

A production-grade Python CLI template showcasing modern UX patterns, beautiful terminal output, and developer-friendly design.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Typer](https://img.shields.io/badge/typer-latest-green)
![Rich](https://img.shields.io/badge/rich-latest-purple)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or poetry

## Quick Start

```bash
# Get help
python cli.py --help

# Process a single file
python cli.py process data.txt --transform upper

# Process multiple files with output directory
python cli.py process *.txt --transform lower --output ./processed/

# List current directory contents
python cli.py list

# List with pattern matching
python cli.py list . --pattern "*.py"
```

## Usage Guide

### Global Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--help` | | Show help message | `python cli.py --help` |
| `--version` | | Display version | `python cli.py --version` |

### `process` Command

Transform and process files with visual feedback and safety features.

#### Basic Usage

```bash
# Process a single file (uppercase by default)
python cli.py process input.txt

# Process with specific transformation
python cli.py process input.txt --transform lower

# Process multiple files
python cli.py process file1.txt file2.txt file3.txt
```

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--transform` | `-t` | Transformation to apply (upper/lower) | upper |
| `--output` | `-o` | Output directory | current directory |
| `--dry-run` | | Preview changes without writing | False |
| `--yes` | `-y` | Skip confirmation prompts | False |
| `--verbose` | `-v` | Enable debug output | False |

#### Advanced Examples

```bash
# Preview what would happen (dry run)
python cli.py process *.txt --transform lower --dry-run

# Process without confirmation prompts
python cli.py process *.txt --yes

# Verbose output with custom directory
python cli.py process data/*.csv --output ./results/ --verbose

# Combine multiple options
python cli.py process *.log \
    --transform upper \
    --output ./processed/ \
    --verbose \
    --yes
```

### `list` Command

Display directory contents in a beautiful, formatted table.

#### Basic Usage

```bash
# List current directory
python cli.py list

# List specific directory
python cli.py list /path/to/directory

# Filter with patterns
python cli.py list . --pattern "*.py"
```

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--pattern` | `-p` | Glob pattern to filter files | * |
| `--json` | | Output as JSON for scripting | False |
| `--verbose` | `-v` | Show additional details | False |

#### Output Formats

**Human-Readable Table** (default):
```
                 📁 /home/user/project                  
┌────────────┬──────┬───────┬─────────────────┐
│ Name       │ Type │  Size │ Modified        │
├────────────┼──────┼───────┼─────────────────┤
│ README.md  │ file │ 8,432 │ 2025-01-15 14:23│
│ cli.py     │ file │ 5,621 │ 2025-01-15 13:45│
│ tests/     │ dir  │     - │ 2025-01-14 10:30│
└────────────┴──────┴───────┴─────────────────┘
Found 3 items matching '*'
```

**JSON Output** (for scripting):
```bash
$ python cli.py list --json --pattern "*.py"
[
  {
    "name": "cli.py",
    "type": "file",
    "size": 5621
  },
  {
    "name": "test_cli.py",
    "type": "file",
    "size": 2156
  }
]
```

### Logging

When using `--verbose`, the tool outputs debug information:

```bash
$ python cli.py process file.txt --verbose
14:23:45 - __main__ - DEBUG - Processing 1 files with transform=upper
14:23:45 - __main__ - DEBUG - Processing file.txt
14:23:45 - __main__ - INFO - Wrote 1234 bytes to file_upper.txt
```

## Best Practices

### For Users

1. **Always use dry-run first** when processing multiple files:
   ```bash
   python cli.py process *.txt --dry-run
   ```

2. **Pipe JSON output** for further processing:
   ```bash
   python cli.py list --json | jq '.[] | select(.size > 1000)'
   ```

3. **Use verbose mode** when debugging:
   ```bash
   python cli.py process file.txt --verbose 2>&1 | tee process.log
   ```

4. **Check exit codes** in scripts:
   ```bash
   if python cli.py process *.txt; then
       echo "Success!"
   else
       echo "Failed with code $?"
   fi
   ```

## Error Handling

The CLI provides clear error messages and appropriate exit codes:

| Exit Code | Meaning | Example Scenario |
|-----------|---------|-----------------|
| 0 | Success | Operation completed successfully |
| 1 | General error | File not found, permission denied |
| 130 | User interrupt | User cancelled operation (Ctrl+C or 'no' to prompt) |

Example error outputs:

```bash
# File not found
$ python cli.py process missing.txt
⚠️  Some files failed:
  • missing.txt: File not found: missing.txt
Exit code: 1

# Permission denied
$ python cli.py list /root
Error: Permission denied: /root
Tip: Check the path exists and you have read permissions
Exit code: 1

# User cancellation
$ python cli.py process *.txt
⚠️  About to process 10 files
Continue? [y/n]: n
Aborted by user
Exit code: 130
```