# Installation Troubleshooting Guide

## Common Installation Issues and Solutions

### Poetry Installation Error: "No file/folder found for package"

**Error Message:**
```
Error: The current project could not be installed: No file/folder found for package dondelocompro-backend
If you do not want to install the current project use --no-root.
```

**Solution:**
This error has been fixed in the latest version. The `pyproject.toml` now includes `package-mode = false` which tells Poetry to only manage dependencies without trying to install the project as a package.

**If you still encounter this error:**
1. Make sure you have the latest version from the repository
2. Try running: `poetry install --no-root`
3. Or manually add `package-mode = false` to your `pyproject.toml` under the `[tool.poetry]` section

### Database Connection Issues

**Error Message:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Solution:**
1. Ensure PostgreSQL is running
2. Check your `.env` file has the correct database credentials
3. Verify the database exists: `createdb dondelocompro` (or your database name)
4. Test connection: `psql -h localhost -U postgres -d dondelocompro`

### Missing Environment File

**Error Message:**
```
FileNotFoundError: [Errno 2] No such file or directory: '.env'
```

**Solution:**
1. Copy the example environment file: `cp .env.example .env`
2. Edit the `.env` file with your actual database credentials
3. Make sure the file is in the `backend/` directory

### Python Version Issues

**Error Message:**
```
The current project's Python requirement (^3.11) is not compatible with some of the required packages
```

**Solution:**
1. Ensure you have Python 3.11 or higher installed
2. Check your Python version: `python --version`
3. If using pyenv: `pyenv install 3.11.0 && pyenv local 3.11.0`
4. Recreate the Poetry environment: `poetry env remove python && poetry install`

### Redis Connection Issues

**Error Message:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Solution:**
1. Install Redis: `sudo apt install redis-server` (Ubuntu) or `brew install redis` (macOS)
2. Start Redis: `sudo systemctl start redis` (Ubuntu) or `brew services start redis` (macOS)
3. Test Redis: `redis-cli ping` (should return "PONG")

### Alembic Migration Issues

**Error Message:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solution:**
1. Check current migration status: `poetry run alembic current`
2. Run migrations: `poetry run alembic upgrade head`
3. If migrations fail, check database permissions and connection

### Port Already in Use

**Error Message:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
1. Check what's using the port: `lsof -i :8000`
2. Kill the process: `kill -9 <PID>`
3. Or use a different port: `poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001`

## Quick Installation Verification

After installation, verify everything is working:

```bash
# Test Poetry environment
poetry run python -c "import fastapi; print('✅ FastAPI imported successfully')"

# Test database connection (requires .env setup)
poetry run python -c "from app.database import engine; print('✅ Database connection successful')"

# Start the server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test health endpoint (in another terminal)
curl http://localhost:8000/health
```

Expected health response:
```json
{
    "status": "healthy",
    "timestamp": "2025-06-16T00:00:00Z",
    "database": "connected",
    "redis": "connected"
}
```

## Getting Help

If you continue to experience issues:

1. **Check the logs:** Look for detailed error messages in the terminal output
2. **Verify prerequisites:** Ensure Python 3.11+, PostgreSQL, and Redis are properly installed
3. **Review configuration:** Double-check your `.env` file settings
4. **Test components individually:** Use the verification commands above to isolate issues
5. **GitHub Issues:** Report persistent issues at https://github.com/JARA99/dlc_manus_repo/issues

