# GearCrew: AI Hiking Gear Researcher

This project uses a team of AI agents (CrewAI) to extract, verify, and store hiking gear information into a Cognee graph database.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Copy `.env.example` to `.env` and fill in your API keys:
    ```bash
    cp .env.example .env
    ```
    *   `GOOGLE_API_KEY`: For Gemini models.
    *   `SERPER_API_KEY`: For Google Search (via Serper.dev).
    *   `COGWIT_API_KEY`: For Cognee Cloud access.

3.  **Ontology:**
    Place your custom ontology file (e.g., `gear_ontology.owl`) in the root directory.
    *   If your file has a different name, update `DEFAULT_ONTOLOGY_FILE` in `main.py`.

## Usage

Run the main script:

```bash
python main.py
```

Paste your gear review summary or video transcript when prompted.

## Architecture

*   **Framework:** CrewAI
*   **LLMs:** Gemini 1.5 Pro (Extraction/Verification), Gemini 1.5 Flash (Knowledge/Admin)
*   **Database:** Cognee Cloud (Graph DB)
*   **Agents:**
    1.  **Extractor:** Parses raw text for gear specs.
    2.  **Verifier:** Searches the web to validate and correct specs.
    3.  **Knowledge Miner:** Extracts usage tips and practical knowledge.
    4.  **DB Admin:** Inserts data into Cognee and triggers cognification.
