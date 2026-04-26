# ITLC Docker Testing Guide

This guide shows how to test the ITLC CLI in an isolated Docker container without affecting your system.

## Quick Start

### Build and Run

```bash
# Build the Docker image
docker build -t itlc-test .

# Run a command
docker run --rm itlc-test itlc --version
docker run --rm itlc-test itlc --help
docker run --rm itlc-test itlc config

# Interactive shell
docker run --rm -it itlc-test /bin/bash
```

### Using Docker Compose

```bash
# Run a single command
docker-compose run --rm itlc-test itlc --help

# Start interactive shell
docker-compose run --rm itlc-test

# Inside the container:
itlc --version
itlc config
itlc cluster list
itlc --help
```

## Test Commands

```bash
# Version check
docker run --rm itlc-test itlc --version

# Configuration
docker run --rm itlc-test itlc config

# List clusters
docker run --rm itlc-test itlc cluster list

# Check cached tokens
docker run --rm itlc-test itlc cache-list

# Get help for any command
docker run --rm itlc-test itlc get-token --help
```

## Environment Variables

Override environment variables:

```bash
docker run --rm \
  -e KEYCLOAK_URL=https://your-keycloak.com \
  -e KEYCLOAK_REALM=your-realm \
  itlc-test itlc config
```

## Development Testing

```bash
# Mount source code for live testing
docker run --rm -it \
  -v $(pwd)/src:/app/src:ro \
  itlc-test /bin/bash

# Inside container, changes to source are reflected immediately
```

## Cleanup

```bash
# Remove container
docker-compose down

# Remove volumes
docker-compose down -v

# Remove image
docker rmi itlc-test
```

## Available Commands in Container

All `itlc` commands are available:
- `login` - Interactive login (requires browser, may not work in container)
- `logout` - Logout
- `whoami` - Show current user
- `get-token` - Get service account token
- `config` - Show configuration
- `realm` - Manage realms
- `cluster` - Manage clusters
- `cache-list` - List cached tokens
- `clear-cache` - Clear token cache
- `inspect` - Inspect JWT token
- `introspect` - Validate token with Keycloak

## Notes

- Interactive browser login may not work in containers (use service account tokens instead)
- Token cache is persisted in a Docker volume (see docker-compose.yml)
- The container runs as root by default
- Source code changes require rebuilding the image
