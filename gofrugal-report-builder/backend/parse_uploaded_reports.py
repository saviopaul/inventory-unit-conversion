import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

def parse_gofrugal_csv(filepath):
    """
    Parse GoFrugal CSV report
    Format: 
    - Line 0: Company name
    - Line 1: Report title
    - Line 2: Filters/date range
    - Line 3: Column headers
    - Line 4+: Data
    """
    try:
        # Read file to find header row
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Assuming headers are on line 3 (0-indexed)
        if len(lines) > 3:
            # Parse the report metadata
            company_name = lines[0].strip()
            report_title = lines[1].strip().strip('"')
            filters = lines[2].strip().strip('"')
            
            # Read from line 3 onwards as CSV
            df = pd.read_csv(filepath, skiprows=3)
            
            columns = df.columns.tolist()
            row_count = len(df)
            
            # Get sample data (first 2 rows) - convert to strings to avoid serialization issues
            sample_data = df.head(2).astype(str).values.tolist()
            
            return {
                'success': True,
                'company_name': company_name,
                'report_title': report_title,
                'filters': filters,
                'columns': columns,
                'column_count': len(columns),
                'row_count': row_count,
                'sample_data': sample_data,
                'format': 'csv'
            }
        else:
            return {'success': False, 'error': 'File too short'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_gofrugal_xls(filepath):
    """
    Parse GoFrugal XLS report
    """
    try:
        # Read XLS file
        df = pd.read_excel(filepath, header=None)
        
        # Similar structure: skip first few rows
        # Find the row with most non-null values (likely the header)
        header_row_idx = 0
        max_non_null = 0
        
        for idx in range(min(10, len(df))):
            non_null_count = df.iloc[idx].notna().sum()
            if non_null_count > max_non_null:
                max_non_null = non_null_count
                header_row_idx = idx
        
        # Read again with correct header
        df = pd.read_excel(filepath, header=header_row_idx)
        
        # Extract metadata from first few rows
        meta_df = pd.read_excel(filepath, header=None, nrows=header_row_idx)
        company_name = str(meta_df.iloc[0, 0]) if len(meta_df) > 0 else ''
        report_title = str(meta_df.iloc[1, 0]) if len(meta_df) > 1 else ''
        filters = str(meta_df.iloc[2, 0]) if len(meta_df) > 2 else ''
        
        columns = df.columns.tolist()
        row_count = len(df)
        
        # Get sample data (first 2 rows)
        sample_data = df.head(2).values.tolist()
        
        return {
            'success': True,
            'company_name': company_name,
            'report_title': report_title,
            'filters': filters,
            'columns': columns,
            'column_count': len(columns),
            'row_count': row_count,
            'sample_data': sample_data,
            'format': 'xls'
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def extract_report_id_from_filename(filename):
    """Extract report ID from filename like '474_Current_St...'"""
    try:
        return filename.split('_')[0]
    except:
        return 'unknown'

def create_master_schema():
    """
    Parse all uploaded reports and create master schema
    """
    print("="*80)
    print("📊 CREATING MASTER SCHEMA FROM UPLOADED REPORTS")
    print("="*80)
    
    reports_dir = "/app/gofrugal-report-builder/uploaded_reports"
    output_dir = "/app/gofrugal-report-builder/database/schemas"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    master_schema = {
        "created_at": datetime.now().isoformat(),
        "source": "uploaded_reports",
        "total_reports": 0,
        "reports": {}
    }
    
    # Get all report files
    report_files = list(Path(reports_dir).glob('report_*.*'))
    
    print(f"\nFound {len(report_files)} report files")
    print("\n" + "-"*80)
    
    for filepath in sorted(report_files):
        filename = filepath.name
        report_id = extract_report_id_from_filename(filename)
        
        print(f"\n📄 Processing: {filename}")
        print(f"   Report ID: {report_id}")
        
        # Parse based on extension
        if filename.endswith('.csv'):
            result = parse_gofrugal_csv(str(filepath))
        elif filename.endswith('.xls') or filename.endswith('.xlsx'):
            result = parse_gofrugal_xls(str(filepath))
        else:
            print(f"   ⚠️  Unsupported format")
            continue
        
        if result['success']:
            print(f"   ✅ Parsed successfully")
            print(f"   Report: {result['report_title']}")
            print(f"   Columns: {result['column_count']}")
            print(f"   Rows: {result['row_count']}")
            
            # Show first 10 columns
            print(f"\n   📋 Columns:")
            for i, col in enumerate(result['columns'][:10], 1):
                print(f"      {i}. {col}")
            if result['column_count'] > 10:
                print(f"      ... and {result['column_count'] - 10} more")
            
            # Add to master schema
            master_schema['reports'][report_id] = {
                'report_id': report_id,
                'report_name': result['report_title'],
                'company_name': result['company_name'],
                'filters': result['filters'],
                'column_count': result['column_count'],
                'columns': result['columns'],
                'row_count': result['row_count'],
                'sample_data': result['sample_data'],
                'file_format': result['format'],
                'source_file': filename
            }
            
            master_schema['total_reports'] += 1
            
        else:
            print(f"   ❌ Failed: {result['error']}")
    
    # Save master schema
    print("\n" + "="*80)
    print("💾 Saving Master Schema...")
    
    schema_file = f'{output_dir}/master_schema.json'
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(master_schema, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Master schema saved to: {schema_file}")
    
    # Save individual report schemas
    for report_id, report_data in master_schema['reports'].items():
        individual_file = f'{output_dir}/report_{report_id}_schema.json'
        with open(individual_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Individual schema: report_{report_id}_schema.json")
    
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Total reports processed: {master_schema['total_reports']}")
    print(f"\nReport IDs:")
    for report_id, data in master_schema['reports'].items():
        print(f"  - Report {report_id}: {data['report_name']} ({data['column_count']} columns)")
    
    print("\n" + "="*80)
    print("✅ SCHEMA EXTRACTION COMPLETE!")
    print("="*80)
    
    return master_schema

if __name__ == "__main__":
    master_schema = create_master_schema()
