const fs = require('fs');
const path = require('path');

console.log('📦 Preparing Next.js export for Electron...');

// Create a temporary directory for the export
const exportDir = path.join(process.cwd(), 'out');
if (fs.existsSync(exportDir)) {
  fs.rmSync(exportDir, { recursive: true, force: true });
}

// Copy only the necessary files for Electron
const copyFiles = [
  'package.json',
  'electron',
  'public',
  '.next',
  'next.config.ts'
];

console.log('✅ Export preparation completed');