# AI-Based Vehicle Damage Estimation and Claims Assessment

## Overview

This project was developed as part of a Final Year Project (PFE) in collaboration with COMAR Assurances.

The objective of the project is to automate and assist the insurance claims assessment process by combining Computer Vision, OCR, Large Language Models (LLMs), and Information Retrieval techniques.

The system allows users to upload vehicle images and accident reports (Constats), automatically detects damaged vehicle parts, extracts relevant information from accident documents, retrieves similar historical claims, and estimates repair costs based on previous cases.

---

## Key Features

### Vehicle Damage Detection
- Damage detection using YOLOv8.
- Identification of damaged vehicle parts.
- Automatic analysis of uploaded vehicle images.

### Accident Report Analysis
- OCR-based extraction from accident reports (Constats).
- Information extraction using LLMs.
- Extraction of:
  - Accident date
  - Accident time
  - Accident location
  - Vehicle information
  - Driver information
  - Witness information

### Similar Claims Retrieval
- Historical claims are indexed in a Vector Database.
- Hybrid retrieval approach combining:
  - Semantic Search
  - BM25 Ranking
- Automotive domain normalization for handling synonyms and abbreviations.

### Cost Estimation
- Retrieval of similar historical claims.
- Estimation of repair costs using previous claim data.
- Spare parts price lookup integration.

### User Management
- Admin account management.
- User authentication and authorization.
- Claim submission and consultation.

---

## System Architecture

```text
                                    ┌───────────────────────┐
                                    │       USER            │
                                    └───────────┬───────────┘
                                                │
                    ┌───────────────────────────┴───────────────────────────┐
                    │                                                       │
                    ▼                                                       ▼

        ┌───────────────────────┐                           ┌───────────────────────┐
        │   Vehicle Image       │                           │ Accident Report       │
        │      Upload           │                           │     (Constat)         │
        └───────────┬───────────┘                           └───────────┬───────────┘
                    │                                                   │
                    ▼                                                   ▼

        ┌───────────────────────┐                           ┌───────────────────────┐
        │ YOLOv8 Damage         │                           │ OCR + LLM Extraction  │
        │ Detection Model       │                           │                       │
        └───────────┬───────────┘                           └───────────┬───────────┘
                    │                                                   │
                    ▼                                                   ▼

        ┌───────────────────────┐                           ┌───────────────────────┐
        │ Damaged Vehicle Parts │                           │ Structured Accident   │
        │ Identification        │                           │ Information           │
        └───────────┬───────────┘                           └───────────┬───────────┘
                    │                                                   │
                    └───────────────────┬───────────────────────────────┘
                                        │
                                        ▼

                       ┌─────────────────────────────────┐
                       │ Query Construction &            │
                       │ Domain Normalization            │
                       └───────────────┬─────────────────┘
                                       │
                                       ▼

                       ┌─────────────────────────────────┐
                       │ Hybrid Retrieval Engine         │
                       │ Semantic Search + BM25         │
                       └───────────────┬─────────────────┘
                                       │
                                       ▼

                       ┌─────────────────────────────────┐
                       │ Historical Claims Database      │
                       │ & Vector Database               │
                       └───────────────┬─────────────────┘
                                       │
                                       ▼

                       ┌─────────────────────────────────┐
                       │ Similar Claims Retrieval        │
                       └───────────────┬─────────────────┘
                                       │
                                       ▼

                       ┌─────────────────────────────────┐
                       │ Repair Cost Estimation          │
                       └───────────────┬─────────────────┘
                                       │
                                       ▼

                       ┌─────────────────────────────────┐
                       │ Final Claims Assessment         │
                       └─────────────────────────────────┘
```

---

## Technology Stack

### Backend
- FastAPI
- Python

### Frontend
- React.js

### Database
- PostgreSQL

### Artificial Intelligence
- YOLOv8
- Llama
- OCR

### Information Retrieval
- Vector Database
- Semantic Search
- BM25 Ranking

### Development Tools
- Git
- GitHub
- VS Code

---

## Project Structure

```text
pfe/
│
├── backend/
│   ├── api/
│   ├── services/
│   ├── database/
│   ├── models/
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── public/
│
├── models/
│   ├── yolo/
│   └── llm/
│
├── datasets/
│
├── docs/
│
├── requirements.txt
│
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Yassine-Ben-Salah/pfe.git
cd pfe
```

### Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

---

## Workflow

1. User uploads vehicle images.
2. YOLOv8 detects damaged parts.
3. User uploads the accident report (Constat).
4. OCR and LLM extract relevant information.
5. Damaged parts and extracted data are used to build a search query.
6. Hybrid retrieval searches historical claims.
7. Similar claims are ranked using Semantic Search and BM25.
8. Repair cost is estimated using retrieved cases.
9. Final assessment is presented to the user.

---

## Research Contributions

- Automated vehicle damage detection.
- Accident report information extraction.
- Hybrid retrieval using Semantic Search and BM25.
- Domain-specific normalization for automotive terminology.
- AI-assisted insurance claims assessment workflow.

---

## Author

**Yassine Ben Salah**

National Engineering School of Tunis (ENIT)

Computer Science Engineering Student

Final Year Project (PFE)

2025–2026

---

## Acknowledgments

- COMAR Assurances
- National Engineering School of Tunis (ENIT)
- PFE Supervisor
- Open Source Community
