#!/bin/bash
# Extract Supabase environment variables from local instance
# Usage: source scripts/extract_supabase_env.sh

set -e

# Check if Supabase is running
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install Supabase CLI first."
    exit 1
fi

# Get Supabase status
echo "🔍 Extracting Supabase environment variables..."
STATUS_OUTPUT=$(supabase status -o env)

if [ -z "$STATUS_OUTPUT" ]; then
    echo "❌ Failed to get Supabase status. Is Supabase running?"
    exit 1
fi

# Extract and export environment variables
export SUPABASE_URL=$(echo "$STATUS_OUTPUT" | grep -E '^API_URL=' | cut -d'=' -f2- | tr -d '"')
export SUPABASE_ANON_KEY=$(echo "$STATUS_OUTPUT" | grep -E '^ANON_KEY=' | cut -d'=' -f2- | tr -d '"')
export SUPABASE_SERVICE_KEY=$(echo "$STATUS_OUTPUT" | grep -E '^SERVICE_ROLE_KEY=' | cut -d'=' -f2- | tr -d '"')
export DATABASE_URL=$(echo "$STATUS_OUTPUT" | grep -E '^DB_URL=' | cut -d'=' -f2- | tr -d '"')
export JWT_SECRET_KEY=$(echo "$STATUS_OUTPUT" | grep -E '^JWT_SECRET=' | cut -d'=' -f2- | tr -d '"')

# Validate that all required variables were extracted
required_vars=("SUPABASE_URL" "SUPABASE_ANON_KEY" "SUPABASE_SERVICE_KEY" "DATABASE_URL" "JWT_SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Failed to extract required environment variables: ${missing_vars[*]}"
    echo "Raw Supabase status output:"
    echo "$STATUS_OUTPUT"
    exit 1
fi

# Success - log the extracted configuration
echo "✅ Successfully extracted Supabase environment variables:"
echo "   API URL: $SUPABASE_URL"
echo "   DB URL: $DATABASE_URL"
echo "   All authentication keys extracted successfully"