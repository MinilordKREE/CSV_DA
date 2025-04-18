FROM python:3.11-slim

# Add a non-root user for running code in the sandbox
RUN useradd -m sandbox && \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

USER sandbox
WORKDIR /workspace      # Set the working directory for the sandboxed environment

# Configure a headless backend for rendering plots
ENV MPLBACKEND=Agg
ENV PYTHONUNBUFFERED=1

# Install the necessary Python dependencies
RUN pip install --no-cache-dir pandas numpy matplotlib seaborn

# Copy the sandbox entry script into the container
COPY sandbox_entry.py /workspace/

# Run the entry script when the container starts
ENTRYPOINT ["python", "sandbox_entry.py"]
