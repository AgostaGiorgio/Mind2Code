#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Check if the new version was passed as an argument
if [ -z "$1" ]; then
  echo "Error: You must provide the new version as an argument."
  echo "Usage: $0 <new_version>"
  exit 1
fi

NEW_VERSION=$1
echo "Updating files to version $NEW_VERSION..."

# 1. Update backend/pyproject.toml in a cross-platform way (Mac + Linux)
if [ -f "backend/pyproject.toml" ]; then
  sed "s/^version = .*/version = \"$NEW_VERSION\"/" backend/pyproject.toml > backend/pyproject.toml.tmp
  mv backend/pyproject.toml.tmp backend/pyproject.toml
  echo "✅ backend/pyproject.toml updated"
else
  echo "⚠️ backend/pyproject.toml not found"
fi

# 2. Update frontend/package.json safely using jq
if [ -f "frontend/package.json" ]; then
  jq --arg v "$NEW_VERSION" '.version = $v' frontend/package.json > frontend/package.json.tmp
  mv frontend/package.json.tmp frontend/package.json
  echo "✅ frontend/package.json updated"
else
  echo "⚠️ frontend/package.json not found"
fi