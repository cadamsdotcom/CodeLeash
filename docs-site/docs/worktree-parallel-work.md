---
title: 'Worktree Parallel Work'
sidebar_position: 8
---

Git worktrees let you check out multiple branches of the same repo simultaneously, each in its own directory. CodeLeash's [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh) script automatically configures isolated ports and Supabase instances for each worktree, so multiple branches can run side by side without conflicts.

## Worktree Detection

The [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh) script compares the current directory to the main repo and calculates a slot number:

```bash
WORKTREE_NAME=$(basename "$PWD")
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')

if [ "$PWD" = "$MAIN_REPO" ]; then
    SLOT=0
    PROJECT_ID="codeleash"
else
    # Calculate slot from worktree name
    if [[ "$WORKTREE_NAME" =~ ^[0-9]+$ ]] && [ "$WORKTREE_NAME" -ge 1 ] && [ "$WORKTREE_NAME" -le 99 ]; then
        SLOT=$WORKTREE_NAME
    else
        SLOT=$(echo -n "$WORKTREE_NAME" | cksum | awk '{print ($1 % 99) + 1}')
    fi
fi
```

> [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh)

- The main repo always gets slot 0 (default ports)
- Numeric worktree names (1-99) use their number as the slot directly
- Other names are hashed with `cksum` to a slot in 1-99

## Port Formula

Each slot gets a deterministic set of ports, calculated with simple arithmetic:

```bash
PORT=$((8000 + SLOT))
VITE_PORT=$((5173 + SLOT))
API_PORT=$((54321 + SLOT * 10))
DB_PORT=$((54322 + SLOT * 10))
SHADOW_PORT=$((54320 + SLOT * 10))
POOLER_PORT=$((54329 + SLOT * 10))
STUDIO_PORT=$((54323 + SLOT * 10))
INBUCKET_PORT=$((54324 + SLOT * 10))
```

> [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh)

| Service      | Formula         | Slot 0 (main) | Slot 1 | Slot 5 |
| ------------ | --------------- | ------------- | ------ | ------ |
| FastAPI      | 8000 + slot     | 8000          | 8001   | 8005   |
| Vite         | 5173 + slot     | 5173          | 5174   | 5178   |
| Supabase API | 54321 + slot×10 | 54321         | 54331  | 54371  |
| Supabase DB  | 54322 + slot×10 | 54322         | 54332  | 54372  |
| DB Shadow    | 54320 + slot×10 | 54320         | 54330  | 54370  |
| DB Pooler    | 54329 + slot×10 | 54329         | 54339  | 54379  |
| Studio       | 54323 + slot×10 | 54323         | 54333  | 54373  |
| Inbucket     | 54324 + slot×10 | 54324         | 54334  | 54374  |
| Analytics    | 54327 + slot×10 | 54327         | 54337  | 54377  |

## Supabase Config Isolation

For worktrees (slot > 0), `init.sh` generates a fresh config and patches the ports with `sed`:

```bash
# Generate fresh config.toml
TEMP_DIR=$(mktemp -d)
(cd "$TEMP_DIR" && supabase init --force) > /dev/null 2>&1
cp "$TEMP_DIR/supabase/config.toml" "$TEMP_CONFIG"

# Patch port numbers
sed -i '' "s/^project_id = .*/project_id = \"$PROJECT_ID\"/" "$TEMP_CONFIG"
sed -i '' "s/^port = 54321$/port = $API_PORT/" "$TEMP_CONFIG"
sed -i '' "s/^port = 54322$/port = $DB_PORT/" "$TEMP_CONFIG"
sed -i '' "s/^shadow_port = 54320$/shadow_port = $SHADOW_PORT/" "$TEMP_CONFIG"
sed -i '' "s/^port = 54329$/port = $POOLER_PORT/" "$TEMP_CONFIG"
sed -i '' "s/^port = 54323$/port = $STUDIO_PORT/" "$TEMP_CONFIG"
```

> [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh)

This ensures each worktree's Supabase instance has its own Docker containers and PostgreSQL data.

## Environment File

Worktrees get their own `.env` with port overrides:

```bash
# Worktree 'feature-xyz' (slot 42) port configuration
PORT=8042
VITE_SERVER_PORT=5215
SUPABASE_URL=http://127.0.0.1:54741
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54742/postgres
```

The `.env` file starts as a copy from the main repo, with port-related variables replaced.

## Typical Workflow

```bash
# Create a worktree for a feature branch
git worktree add ../my-feature feature-branch

# Initialize the worktree (installs deps, configures ports, starts Supabase)
cd ../my-feature
./init.sh

# Develop normally --- runs on its own ports
npm run dev    # FastAPI on 8042, Vite on 5215

# Meanwhile, main repo keeps running on default ports
cd ../CodeLeash
npm run dev    # FastAPI on 8000, Vite on 5173
```

Both instances run simultaneously with no port conflicts.

## Limitations

- **Slot collisions**: Two worktree names that hash to the same slot will conflict. Use numeric names (1-99) for deterministic assignment.
- **Docker resources**: Each Supabase instance runs its own set of Docker containers. Running many worktrees simultaneously requires significant memory.
- **First startup**: The first `init.sh` in a worktree may need to pull Docker images, which can be slow.
- **macOS sed**: The port patching uses `sed -i ''` (BSD sed syntax). On Linux, this would need `sed -i` without the empty string argument.
