# InventoryUnitConverter - Always-On Agent

An intelligent always-on agent that auto-detects new inventory data, fetches the latest conversion master (JSON/CSV), and instantly standardizes units (PIECE, BOX, CARTON) using conversion rules. Supports API, webhook, or file input with comprehensive logging.

## Features

🤖 **Always-On Agent**: Runs continuously without manual activation
📁 **Auto-Detection**: Monitors file system for new inventory data (JSON/CSV)
🔄 **Real-Time Processing**: Instantly processes and standardizes inventory units
🌐 **Multiple Input Methods**: API endpoints, webhooks, and file system monitoring
📊 **Smart Conversion**: Product-specific and default conversion rules
📝 **Comprehensive Logging**: All activities logged with timestamps
🚀 **Zero Configuration**: Works out-of-the-box with sensible defaults

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/saviopaul/inventory-unit-conversion.git
cd inventory-unit-conversion

# Install dependencies
npm install

# Start the always-on agent
npm start
```

### Usage

#### 1. File-Based Processing (Auto-Detection)

Drop inventory files into the `data/` directory:

**JSON Format:**
```json
{
  "source": "outlet-001",
  "items": [
    {
      "sku": "SKU001",
      "name": "Widget A",
      "quantity": 120,
      "unit": "PIECE",
      "category": "Electronics"
    }
  ]
}
```

**CSV Format:**
```csv
sku,name,quantity,unit,category
SKU001,Widget A,120,PIECE,Electronics
```

#### 2. Webhook API

```bash
# Send inventory data via webhook
curl -X POST http://localhost:3000/webhook/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "source": "api-client",
    "items": [
      {"sku": "SKU001", "quantity": 50, "unit": "PIECE", "name": "Test Widget"}
    ]
  }'
```

#### 3. Direct Conversion API

```bash
# Convert specific items to target unit
curl -X POST http://localhost:3000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"sku": "SKU001", "quantity": 100, "unit": "PIECE"}
    ],
    "targetUnit": "BOX"
  }'
```

#### 4. Health Check

```bash
curl http://localhost:3000/health
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health status and version info |
| POST | `/webhook/inventory` | Process inventory data via webhook |
| POST | `/convert` | Convert items to specific target unit |

## Conversion Rules

The agent uses a configurable conversion master (`conversion-master.json`) with product-specific and default rules:

```json
{
  "conversionRules": {
    "PIECE_TO_BOX": {
      "default": 12,
      "products": {
        "SKU001": 10,
        "SKU002": 24
      }
    }
  },
  "supportedUnits": ["PIECE", "BOX", "CARTON"]
}
```

## Output Format

All processed inventory items are standardized with conversions to all supported units:

```json
{
  "sku": "SKU001",
  "originalQuantity": 120,
  "originalUnit": "PIECE",
  "standardizedUnits": {
    "PIECE": 120,
    "BOX": 12,
    "CARTON": 3
  },
  "convertedAt": "2024-01-15T10:30:00Z"
}
```

## Configuration

Configure the agent through environment variables or config files:

```bash
# Environment Variables
PORT=3000                    # Webhook server port
LOG_LEVEL=info              # Logging level (debug, info, warn, error)
CONVERSION_MASTER_PATH=./conversion-master.json
DATA_DIRECTORY=./data
LOG_DIRECTORY=./logs
```

## Logging

The agent provides comprehensive logging:

- **Console Output**: Real-time status and activity
- **File Logging**: Daily log files with timestamps
- **Processed Data**: JSON files for each processed batch in `logs/` directory

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Watcher  │    │  Webhook Server │    │  Conversion     │
│   (data/*.json) │───▶│  (Port 3000)    │───▶│  Engine         │
│   (data/*.csv)  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │  Standardized   │
                                              │  Output         │
                                              │  (logs/*.json)  │
                                              └─────────────────┘
```

## Testing

```bash
# Run unit tests
npm test

# Test with sample data
npm start
# In another terminal:
cp data/sample-inventory.json data/test-$(date +%s).json
```

## Development

### Project Structure

```
inventory-unit-conversion/
├── src/
│   ├── InventoryUnitConverter.js  # Main agent class
│   └── index.js                   # Entry point
├── data/                          # Input directory (monitored)
├── logs/                          # Output directory
├── test/                          # Unit tests
├── conversion-master.json         # Conversion rules
└── package.json
```

### Adding New Units

1. Update `conversion-master.json` with new conversion rules
2. Add the unit to `supportedUnits` array
3. Define bidirectional conversion rules
4. Test with sample data

## n8n Integration

Perfect for n8n workflows:

1. **File Node**: Monitor processed files in `logs/` directory  
2. **HTTP Request Node**: Send data to webhook endpoints
3. **Function Node**: Process standardized output data

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request
