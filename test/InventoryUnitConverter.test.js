import { test, describe, before, after } from 'node:test';
import assert from 'node:assert';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import InventoryUnitConverter from '../src/InventoryUnitConverter.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Test configuration
const testConfig = {
  conversionMasterPath: path.join(__dirname, '../conversion-master.json'),
  dataDirectory: path.join(__dirname, '../test-data'),
  logDirectory: path.join(__dirname, '../test-logs'),
  enableWebhook: false,
  enableFileWatcher: false,
  logLevel: 'error' // Reduce noise during tests
};

describe('InventoryUnitConverter', () => {
  let converter;

  before(async () => {
    // Setup test directories
    await fs.ensureDir(testConfig.dataDirectory);
    await fs.ensureDir(testConfig.logDirectory);
    
    converter = new InventoryUnitConverter(testConfig);
    await converter.initialize();
  });

  after(async () => {
    if (converter) {
      await converter.stop();
    }
    // Cleanup test directories
    await fs.remove(testConfig.dataDirectory);
    await fs.remove(testConfig.logDirectory);
  });

  test('should initialize successfully', () => {
    assert.strictEqual(converter.isRunning, true);
    assert.ok(converter.conversionRules);
    assert.strictEqual(converter.conversionRules.version, '1.0.0');
  });

  test('should convert PIECE to BOX correctly', () => {
    const result = converter.convertUnit(24, 'PIECE', 'BOX', 'SKU002');
    assert.strictEqual(result, 1); // SKU002 has 24 pieces per box
  });

  test('should convert BOX to CARTON correctly', () => {
    const result = converter.convertUnit(8, 'BOX', 'CARTON', 'SKU002');
    assert.strictEqual(result, 1); // SKU002 has 8 boxes per carton
  });

  test('should convert PIECE to CARTON correctly', () => {
    const result = converter.convertUnit(192, 'PIECE', 'CARTON', 'SKU002');
    assert.strictEqual(result, 1); // SKU002 has 192 pieces per carton
  });

  test('should use default conversion when SKU not found', () => {
    const result = converter.convertUnit(12, 'PIECE', 'BOX', 'UNKNOWN_SKU');
    assert.strictEqual(result, 1); // Default is 12 pieces per box
  });

  test('should return same quantity for same unit conversion', () => {
    const result = converter.convertUnit(100, 'PIECE', 'PIECE', 'SKU001');
    assert.strictEqual(result, 100);
  });

  test('should throw error for unsupported conversion', () => {
    assert.throws(() => {
      converter.convertUnit(10, 'INVALID_UNIT', 'PIECE', 'SKU001');
    }, /No conversion rule found/);
  });

  test('should standardize inventory item correctly', () => {
    const item = {
      sku: 'SKU001',
      name: 'Test Widget',
      quantity: 120,
      unit: 'PIECE',
      category: 'Test'
    };

    const result = converter.standardizeItem(item);
    
    assert.strictEqual(result.sku, 'SKU001');
    assert.strictEqual(result.originalQuantity, 120);
    assert.strictEqual(result.originalUnit, 'PIECE');
    assert.ok(result.standardizedUnits);
    assert.strictEqual(result.standardizedUnits.PIECE, 120);
    assert.strictEqual(result.standardizedUnits.BOX, 12); // 120/10 for SKU001
    assert.strictEqual(result.standardizedUnits.CARTON, 3); // 120/40 for SKU001
  });

  test('should handle invalid item format', () => {
    const invalidItem = { name: 'Invalid Item' }; // Missing sku, quantity, unit
    
    const result = converter.standardizeItem(invalidItem);
    
    assert.ok(result.error);
    assert.match(result.error, /Missing required fields/);
  });

  test('should process inventory data correctly', () => {
    const inventoryData = {
      source: 'test-outlet',
      items: [
        { sku: 'SKU001', quantity: 60, unit: 'PIECE', name: 'Widget 1' },
        { sku: 'SKU002', quantity: 2, unit: 'BOX', name: 'Widget 2' }
      ]
    };

    const result = converter.processInventoryData(inventoryData);
    
    assert.strictEqual(result.source, 'test-outlet');
    assert.strictEqual(result.items.length, 2);
    assert.ok(result.processedAt);
    assert.strictEqual(result.conversionVersion, '1.0.0');
    
    // Check first item conversion
    const item1 = result.items[0];
    assert.strictEqual(item1.sku, 'SKU001');
    assert.strictEqual(item1.standardizedUnits.PIECE, 60);
    assert.strictEqual(item1.standardizedUnits.BOX, 6); // 60/10
    assert.strictEqual(item1.standardizedUnits.CARTON, 1.5); // 60/40
  });

  test('should throw error for invalid inventory data format', () => {
    const invalidData = { source: 'test' }; // Missing items array
    
    assert.throws(() => {
      converter.processInventoryData(invalidData);
    }, /Invalid inventory data format/);
  });

  test('should parse CSV correctly', () => {
    const csvContent = `sku,name,quantity,unit
SKU001,Widget A,100,PIECE
SKU002,Widget B,5,BOX`;
    
    const result = converter.parseCSV(csvContent);
    
    assert.ok(result.items);
    assert.strictEqual(result.items.length, 2);
    assert.strictEqual(result.items[0].sku, 'SKU001');
    assert.strictEqual(result.items[0].quantity, 100);
    assert.strictEqual(result.items[1].sku, 'SKU002');
    assert.strictEqual(result.items[1].quantity, 5);
  });

  test('should convert multiple items to target unit', () => {
    const items = [
      { sku: 'SKU001', quantity: 30, unit: 'PIECE' },
      { sku: 'SKU002', quantity: 2, unit: 'BOX' }
    ];

    const result = converter.convertUnits(items, 'BOX');
    
    assert.strictEqual(result.length, 2);
    assert.strictEqual(result[0].convertedQuantity, 3); // 30/10 pieces to box
    assert.strictEqual(result[0].convertedUnit, 'BOX');
    assert.strictEqual(result[1].convertedQuantity, 2); // Already in BOX
    assert.strictEqual(result[1].convertedUnit, 'BOX');
  });

  test('should get correct status', () => {
    const status = converter.getStatus();
    
    assert.strictEqual(status.running, true);
    assert.strictEqual(status.conversionVersion, '1.0.0');
    assert.ok(status.config);
    assert.ok(Array.isArray(status.supportedUnits));
    assert.strictEqual(status.supportedUnits.length, 3);
  });
});