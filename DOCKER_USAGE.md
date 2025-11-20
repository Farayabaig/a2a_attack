# Docker Usage Guide

## Quick Start

### 1. Build the Docker Image
```bash
docker build -t a2a-security-poc .
```

### 2. Run the Full Demonstration
```bash
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/.env:/app/.env \
  a2a-security-poc
```

## What the Command Does

- `docker run` - Runs a container from the image
- `--rm` - Automatically removes container when it exits
- `-v $(pwd)/reports:/app/reports` - Saves reports to your local `reports/` folder
- `-v $(pwd)/.env:/app/.env` - Uses your local `.env` file for configuration
- `a2a-security-poc` - The Docker image name

## Output

The output will now show:
- ✅ Configuration check (API keys, provider, model)
- ✅ Clear status messages
- ✅ Step-by-step progress
- ✅ Success/error indicators
- ✅ Final report location

## Common Issues

1. **"Image not found"** - Run `docker build -t a2a-security-poc .` first
2. **"API key not configured"** - Check your `.env` file
3. **"Permission denied"** - Make sure `.env` file is readable
