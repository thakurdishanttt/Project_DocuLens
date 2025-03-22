# DocuLens

Docluents is a Gen AI focussed  document processing tool that applies advanced AI capabilities to automatically analyze, classify,
and extract information from a wide range of documents. By streamlining critical tasks such as data extraction, document enrichment, 
and secure storage, **DocuLens** significantly reduces manual workload, lowers processing costs, and 
drives operational efficiencies for organizations of any size.

---

## Overview

DocuLens accelerates digital transformation by enabling businesses to:
- **Process and classify** diverse documents (e.g., invoices, legal contracts, images).
- **Extract critical data** using cutting-edge AI models tailored for various industry scenarios.
- **Enhance document quality** and **retrieve information** accurately with robust OCR support for multiple languages.
- **Integrate seamlessly** with existing email or cloud drive services.
- **Enrich** extracted documents with custom-defined fields and intelligent tagging.
- **Securely store** and manage documents with version control, metadata management, and robust security.

By leveraging the **DocuLens**, companies can turn document handling from a time-intensive chore into a strategic advantage.

---

## Key Features

### 1. Document Processing
- **Intelligent Classification**  
  Automatically identifies document types (e.g., rental agreements, invoices, contracts) to reduce manual sorting time.

- **Multi-Format Support**  
  - PDF documents  
  - Images (PNG, JPEG, TIFF, BMP)  
  - Scanned documents  
  - Image-based PDFs  

This flexible approach ensures DocuLens can handle virtually any document format.

### 2. Data Extraction
- **AI-Powered Extraction**  
  Leverages cutting-edge machine learning to accurately extract key data points (e.g., dates, amounts, legal parties).

- **Smart Document Recognition**  
  Identifies documents based on existing or user-defined contract templates, speeding up onboarding and simplifying unique workflows.

- **User-Defined Contracts**  
  Allows defining custom extraction rules or field requirements. DocuLens then automatically extracts these fields across new, similar documents.

### 3. Email & Drive Integration
- **Plugin-Style Integration**  
  Plug DocuLens into your existing email or drive services, selecting specific conversations or folders to process. This eliminates the need to manually move files between systems.

### 4. Image Processing
- **Automatic Enhancement**  
  Applies features like auto-rotation, de-skewing, and brightness adjustments to improve readability before OCR.

- **OCR Capabilities**  
  - Extracts text from images or image-based PDFs.  
  - Preserves layout structures where possible.  
  - Delivers high accuracy across multiple languages.

### 5. Document Enrichment
- **Custom Enrichment Rules**  
  Define advanced tagging or categorization fields (e.g., Cost Center, Spend Category). Over time, DocuLens learns to automatically apply these tags.

- **Intelligent Categorization**  
  Reduces manual data labeling by “learning” from each new example and applying consistent categorization to future documents.

### 6. Document Management
- **Secure Storage**  
  Integration with **Supabase** ensures robust data encryption, user management, and authentication.

- **Version Control**  
  Tracks changes over time, allowing you to revert to older versions of documents or extraction outcomes.

- **Metadata Management**  
  Streamlines document retrieval and organization by storing detailed metadata (e.g., author, category, date).

---

## Technical Features

- **FastAPI** for high-performance, asynchronous request handling.
- **Background Task Processing** to handle long-running AI or OCR operations without blocking the main application flow.
- **REST API Endpoints** for easy integration with existing microservices or front-end applications.
- **Real-Time Status Updates** on document processing stages (e.g., “In Queue,” “Processing,” “Completed”).
- **Comprehensive Error Handling & Validation** to provide clear logs and enable quick debugging.
- **Detailed Logging & Monitoring** to track performance metrics and spot anomalies.
- **Type-Safe Request/Response** handling with **Pydantic** for robust data validation.

---

## Project Structure


- **`app/api/`**: REST API routes and endpoint definitions.  
- **`app/core/`**: Core configurations and environment settings for the application.  
- **`app/models/`**: Data models and database schemas (typically using Pydantic).  
- **`app/services/`**: Business logic for AI classification, OCR, and data extraction.  
- **`app/utils/`**: Helper utilities shared across the codebase.  
- **`tests/`**: Automated test suites (unit, integration, and end-to-end).

---

## Tech Stack

- **FastAPI (0.109.0)**
- **OpenAI (1.12.0)**
- **ChromaDB (0.4.22)**
- **PyTesseract (0.3.10)**
- **Whisper (1.1.10)**
- **Supabase (2.10.0)**
- **Pydantic (2.6.1)**
- Additional libraries for PDF parsing, image handling, NLP, etc..

