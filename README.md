# AI Data Analyst

AI Data Analyst is a no-code data analysis app for querying CSV files or databases in plain English. It uploads CSVs to Supabase, inspects the dataset schema, chooses whether the request needs SQL or visualization, and returns tables, chart images, or short natural-language summaries.

## What It Does

- Upload a CSV file or provide a database connection string.
- Ask questions in natural language.
- Generate SQL for tabular answers.
- Generate Python chart code in an E2B sandbox for visual analysis.
- Store generated chart images in Supabase and return public URLs.

## Architecture

```text
Browser UI
  -> FastAPI routes
     -> /upload stores CSV files in Supabase
     -> /query invokes the LangGraph analyst agent

LangGraph analyst agent
  -> routes CSV vs database input
  -> extracts schema and sample metadata
  -> classifies request as SQL or visualization
  -> generates and checks SQL, or generates Python chart code
  -> executes SQL locally/DuckDB or code in E2B
  -> returns rows, chart URLs, and summaries

External services
  -> OpenAI for reasoning and code/query generation
  -> Supabase for CSV and image storage
  -> E2B for sandboxed visualization execution
```

## Local Setup

Requires Python 3.11+.

```bash
git clone https://github.com/pushpitkamboj/AIDataAnalyst
cd AIDataAnalyst
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

```env
OPENAI_API_KEY=
E2B_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
CSV_BUCKET_NAME=data_csv
IMAGE_BUCKET_NAME=data_image
```

Run the app:

```bash
PYTHONPATH=src uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Docker

```bash
docker compose up --build
```

## License

MIT
