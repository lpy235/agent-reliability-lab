# Configuration

Set `DATABASE_URL` in the environment before starting the service. The value should be a SQLite path for local demos or a Postgres URL in production.

Set `OPENAI_API_KEY` only when you want to use a real OpenAI-compatible model. Without it, the demo uses the deterministic local client.
