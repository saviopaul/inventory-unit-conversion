"""
FastAPI Server for GoFrugal Report Builder
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import logging
from portal_scraper import GoFrugalPortalScraper
import asyncio

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GoFrugal Report Builder API",
    description="API for scraping GoFrugal portal and building custom reports",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scraper instance
scraper_instance = None


class ReportRequest(BaseModel):
    report_id: Optional[int] = None
    report_url: Optional[str] = None


class SchemaResponse(BaseModel):
    report_id: Optional[int]
    report_url: str
    extracted_at: str
    columns: List[str]
    sample_data: Optional[List[str]] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GoFrugal Report Builder API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scraper_initialized": scraper_instance is not None
    }


@app.post("/api/scraper/initialize")
async def initialize_scraper():
    """Initialize the portal scraper"""
    global scraper_instance
    try:
        logger.info("Initializing scraper...")
        scraper_instance = GoFrugalPortalScraper()
        await scraper_instance.initialize()
        
        # Login
        login_success = await scraper_instance.login()
        if not login_success:
            raise HTTPException(status_code=401, detail="Login failed")
        
        return {
            "status": "success",
            "message": "Scraper initialized and logged in successfully"
        }
    except Exception as e:
        logger.error(f"Error initializing scraper: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scraper/discover-reports")
async def discover_reports():
    """Discover all available reports"""
    global scraper_instance
    
    if not scraper_instance:
        raise HTTPException(status_code=400, detail="Scraper not initialized. Call /api/scraper/initialize first")
    
    try:
        logger.info("Discovering reports...")
        reports = await scraper_instance.discover_reports()
        
        return {
            "status": "success",
            "count": len(reports),
            "reports": reports
        }
    except Exception as e:
        logger.error(f"Error discovering reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scraper/extract-schema")
async def extract_schema(request: ReportRequest):
    """Extract schema from a specific report"""
    global scraper_instance
    
    if not scraper_instance:
        raise HTTPException(status_code=400, detail="Scraper not initialized. Call /api/scraper/initialize first")
    
    try:
        logger.info(f"Extracting schema for report: {request.report_id or request.report_url}")
        schema = await scraper_instance.extract_report_schema(
            report_id=request.report_id,
            report_url=request.report_url
        )
        
        if not schema:
            raise HTTPException(status_code=404, detail="Could not extract schema from report")
        
        # Save schema
        if request.report_id:
            schema_file = f'/app/gofrugal-report-builder/database/schemas/report_{request.report_id}_schema.json'
        else:
            schema_file = f'/app/gofrugal-report-builder/database/schemas/report_custom_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(schema_file, 'w') as f:
            json.dump(schema, f, indent=2)
        
        return {
            "status": "success",
            "schema": schema,
            "saved_to": schema_file
        }
    except Exception as e:
        logger.error(f"Error extracting schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schemas")
async def list_schemas():
    """List all extracted schemas"""
    try:
        schemas_dir = '/app/gofrugal-report-builder/database/schemas'
        schema_files = [f for f in os.listdir(schemas_dir) if f.endswith('.json')]
        
        schemas = []
        for file in schema_files:
            with open(os.path.join(schemas_dir, file), 'r') as f:
                schema = json.load(f)
                schemas.append({
                    'filename': file,
                    'report_id': schema.get('report_id'),
                    'extracted_at': schema.get('extracted_at'),
                    'columns_count': len(schema.get('columns', []))
                })
        
        return {
            "status": "success",
            "count": len(schemas),
            "schemas": schemas
        }
    except Exception as e:
        logger.error(f"Error listing schemas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schemas/{report_id}")
async def get_schema(report_id: int):
    """Get schema for a specific report"""
    try:
        schema_file = f'/app/gofrugal-report-builder/database/schemas/report_{report_id}_schema.json'
        
        if not os.path.exists(schema_file):
            raise HTTPException(status_code=404, detail=f"Schema for report {report_id} not found")
        
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        
        return {
            "status": "success",
            "schema": schema
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screenshots")
async def list_screenshots():
    """List all available screenshots"""
    try:
        logs_dir = '/app/gofrugal-report-builder/logs'
        screenshots = [f for f in os.listdir(logs_dir) if f.endswith('.png')]
        
        return {
            "status": "success",
            "count": len(screenshots),
            "screenshots": screenshots
        }
    except Exception as e:
        logger.error(f"Error listing screenshots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screenshots/{filename}")
async def get_screenshot(filename: str):
    """Get a specific screenshot"""
    try:
        screenshot_path = f'/app/gofrugal-report-builder/logs/{filename}'
        
        if not os.path.exists(screenshot_path):
            raise HTTPException(status_code=404, detail=f"Screenshot {filename} not found")
        
        return FileResponse(screenshot_path, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scraper/close")
async def close_scraper():
    """Close the scraper and browser"""
    global scraper_instance
    
    if scraper_instance:
        try:
            await scraper_instance.close()
            scraper_instance = None
            return {"status": "success", "message": "Scraper closed"}
        except Exception as e:
            logger.error(f"Error closing scraper: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return {"status": "success", "message": "Scraper was not initialized"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scraper_instance
    if scraper_instance:
        try:
            await scraper_instance.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
