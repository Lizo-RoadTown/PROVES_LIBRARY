# Risk Scanner

Repository risk scanner for detecting mission-critical issues in PROVES Kit and F Prime projects.

## Purpose

Scans repositories for known risk patterns and creates a **push/pull knowledge capture loop**:
- **PUSH:** Alert teams with risk details + fix links from library
- **PULL:** Capture team's context and resolution for library enrichment

## Architecture

```
risk-scanner/
├── scanner.py         # Main CLI interface
├── patterns/          # Risk pattern definitions
│   ├── power.py      # Power system patterns
│   ├── radio.py      # Radio/communication patterns
│   ├── memory.py     # Memory management patterns
│   └── integration.py # Component integration patterns
├── analyzers/         # Code analysis engines
│   ├── ast_analyzer.py     # Python AST parsing
│   ├── config_analyzer.py  # Config file analysis
│   └── dependency_analyzer.py # Dependency checking
├── capture.py         # Knowledge capture (pull mechanism)
├── models.py          # Risk and capture data models
├── requirements.txt   # Python dependencies
└── README.md
```

## Usage

### Scan a Repository

```bash
python scanner.py --repo /path/to/repo --output report.json
```

### Daily Scan (for CI/CD)

```bash
python scanner.py --repo . --daily --severity high
```

### Capture Knowledge After Fix

```bash
python scanner.py --capture --risk-id abc123
```

## Risk Categories

### Power System Risks
- I2C address conflicts
- Voltage regulator issues
- Power sequencing problems
- Battery management errors

### Radio/Communication Risks
- Timing conflicts
- Frequency configuration errors
- Packet loss patterns
- Antenna integration issues

### Memory Management Risks
- Buffer overflows
- Memory leaks
- Stack overflow conditions
- Heap fragmentation

### Component Integration Risks
- Port mismatch
- Type incompatibility
- Missing dependencies
- Circular dependencies

## Pattern Definition Format

Patterns are defined as Python functions that return risk detections:

```python
# patterns/power.py

def detect_i2c_conflict(ast_tree, config):
    """
    Detect I2C address conflicts in multi-device configurations.

    Pattern: Multiple devices with same I2C address
    Severity: HIGH
    Library Reference: software-001
    """
    devices = extract_i2c_devices(ast_tree)
    addresses = [d.address for d in devices]

    if len(addresses) != len(set(addresses)):
        return Risk(
            pattern="i2c-address-conflict",
            severity="high",
            category="power",
            file_path=get_file_path(ast_tree),
            line_number=get_conflict_line(devices),
            description="Multiple I2C devices using same address",
            library_fix="software-001",
            suggested_resolution="Use I2C multiplexer or reassign addresses"
        )
    return None
```

## Risk Report Format

```json
{
  "scan_id": "scan-20241220-001",
  "timestamp": "2024-12-20T02:00:00Z",
  "repo": "/path/to/repo",
  "risks": [
    {
      "risk_id": "risk-abc123",
      "severity": "high",
      "category": "power",
      "pattern": "i2c-address-conflict",
      "file_path": "src/power/i2c_manager.py",
      "line_number": 45,
      "description": "I2C devices 0x48 and 0x48 conflict",
      "library_fix": "software-001",
      "fix_link": "http://mcp-server/entry/software-001",
      "suggested_resolution": "Use TCA9548A multiplexer or reassign INA219 to 0x49"
    }
  ],
  "summary": {
    "total_risks": 1,
    "critical": 0,
    "high": 1,
    "medium": 0,
    "low": 0
  }
}
```

## Knowledge Capture (Pull Mechanism)

After a risk is fixed, capture the context:

```bash
$ python scanner.py --capture --risk-id risk-abc123

Risk Scanner - Knowledge Capture
=================================

Risk: I2C address conflict (risk-abc123)
Severity: high
File: src/power/i2c_manager.py:45

Did you resolve this risk? (y/n): y

How did you resolve it?
> Used TCA9548A I2C multiplexer to separate bus segments

What was your specific context?
> BroncoSat-2 has 4 INA219 sensors that need same address.
> Added multiplexer allows all 4 on different channels.

Any additional notes?
> Tested with fprime-proves test suite, all sensors read correctly now.
> See commit a4f04c9 for implementation.

Generating library entry draft...
Draft saved to: captures/draft-abc123.md
Submit for review? (y/n): y

Submitted! View at: https://github.com/Lizo-RoadTown/PROVES_LIBRARY/issues/42
```

## Installation

```bash
cd risk-scanner
pip install -r requirements.txt
```

## Adding New Patterns

1. Create pattern function in `patterns/category.py`
2. Register pattern in `scanner.py`
3. Add test in `tests/test_patterns.py`
4. Document pattern in this README

## Testing

```bash
pytest tests/
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: PROVES Risk Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install scanner
        run: |
          pip install -r risk-scanner/requirements.txt
      - name: Run risk scan
        run: |
          python risk-scanner/scanner.py --repo . --severity high
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: risk-report
          path: report.json
```

## Next Steps

1. Implement `scanner.py` CLI
2. Create initial risk patterns (power, radio, memory)
3. Build AST and config analyzers
4. Implement capture workflow
5. Integrate with MCP server for fix lookups
