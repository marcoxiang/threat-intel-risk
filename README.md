# Threat Intel Risk Statement Generator

A lightweight web app that ingests cyber threat intelligence from three sources:

- Structured JSON reports
- Uploaded PDF intelligence/advisory files
- Blog/intel URLs

It then produces:

- Aggregated incident metrics
- Executive-friendly risk statements
- A normalized incident table

## Run locally

```bash
python3 -m http.server 4173
```

Then open <http://localhost:4173>.

## Input options

### 1) JSON reports
Provide an optional JSON array where each object includes at minimum:

- `severity` (1-5)
- `confidence` (0-1)

And may include:

- `source`
- `incident`
- `threatActor`
- `industry`

### 2) PDF uploads
Upload one or more PDF reports. The app extracts text client-side (via pdf.js) and infers incident fields from keywords.

### 3) URLs
Enter one URL per line. The app attempts browser-side fetch + extraction from page text and infers incident fields.

> Note: some sites block cross-origin fetches from browsers, so URL ingestion may show warnings for those sources.
