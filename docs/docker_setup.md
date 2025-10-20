# Docker Container Setup for DataPrism

This document provides the Docker configuration needed for development.

## Required Ports

### Inbound (Development Servers)
| Port | Service | Purpose |
|------|---------|---------|
| 8000 | FastAPI Backend | API server |
| 3000 | Next.js Frontend | Primary frontend dev server |
| 3001 | Next.js Frontend | Backup/alternative frontend |
| 8888 | Jupyter Notebook | Evaluation analysis (optional) |

### Outbound (External Services)
| Port | Service | Purpose |
|------|---------|---------|
| 443 | HTTPS | OpenAI, Pinecone, Supabase APIs |
| 5432 | PostgreSQL | Supabase database connection |

*Note: Outbound ports are typically allowed by default in Docker*

---

## Docker Run Command

### Full Development Setup
```bash
docker run -it \
  -p 8000:8000 \
  -p 3000:3000 \
  -p 3001:3001 \
  -p 8888:8888 \
  -v $(pwd):/home/developer/source/dataprism \
  -w /home/developer/source/dataprism \
  --env-file .env \
  your-image-name
```

### Minimal Setup (Backend + Frontend only)
```bash
docker run -it \
  -p 8000:8000 \
  -p 3000:3000 \
  -v $(pwd):/home/developer/source/dataprism \
  -w /home/developer/source/dataprism \
  --env-file .env \
  your-image-name
```

---

## Docker Compose (Alternative)

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  dataprism-dev:
    image: your-image-name
    container_name: dataprism-dev
    ports:
      - "8000:8000"  # FastAPI backend
      - "3000:3000"  # Next.js frontend
      - "3001:3001"  # Next.js backup
      - "8888:8888"  # Jupyter notebook
    volumes:
      - .:/home/developer/source/dataprism
    working_dir: /home/developer/source/dataprism
    env_file:
      - .env
    stdin_open: true
    tty: true
```

**Usage:**
```bash
docker-compose up -d
docker-compose exec dataprism-dev bash
```

---

## Environment Variables

The container will load environment variables from `.env` file using `--env-file .env` flag.

**Important:** Make sure `.env` file exists in the project root before running the container.

---

## Verifying Port Access

After starting the container, verify ports are accessible:

```bash
# From inside container
# Backend (FastAPI)
curl http://localhost:8000/health

# Frontend (Next.js)
curl http://localhost:3000

# Jupyter
curl http://localhost:8888
```

**From host machine:**
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

---

## Troubleshooting

### Port Already in Use
If you get "port already allocated" error:

```bash
# Find what's using the port
lsof -i :8000
# or
netstat -tlnp | grep 8000

# Kill the process or use different port
docker run -p 8001:8000 ...
```

### Can't Access Services from Host
- Check firewall rules
- Verify port mapping: `docker ps` shows port mappings
- Ensure service is listening on `0.0.0.0` not `127.0.0.1`

### Environment Variables Not Loading
```bash
# Verify .env file exists
ls -la .env

# Check if variables are loaded in container
docker exec container-name env | grep OPENAI
```

---

## Next Steps After Container Rebuild

1. Test all service connections:
   ```bash
   python scripts/test_connections.py
   ```

2. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Start development servers and proceed with Week 1 Days 3-4 (data loading)
