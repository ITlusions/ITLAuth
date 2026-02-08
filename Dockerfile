# Test Dockerfile for ITLC CLI
# This allows testing the installation and CLI without affecting your system

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .

# Set environment variables with defaults
ENV KEYCLOAK_URL=https://sts.itlusions.com
ENV KEYCLOAK_REALM=itlusions
ENV CONTROLPLANE_URL=http://localhost:8000

# Create a test script
RUN echo '#!/bin/bash\n\
echo "======================================"\n\
echo "ITLC CLI - Installation Test"\n\
echo "======================================"\n\
echo ""\n\
echo "Testing itlc installation..."\n\
itlc --version\n\
echo ""\n\
echo "======================================"\n\
echo "Available Commands:"\n\
echo "======================================"\n\
itlc --help\n\
echo ""\n\
echo "======================================"\n\
echo "Configuration:"\n\
echo "======================================"\n\
itlc config || true\n\
echo ""\n\
echo "======================================"\n\
echo "Environment Variables:"\n\
echo "======================================"\n\
echo "KEYCLOAK_URL=$KEYCLOAK_URL"\n\
echo "KEYCLOAK_REALM=$KEYCLOAK_REALM"\n\
echo "CONTROLPLANE_URL=$CONTROLPLANE_URL"\n\
echo ""\n\
echo "======================================"\n\
echo "Installation successful!"\n\
echo "You can now test the CLI commands."\n\
echo "======================================"\n\
echo ""\n\
echo "Examples:"\n\
echo "  itlc --help"\n\
echo "  itlc config"\n\
echo "  itlc realm list"\n\
echo "  itlc get-token --help"\n\
echo ""\n\
' > /usr/local/bin/test-itlc && chmod +x /usr/local/bin/test-itlc

# Run tests on build
RUN test-itlc

# Default command opens interactive shell
CMD ["/bin/bash"]
