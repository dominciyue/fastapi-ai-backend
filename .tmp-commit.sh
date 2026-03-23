#!/usr/bin/env bash
set -euo pipefail

git add .
git commit -m "$(cat <<'EOF'
Build initial Dify-compatible FastAPI RAG service.

Establish a runnable AI backend baseline with document upload, async indexing, retrieval, streaming chat, Docker deployment, and week-one project docs so the roadmap can keep moving without re-scoping.
EOF
)"
git status --short
