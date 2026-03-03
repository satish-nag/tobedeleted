## Alert Summarizer

### Run locally
```bash
uv venv
source .venv/bin/activate
uv sync
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"   # your deployment name
export ALERT_DETAILS_BASE_URL="http://fba-cloud.abc.com"

uv run uvicorn app.main:app --reload --port 8000