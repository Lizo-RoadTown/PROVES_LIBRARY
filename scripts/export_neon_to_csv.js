/**
 * Export Neon database tables to CSV files
 *
 * Usage: node scripts/export_neon_to_csv.js
 *
 * Creates CSV files that can be imported into Supabase
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// Neon connection string
const NEON_URL = "postgresql://neondb_owner:npg_GvP5x0yVrCLm@ep-empty-morning-af4l9ocx-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require";

// Output directory
const OUTPUT_DIR = path.join(__dirname, '..', 'neon_exports');

// Tables to export (in order for import)
const TABLES = [
  'raw_snapshots',
  'staging_extractions',
  'human_decisions',
  'pipeline_runs'
];

async function exportTable(client, tableName) {
  console.log(`\n📦 Exporting ${tableName}...`);

  try {
    // Get row count
    const countResult = await client.query(`SELECT COUNT(*) FROM ${tableName}`);
    const rowCount = parseInt(countResult.rows[0].count);
    console.log(`   Found ${rowCount} rows`);

    if (rowCount === 0) {
      console.log(`   ⚠️  No data to export`);
      return null;
    }

    // Get all data
    const result = await client.query(`SELECT * FROM ${tableName}`);

    if (result.rows.length === 0) {
      return null;
    }

    // Get column names
    const columns = Object.keys(result.rows[0]);

    // Create CSV content
    let csv = columns.join(',') + '\n';

    for (const row of result.rows) {
      const values = columns.map(col => {
        const value = row[col];
        if (value === null || value === undefined) {
          return '';
        }
        // Handle objects/arrays (JSONB)
        if (typeof value === 'object') {
          return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
        }
        // Handle strings with special characters
        if (typeof value === 'string') {
          if (value.includes(',') || value.includes('"') || value.includes('\n')) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value;
        }
        return String(value);
      });
      csv += values.join(',') + '\n';
    }

    // Write to file
    const filePath = path.join(OUTPUT_DIR, `${tableName}.csv`);
    fs.writeFileSync(filePath, csv);

    console.log(`   ✓ Exported to ${filePath}`);
    return filePath;

  } catch (error) {
    if (error.message.includes('does not exist')) {
      console.log(`   ⚠️  Table does not exist`);
    } else {
      console.log(`   ❌ Error: ${error.message}`);
    }
    return null;
  }
}

async function main() {
  console.log('=' .repeat(60));
  console.log('  Neon Database Export to CSV');
  console.log('=' .repeat(60));

  // Create output directory
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  console.log(`\nOutput directory: ${OUTPUT_DIR}`);

  // Connect to Neon
  const client = new Client({ connectionString: NEON_URL });

  try {
    await client.connect();
    console.log('✓ Connected to Neon');

    const exportedFiles = [];

    for (const table of TABLES) {
      const filePath = await exportTable(client, table);
      if (filePath) {
        exportedFiles.push({ table, filePath });
      }
    }

    console.log('\n' + '=' .repeat(60));
    console.log('  Export Complete!');
    console.log('=' .repeat(60));

    if (exportedFiles.length > 0) {
      console.log('\nExported files:');
      for (const { table, filePath } of exportedFiles) {
        console.log(`  - ${table}: ${filePath}`);
      }

      console.log('\n📥 To import into Supabase:');
      console.log('   1. Go to https://supabase.com/dashboard');
      console.log('   2. Open your project > Table Editor');
      console.log('   3. Select a table and click "Insert" > "Import data from CSV"');
      console.log('   4. Upload the corresponding CSV file');
      console.log('\n⚠️  IMPORTANT: Import in this order to avoid FK errors:');
      console.log('   1. raw_snapshots.csv (first - no dependencies)');
      console.log('   2. staging_extractions.csv (second - depends on raw_snapshots)');
      console.log('   3. human_decisions.csv (third - depends on staging_extractions)');
      console.log('   4. pipeline_runs.csv (independent)');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

main();
