#!/usr/bin/env node

import InventoryUnitConverter from './InventoryUnitConverter.js';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Main entry point for the InventoryUnitConverter always-on agent
 */
async function main() {
  console.log('🚀 Starting InventoryUnitConverter Always-On Agent');
  
  // Configuration
  const config = {
    conversionMasterPath: path.join(__dirname, '../conversion-master.json'),
    dataDirectory: path.join(__dirname, '../data'),
    logDirectory: path.join(__dirname, '../logs'),
    enableWebhook: true,
    webhookPort: process.env.PORT || 3000,
    enableFileWatcher: true,
    logLevel: process.env.LOG_LEVEL || 'info'
  };

  // Create converter instance
  const converter = new InventoryUnitConverter(config);

  // Setup event listeners
  converter.on('initialized', () => {
    console.log('✅ InventoryUnitConverter agent is now running');
    console.log(`📡 Webhook server: http://localhost:${config.webhookPort}`);
    console.log(`📁 Watching directory: ${config.dataDirectory}`);
    console.log(`📝 Logs directory: ${config.logDirectory}`);
  });

  converter.on('fileProcessed', ({ filePath, result }) => {
    console.log(`📄 Processed file: ${filePath} (${result.items.length} items)`);
  });

  converter.on('processingError', ({ filePath, error }) => {
    console.error(`❌ Error processing ${filePath}: ${error.message}`);
  });

  converter.on('log', ({ level, message }) => {
    if (level === 'error') {
      console.error(`🔴 ${message}`);
    } else if (level === 'warn') {
      console.warn(`🟡 ${message}`);
    }
  });

  // Graceful shutdown handling
  process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down InventoryUnitConverter agent...');
    try {
      await converter.stop();
      console.log('✅ Agent stopped gracefully');
      process.exit(0);
    } catch (error) {
      console.error('❌ Error during shutdown:', error.message);
      process.exit(1);
    }
  });

  process.on('SIGTERM', async () => {
    console.log('\n🛑 Received SIGTERM, shutting down...');
    try {
      await converter.stop();
      process.exit(0);
    } catch (error) {
      console.error('❌ Error during shutdown:', error.message);
      process.exit(1);
    }
  });

  // Handle uncaught exceptions
  process.on('uncaughtException', (error) => {
    console.error('💥 Uncaught Exception:', error);
    process.exit(1);
  });

  process.on('unhandledRejection', (reason, promise) => {
    console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
  });

  try {
    // Initialize and start the agent
    await converter.initialize();
    
    console.log('🔄 Agent is running continuously. Press Ctrl+C to stop.');
    
    // Keep the process alive
    setInterval(() => {
      const status = converter.getStatus();
      if (!status.running) {
        console.error('❌ Agent stopped unexpectedly');
        process.exit(1);
      }
    }, 30000); // Check every 30 seconds
    
  } catch (error) {
    console.error('💥 Failed to start InventoryUnitConverter agent:', error.message);
    process.exit(1);
  }
}

// Run the agent
main().catch(console.error);