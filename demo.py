import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from extract_thinker import (
    Extractor, Classification, Process, ClassificationStrategy,
    DocumentLoaderPyPdf, Contract
)
import tempfile
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audit_report_processor")
file_handler = RotatingFileHandler("audit_report_processor.log", maxBytes=10485760, backupCount=5)
console_handler = logging.StreamHandler()
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Audit Report Processing API",
    description="API for classifying and extracting data from audit report documents",
    version="1.0.0"
)

# Contract Definitions
class AuditReportContract(Contract):
    audit_report_number: str
    audit_report_date: str
    audit_report_type: str
    findings: Optional[str]
    recommendations: Optional[str]
    risk_level: Optional[str]

class InvoiceContract(Contract):
    invoice_number: str
    invoice_date: str

# Response Models
class AuditReportResponse(BaseModel):
    filename: str
    audit_report_number: str
    audit_report_date: str
    audit_report_type: str
    findings: Optional[str]
    recommendations: Optional[str]
    risk_level: Optional[str]
    error: Optional[str] = None

class ClassificationResponse(BaseModel):
    filename: str
    is_audit_report: bool
    confidence: float
    error: Optional[str] = None

class DetailedAuditResponse(BaseModel):
    filename: str
    is_audit_report: bool
    confidence: float
    extracted_data: Optional[AuditReportResponse]
    error: Optional[str] = None

# Initialize extractor
extractor = Extractor()
extractor.load_document_loader(DocumentLoaderPyPdf())
extractor.load_llm("gpt-4o-mini")

# Define classifications
classifications = [
    Classification(
        name="Audit Report",
        description="An audit report document containing findings and recommendations",
        contract=AuditReportContract,
        extractor=extractor,
    ),
    Classification(
        name="Invoice",
        description="An invoice document",
        contract=InvoiceContract,
        extractor=extractor,
    )
]

@app.post("/classify", response_model=ClassificationResponse)
async def classify_document(file: UploadFile = File(...)):
    """
    Classify if the document is an audit report
    """
    logger.info(f"Classifying document: {file.filename}")
    
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(contents)
            temp_file_path = temp_file.name
            
        try:
            classification_result = extractor.classify(
                temp_file_path,
                classifications,
                image=True
            )
            
            is_audit = classification_result and classification_result.name == "Audit Report"
            
            return ClassificationResponse(
                filename=file.filename,
                is_audit_report=is_audit,
                confidence=classification_result.confidence if classification_result else 0.0,
                error=None if classification_result else "Classification failed"
            )
            
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error classifying document: {str(e)}", exc_info=True)
        return ClassificationResponse(
            filename=file.filename,
            is_audit_report=False,
            confidence=0.0,
            error=str(e)
        )

@app.post("/extract-audit-report", response_model=AuditReportResponse)
async def extract_audit_report(file: UploadFile = File(...)):
    """
    Extract data from audit report
    """
    logger.info(f"Processing audit report: {file.filename}")
    
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(contents)
            temp_file_path = temp_file.name
            
        try:
            result = extractor.extract(temp_file_path, AuditReportContract)
            logger.info(f"Extraction Result: {result}")
            
            if not result:
                return AuditReportResponse(
                    filename=file.filename,
                    audit_report_number="",
                    audit_report_date="",
                    audit_report_type="",
                    error="Failed to extract data"
                )
            
            return AuditReportResponse(
                filename=file.filename,
                audit_report_number=result.audit_report_number,
                audit_report_date=result.audit_report_date,
                audit_report_type=result.audit_report_type,
                findings=getattr(result, 'findings', None),
                recommendations=getattr(result, 'recommendations', None),
                risk_level=getattr(result, 'risk_level', None)
            )
            
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error processing audit report {file.filename}: {str(e)}", exc_info=True)
        return AuditReportResponse(
            filename=file.filename,
            audit_report_number="",
            audit_report_date="",
            audit_report_type="",
            error=str(e)
        )

@app.post("/process-complete", response_model=DetailedAuditResponse)
async def process_complete(file: UploadFile = File(...)):
    """
    Complete process: classify and extract if it's an audit report
    """
    logger.info(f"Starting complete processing for: {file.filename}")
    
    # First classify
    classification_result = await classify_document(file)
    
    if not classification_result.is_audit_report:
        return DetailedAuditResponse(
            filename=file.filename,
            is_audit_report=False,
            confidence=classification_result.confidence,
            extracted_data=None,
            error="Document is not an audit report"
        )
    
    # Then extract
    extraction_result = await extract_audit_report(file)
    
    return DetailedAuditResponse(
        filename=file.filename,
        is_audit_report=True,
        confidence=classification_result.confidence,
        extracted_data=extraction_result,
        error=extraction_result.error if extraction_result.error else None
    )

@app.get("/health")
def health_check():
    """
    Check API health
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)