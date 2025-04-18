FROM python:3.11-slim

# --- harden the container ---
RUN useradd -m sandbox && \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

USER sandbox
WORKDIR /workspace              # all execution happens here

# non‑interactive backend so plots render headless
ENV MPLBACKEND=Agg
ENV PYTHONUNBUFFERED=1

# install *only* safe libs
RUN pip install --no-cache-dir pandas numpy matplotlib seaborn

# copy the tiny entry script
COPY sandbox_entry.py /workspace/

ENTRYPOINT ["python", "sandbox_entry.py"]
