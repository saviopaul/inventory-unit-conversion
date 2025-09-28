import fs from 'fs-extra';
import path from 'path';
import chokidar from 'chokidar';
import { EventEmitter } from 'events';

/**
 * InventoryUnitConverter - Always-on agent for inventory unit conversion
 * Auto-detects new inventory data and standardizes units using conversion rules
 */
export class InventoryUnitConverter extends EventEmitter {
  constructor(config = {}) {
    super();
    
    this.config = {
      conversionMasterPath: config.conversionMasterPath || './conversion-master.json',
      dataDirectory: config.dataDirectory || './data',
      logDirectory: config.logDirectory || './logs',
      enableWebhook: config.enableWebhook || true,
      webhookPort: config.webhookPort || 3000,
      enableFileWatcher: config.enableFileWatcher || true,
      logLevel: config.logLevel || 'info',
      ...config
    };

    this.conversionRules = null;
    this.isRunning = false;
    this.fileWatcher = null;
    this.webServer = null;
    
    this.setupLogging();
  }

  /**
   * Initialize the converter agent
   */
  async initialize() {
    try {
      this.log('info', 'Initializing InventoryUnitConverter agent');
      
      // Load conversion master data
      await this.loadConversionMaster();
      
      // Setup file watcher if enabled
      if (this.config.enableFileWatcher) {
        await this.setupFileWatcher();
      }
      
      // Setup webhook server if enabled
      if (this.config.enableWebhook) {
        await this.setupWebhookServer();
      }
      
      this.isRunning = true;
      this.log('info', 'InventoryUnitConverter agent initialized successfully');
      this.emit('initialized');
      
    } catch (error) {
      this.log('error', `Failed to initialize converter: ${error.message}`);
      throw error;
    }
  }

  /**
   * Load conversion master data from JSON file
   */
  async loadConversionMaster() {
    try {
      if (!await fs.pathExists(this.config.conversionMasterPath)) {
        throw new Error(`Conversion master file not found: ${this.config.conversionMasterPath}`);
      }
      
      const masterData = await fs.readJson(this.config.conversionMasterPath);
      this.conversionRules = masterData;
      
      this.log('info', `Loaded conversion master v${masterData.version}`);
      this.emit('conversionMasterLoaded', masterData);
      
    } catch (error) {
      this.log('error', `Failed to load conversion master: ${error.message}`);
      throw error;
    }
  }

  /**
   * Setup file system watcher for auto-detection of new inventory data
   */
  async setupFileWatcher() {
    try {
      // Ensure data directory exists
      await fs.ensureDir(this.config.dataDirectory);
      
      this.fileWatcher = chokidar.watch(this.config.dataDirectory, {
        ignored: /^\./,
        persistent: true,
        ignoreInitial: false
      });

      this.fileWatcher.on('add', (filePath) => {
        this.log('info', `New file detected: ${filePath}`);
        this.processInventoryFile(filePath);
      });

      this.fileWatcher.on('change', (filePath) => {
        this.log('info', `File changed: ${filePath}`);
        this.processInventoryFile(filePath);
      });

      this.log('info', `File watcher setup for directory: ${this.config.dataDirectory}`);
      
    } catch (error) {
      this.log('error', `Failed to setup file watcher: ${error.message}`);
      throw error;
    }
  }

  /**
   * Setup webhook server for API input
   */
  async setupWebhookServer() {
    const express = await import('express');
    const app = express.default();
    
    app.use(express.json());
    
    // Health check endpoint
    app.get('/health', (req, res) => {
      res.json({ 
        status: 'healthy', 
        version: this.conversionRules?.version,
        running: this.isRunning 
      });
    });

    // Webhook endpoint for inventory data
    app.post('/webhook/inventory', (req, res) => {
      try {
        this.log('info', 'Received inventory data via webhook');
        const result = this.processInventoryData(req.body);
        res.json({ success: true, result });
      } catch (error) {
        this.log('error', `Webhook processing error: ${error.message}`);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Direct conversion endpoint
    app.post('/convert', (req, res) => {
      try {
        const { items, targetUnit } = req.body;
        const result = this.convertUnits(items, targetUnit);
        res.json({ success: true, result });
      } catch (error) {
        this.log('error', `Conversion API error: ${error.message}`);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    return new Promise((resolve, reject) => {
      this.webServer = app.listen(this.config.webhookPort, (error) => {
        if (error) {
          this.log('error', `Failed to start webhook server: ${error.message}`);
          reject(error);
        } else {
          this.log('info', `Webhook server running on port ${this.config.webhookPort}`);
          resolve();
        }
      });
    });
  }

  /**
   * Process inventory file (JSON/CSV)
   */
  async processInventoryFile(filePath) {
    try {
      const ext = path.extname(filePath).toLowerCase();
      let data;

      if (ext === '.json') {
        data = await fs.readJson(filePath);
      } else if (ext === '.csv') {
        // Simple CSV parsing for demo - in production, use a proper CSV parser
        const csvContent = await fs.readFile(filePath, 'utf8');
        data = this.parseCSV(csvContent);
      } else {
        this.log('warn', `Unsupported file type: ${ext}`);
        return;
      }

      const result = this.processInventoryData(data);
      await this.saveProcessedData(filePath, result);
      
      this.emit('fileProcessed', { filePath, result });
      
    } catch (error) {
      this.log('error', `Failed to process file ${filePath}: ${error.message}`);
      this.emit('processingError', { filePath, error });
    }
  }

  /**
   * Process inventory data and standardize units
   */
  processInventoryData(data) {
    this.log('info', 'Processing inventory data for unit standardization');
    
    if (!data || !Array.isArray(data.items)) {
      throw new Error('Invalid inventory data format. Expected { items: [] }');
    }

    const processedItems = data.items.map(item => {
      return this.standardizeItem(item);
    });

    const result = {
      ...data,
      items: processedItems,
      processedAt: new Date().toISOString(),
      conversionVersion: this.conversionRules.version
    };

    this.log('info', `Processed ${processedItems.length} inventory items`);
    return result;
  }

  /**
   * Standardize a single inventory item's units
   */
  standardizeItem(item) {
    const { sku, quantity, unit, ...rest } = item;
    
    if (!sku || !quantity || !unit) {
      this.log('warn', `Invalid item format: ${JSON.stringify(item)}`);
      return { ...item, error: 'Missing required fields: sku, quantity, unit' };
    }

    try {
      // Convert to all standard units
      const conversions = {};
      
      for (const targetUnit of this.conversionRules.supportedUnits) {
        if (unit === targetUnit) {
          conversions[targetUnit] = quantity;
        } else {
          conversions[targetUnit] = this.convertUnit(quantity, unit, targetUnit, sku);
        }
      }

      return {
        ...rest,
        sku,
        originalQuantity: quantity,
        originalUnit: unit,
        standardizedUnits: conversions,
        convertedAt: new Date().toISOString()
      };
      
    } catch (error) {
      this.log('error', `Failed to standardize item ${sku}: ${error.message}`);
      return { ...item, error: error.message };
    }
  }

  /**
   * Convert units using conversion rules
   */
  convertUnit(quantity, fromUnit, toUnit, sku = null) {
    if (fromUnit === toUnit) {
      return quantity;
    }

    const conversionKey = `${fromUnit}_TO_${toUnit}`;
    const rules = this.conversionRules.conversionRules[conversionKey];
    
    if (!rules) {
      throw new Error(`No conversion rule found for ${fromUnit} to ${toUnit}`);
    }

    // Use product-specific rule if available, otherwise use default
    const conversionFactor = (sku && rules.products[sku]) ? rules.products[sku] : rules.default;
    
    // Determine if we're converting up or down the hierarchy
    const hierarchy = this.conversionRules.unitHierarchy;
    const fromIndex = hierarchy.indexOf(fromUnit);
    const toIndex = hierarchy.indexOf(toUnit);
    
    let result;
    if (fromIndex < toIndex) {
      // Converting from smaller to larger unit (e.g., PIECE to BOX)
      result = quantity / conversionFactor;
    } else {
      // Converting from larger to smaller unit (e.g., BOX to PIECE)
      result = quantity * conversionFactor;
    }
    
    this.log('debug', `Converted ${quantity} ${fromUnit} to ${result} ${toUnit} for ${sku || 'default'}`);
    
    return Math.round(result * 100) / 100; // Round to 2 decimal places
  }

  /**
   * Convert multiple items to target unit
   */
  convertUnits(items, targetUnit) {
    return items.map(item => {
      const converted = this.convertUnit(item.quantity, item.unit, targetUnit, item.sku);
      return {
        ...item,
        convertedQuantity: converted,
        convertedUnit: targetUnit,
        conversionFactor: converted / item.quantity
      };
    });
  }

  /**
   * Save processed data to logs
   */
  async saveProcessedData(originalPath, processedData) {
    try {
      const fileName = path.basename(originalPath, path.extname(originalPath));
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const outputPath = path.join(this.config.logDirectory, `processed_${fileName}_${timestamp}.json`);
      
      await fs.ensureDir(this.config.logDirectory);
      await fs.writeJson(outputPath, processedData, { spaces: 2 });
      
      this.log('info', `Saved processed data to: ${outputPath}`);
      
    } catch (error) {
      this.log('error', `Failed to save processed data: ${error.message}`);
    }
  }

  /**
   * Simple CSV parser (for demo purposes)
   */
  parseCSV(csvContent) {
    const lines = csvContent.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    const items = lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim());
      const item = {};
      
      headers.forEach((header, index) => {
        const value = values[index];
        // Try to parse as number if it looks like one
        item[header] = /^\d+(\.\d+)?$/.test(value) ? parseFloat(value) : value;
      });
      
      return item;
    });

    return { items };
  }

  /**
   * Setup logging functionality
   */
  setupLogging() {
    this.logFile = path.join(this.config.logDirectory, `converter_${new Date().toISOString().split('T')[0]}.log`);
    
    // Ensure log directory exists
    fs.ensureDirSync(this.config.logDirectory);
  }

  /**
   * Log messages with timestamp
   */
  log(level, message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    
    // Console output
    console.log(logMessage);
    
    // File logging
    try {
      fs.appendFileSync(this.logFile, logMessage + '\n');
    } catch (error) {
      console.error('Failed to write to log file:', error.message);
    }
    
    // Emit log event
    this.emit('log', { level, message, timestamp });
  }

  /**
   * Reload conversion master data
   */
  async reloadConversionMaster() {
    this.log('info', 'Reloading conversion master data');
    await this.loadConversionMaster();
  }

  /**
   * Stop the converter agent
   */
  async stop() {
    this.log('info', 'Stopping InventoryUnitConverter agent');
    
    this.isRunning = false;
    
    if (this.fileWatcher) {
      await this.fileWatcher.close();
      this.fileWatcher = null;
    }
    
    if (this.webServer) {
      await new Promise((resolve) => {
        this.webServer.close(resolve);
      });
      this.webServer = null;
    }
    
    this.log('info', 'InventoryUnitConverter agent stopped');
    this.emit('stopped');
  }

  /**
   * Get current status
   */
  getStatus() {
    return {
      running: this.isRunning,
      conversionVersion: this.conversionRules?.version,
      config: this.config,
      supportedUnits: this.conversionRules?.supportedUnits || []
    };
  }
}

export default InventoryUnitConverter;