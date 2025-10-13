from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path
import pandas as pd

app = FastAPI(title="GoFrugal Report Builder API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
SCHEMA_DIR = Path("/app/gofrugal-report-builder/database/schemas")
REPORTS_DIR = Path("/app/gofrugal-report-builder/uploaded_reports")

# Load master schema on startup
master_schema = {}
if (SCHEMA_DIR / "master_schema.json").exists():
    with open(SCHEMA_DIR / "master_schema.json", 'r') as f:
        master_schema = json.load(f)

# ==================== Models ====================

class ColumnInfo(BaseModel):
    column_name: str
    qualified_name: str
    display_name: str
    source_report_id: str
    source_report_name: str
    index: int

class ReportSchema(BaseModel):
    report_id: str
    report_name: str
    column_count: int
    row_count: int
    columns: List[str]

class CustomReportRequest(BaseModel):
    selected_columns: List[Dict[str, Any]]  # [{report_id, column_name, column_index}]
    filters: Optional[Dict[str, Any]] = None
    join_keys: Optional[List[str]] = None  # ["item_code", "date"]

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

# ==================== Endpoints ====================

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "reports_loaded": len(master_schema.get("reports", {}))}

@app.get("/api/reports")
async def get_all_reports():
    """Get list of all available reports"""
    reports = master_schema.get("reports", {})
    report_list = []
    
    for report_id, report_data in reports.items():
        report_list.append({
            "report_id": report_id,
            "report_name": report_data["report_name"].strip(),
            "column_count": report_data["column_count"],
            "row_count": report_data["row_count"],
            "source_file": report_data.get("source_file", "")
        })
    
    return {
        "total": len(report_list),
        "reports": sorted(report_list, key=lambda x: x["report_id"])
    }

@app.get("/api/reports/{report_id}")
async def get_report_schema(report_id: str):
    """Get detailed schema for a specific report"""
    reports = master_schema.get("reports", {})
    
    if report_id not in reports:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    report_data = reports[report_id]
    
    # Enhance columns with qualified names
    enhanced_columns = []
    for idx, col_name in enumerate(report_data["columns"]):
        enhanced_columns.append({
            "column_name": col_name,
            "qualified_name": f"Report_{report_id}.{col_name}",
            "display_name": f"{col_name} (Report {report_id})",
            "source_report_id": report_id,
            "source_report_name": report_data["report_name"].strip(),
            "index": idx
        })
    
    return {
        "report_id": report_id,
        "report_name": report_data["report_name"].strip(),
        "company_name": report_data.get("company_name", ""),
        "filters": report_data.get("filters", ""),
        "column_count": report_data["column_count"],
        "row_count": report_data["row_count"],
        "columns": enhanced_columns,
        "sample_data": report_data.get("sample_data", [])[:5]  # First 5 rows
    }

@app.get("/api/reports/{report_id}/columns")
async def get_report_columns(report_id: str):
    """Get just the columns for a specific report"""
    reports = master_schema.get("reports", {})
    
    if report_id not in reports:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    report_data = reports[report_id]
    columns = []
    
    for idx, col_name in enumerate(report_data["columns"]):
        columns.append({
            "name": col_name,
            "qualified_name": f"{report_id}.{col_name}",
            "index": idx
        })
    
    return {"report_id": report_id, "columns": columns}

@app.post("/api/reports/custom/preview")
async def preview_custom_report(request: CustomReportRequest):
    """Preview a custom report with selected columns"""
    try:
        # Group columns by report
        columns_by_report = {}
        for col in request.selected_columns:
            report_id = col["report_id"]
            if report_id not in columns_by_report:
                columns_by_report[report_id] = []
            columns_by_report[report_id].append(col)
        
        # Load data from each report
        dataframes = {}
        for report_id, columns in columns_by_report.items():
            report_data = master_schema["reports"][report_id]
            source_file = REPORTS_DIR / report_data["source_file"]
            
            if not source_file.exists():
                continue
            
            # Load based on file type
            if source_file.suffix == '.csv':
                df = pd.read_csv(source_file, skiprows=3)
            else:
                # Find header row for XLS
                df_temp = pd.read_excel(source_file, header=None)
                header_row = 0
                for idx in range(min(10, len(df_temp))):
                    if df_temp.iloc[idx].notna().sum() > len(df_temp.columns) * 0.5:
                        header_row = idx
                        break
                df = pd.read_excel(source_file, header=header_row)
            
            # Select only requested columns
            col_indices = [c["column_index"] for c in columns]
            col_names = [df.columns[i] for i in col_indices]
            df_selected = df[col_names]
            
            # Rename columns with report prefix
            df_selected.columns = [f"{report_id}_{col}" for col in df_selected.columns]
            
            dataframes[report_id] = df_selected
        
        # Merge dataframes if join keys specified
        if request.join_keys and len(dataframes) > 1:
            # For now, simple merge on first common column
            result_df = list(dataframes.values())[0]
            for df in list(dataframes.values())[1:]:
                # This is a simplified join - will enhance later
                result_df = pd.concat([result_df, df], axis=1)
        else:
            # Just concatenate columns
            result_df = pd.concat(list(dataframes.values()), axis=1)
        
        # Get preview (first 50 rows)
        preview_data = result_df.head(50).fillna("").astype(str).values.tolist()
        column_names = result_df.columns.tolist()
        
        return {
            "success": True,
            "columns": column_names,
            "row_count": len(result_df),
            "preview_rows": len(preview_data),
            "data": preview_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """AI chatbot endpoint for natural language report building"""
    try:
        # For now, return a mock response
        # Will implement full LLM integration
        
        message = request.message.lower()
        
        # Simple pattern matching for demo
        if "dsr" in message or "daily sales" in message:
            response = {
                "message": "I understand you want to create a DSR (Daily Sales Report). I'll need data from:\n\n" +
                          "• Report 474 (Current Stock) - for opening/closing stock\n" +
                          "• Report 521 (Sales) - for sales transactions\n" +
                          "• Report 40000006 (Transfer Out) - for transfers\n\n" +
                          "Should I proceed with creating this report?",
                "suggested_columns": [
                    {"report_id": "474", "column": "Item Code", "reason": "Join key"},
                    {"report_id": "474", "column": "Item Name", "reason": "Item identification"},
                    {"report_id": "521", "column": "Qty", "reason": "Sales quantity"},
                    {"report_id": "40000006", "column": "TO Qty", "reason": "Transfer quantity"}
                ],
                "action": "confirm"
            }
        elif "stock" in message:
            response = {
                "message": "I found stock data in Report 474 (Current Stock - Item Wise Detail). " +
                          "This report has 39 columns including Item Code, Item Name, Stock Quantity, and Location.\n\n" +
                          "What specific stock information do you need?",
                "suggested_reports": ["474"],
                "action": "clarify"
            }
        elif "sales" in message:
            response = {
                "message": "Sales data is available in Report 521 (Sales - Bill Wise Item Detailed). " +
                          "It has 121 columns including Bill Date, Item details, Quantities, Amounts, and Tax information.\n\n" +
                          "Which columns would you like to include?",
                "suggested_reports": ["521"],
                "action": "clarify"
            }
        else:
            response = {
                "message": "I can help you build custom reports from your 5 available reports:\n\n" +
                          "• Report 335: Invoice Wise Item Detailed (45 columns)\n" +
                          "• Report 40000006: Transfer Out Consolidated (19 columns)\n" +
                          "• Report 474: Current Stock Detail (39 columns)\n" +
                          "• Report 521: Sales Bill Wise Detail (121 columns)\n" +
                          "• Report 677: Sales Tenderwise (59 columns)\n\n" +
                          "Try asking:\n" +
                          "- 'Create a DSR report'\n" +
                          "- 'Show me stock data'\n" +
                          "- 'I need sales report with item names and quantities'",
                "action": "help"
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
