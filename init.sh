#!/bin/bash
set -e
# This script is idempotent — safe to run repeatedly.
# Each step either skips if already done or overwrites cleanly.

# Initial setup: install packages
npm install
uv sync --all-extras

# Detect worktree: compare current directory to main repo
WORKTREE_NAME=$(basename "$PWD")
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')

if [ "$PWD" = "$MAIN_REPO" ]; then
    # Main repo: slot 0, default ports
    echo "📁 Main repo detected"
    SLOT=0
    PROJECT_ID="codeleash"

    # Copy .env.example to .env if .env doesn't exist yet
    if [ ! -f .env ] && [ -f .env.example ]; then
        cp .env.example .env
        echo "   ✅ Created .env from .env.example"
    fi
else
    # Worktree: calculate slot from name
    echo "🌳 Worktree '$WORKTREE_NAME' detected"

    # Sanitize name for project ID: lowercase, replace non-alphanumeric with hyphens
    SANITIZED_NAME=$(echo "$WORKTREE_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
    PROJECT_ID="codeleash-$SANITIZED_NAME"

    # Calculate slot: numeric 1-99 uses number directly, otherwise hash
    if [[ "$WORKTREE_NAME" =~ ^[0-9]+$ ]] && [ "$WORKTREE_NAME" -ge 1 ] && [ "$WORKTREE_NAME" -le 99 ]; then
        SLOT=$WORKTREE_NAME
    else
        SLOT=$(echo -n "$WORKTREE_NAME" | cksum | awk '{print ($1 % 99) + 1}')
    fi
fi

# Calculate ports from slot
PORT=$((8000 + SLOT))
VITE_PORT=$((5173 + SLOT))
API_PORT=$((54321 + SLOT * 10))
DB_PORT=$((54322 + SLOT * 10))
SHADOW_PORT=$((54320 + SLOT * 10))
POOLER_PORT=$((54329 + SLOT * 10))
STUDIO_PORT=$((54323 + SLOT * 10))
INBUCKET_PORT=$((54324 + SLOT * 10))
ANALYTICS_PORT=$((54327 + SLOT * 10))

echo "   Slot: $SLOT, Project: $PROJECT_ID"

# Setup .env for worktrees (copy from main repo + add port overrides)
if [ "$SLOT" -gt 0 ]; then
    echo "📋 Setting up .env for worktree '$WORKTREE_NAME'..."

    # Copy from main repo if we don't have one
    if [ ! -f .env ] && [ -f "$MAIN_REPO/.env" ]; then
        cp "$MAIN_REPO/.env" .env
    fi

    # Remove any existing port settings and re-add
    [ -f .env ] && sed -i '' '/^PORT=/d; /^VITE_SERVER_PORT=/d; /^SUPABASE_URL=/d; /^DATABASE_URL=/d; /^# Worktree .* port configuration/d' .env 2>/dev/null || true

    # Add worktree-specific settings
    cat >> .env << EOF

# Worktree '$WORKTREE_NAME' (slot $SLOT) port configuration
PORT=$PORT
VITE_SERVER_PORT=$VITE_PORT
SUPABASE_URL=http://127.0.0.1:$API_PORT
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:$DB_PORT/postgres
EOF
    echo "   ✅ Ports configured: FastAPI=$PORT, Vite=$VITE_PORT, Supabase=$API_PORT"
fi

# Generate supabase config (always regenerate - it's gitignored)
echo "🗄️  Generating Supabase config..."
TEMP_CONFIG=$(mktemp)

if [ "$SLOT" -gt 0 ]; then
    # Worktree: full config from supabase init, then patch ports
    TEMP_DIR=$(mktemp -d)
    (cd "$TEMP_DIR" && supabase init --force) > /dev/null 2>&1
    cp "$TEMP_DIR/supabase/config.toml" "$TEMP_CONFIG"
    rm -rf "$TEMP_DIR"

    sed -i '' "s/^project_id = .*/project_id = \"$PROJECT_ID\"/" "$TEMP_CONFIG"
    sed -i '' "s/^port = 54321$/port = $API_PORT/" "$TEMP_CONFIG"
    sed -i '' "s/^port = 54322$/port = $DB_PORT/" "$TEMP_CONFIG"
    sed -i '' "s/^shadow_port = 54320$/shadow_port = $SHADOW_PORT/" "$TEMP_CONFIG"
    sed -i '' "s/^port = 54329$/port = $POOLER_PORT/" "$TEMP_CONFIG"
    sed -i '' "s/^port = 54323$/port = $STUDIO_PORT/" "$TEMP_CONFIG"
    sed -i '' "s/^port = 54324$/port = $INBUCKET_PORT/" "$TEMP_CONFIG"
    sed -i '' "s/^port = 54327$/port = $ANALYTICS_PORT/" "$TEMP_CONFIG"
fi

mv "$TEMP_CONFIG" supabase/config.toml
echo "   ✅ supabase/config.toml generated (slot $SLOT)"

# Start Supabase if not running (check if API port is listening)
if ! nc -z 127.0.0.1 $API_PORT 2>/dev/null; then
    echo "🚀 Starting Supabase on port $API_PORT..."
    # Stop any existing instance for this project first
    supabase stop --project-id "$PROJECT_ID" 2>/dev/null || true
    supabase start
else
    echo "✅ Supabase already running on port $API_PORT"
fi

# Configure .env with Supabase credentials
echo "🔑 Configuring Supabase credentials in .env..."
eval "$(supabase status -o env 2>/dev/null | grep -v '^Stopped')"
sed -i '' "s|^SUPABASE_URL=.*|SUPABASE_URL=$API_URL|" .env
sed -i '' "s|^SUPABASE_ANON_KEY=.*|SUPABASE_ANON_KEY=$ANON_KEY|" .env
sed -i '' "s|^SUPABASE_SERVICE_KEY=.*|SUPABASE_SERVICE_KEY=$SERVICE_ROLE_KEY|" .env
sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=$DB_URL|" .env
sed -i '' "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" .env
echo "   ✅ Supabase credentials configured"

# Install git pre-commit hook
HOOKS_DIR="$(git rev-parse --git-common-dir)/hooks"
HOOK_PATH="$HOOKS_DIR/pre-commit"

DESIRED_HOOK='#!/bin/bash
# Pre-commit hook installed by init.sh
# Runs pre-commit checks and full test suite before allowing commits
set -e
npm run test:all'

if [ -f "$HOOK_PATH" ] && [ "$(cat "$HOOK_PATH")" = "$DESIRED_HOOK" ]; then
    echo "   ✅ Git pre-commit hook already installed"
else
    if [ -f "$HOOK_PATH" ]; then
        BACKUP_PATH="${HOOK_PATH}.backup.$(date +%Y%m%d%H%M%S)"
        mv "$HOOK_PATH" "$BACKUP_PATH"
        echo "   ⚠️  Existing pre-commit hook backed up to: $BACKUP_PATH"
    fi

    echo "$DESIRED_HOOK" > "$HOOK_PATH"
    chmod +x "$HOOK_PATH"
    echo "   ✅ Git pre-commit hook installed (runs test:all)"
fi

echo ""
echo "🎉 Setup complete! Run: npm run dev"
echo "   Access at: http://localhost:$PORT"
