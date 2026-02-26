#!/bin/bash
# Cleanup orphaned e2e test Supabase instances
# Use this if e2e tests are interrupted and leave behind containers/directories
#
# E2E tests create Supabase instances with project IDs like: e2e-{timestamp}-{8char_random}
# This creates Docker resources named: supabase_{service}_e2e-{timestamp}-{random}
# Interrupted tests may also leave behind:
#   - Random-named containers from supabase images (e.g. happy_lumiere)
#   - Dangling supabase volumes from incomplete cleanup

set -e

echo "🧹 Cleaning up orphaned E2E Supabase instances..."

# Stop and remove e2e-named Supabase containers
echo ""
echo "🐳 Stopping orphaned E2E containers..."
CONTAINERS=$(docker ps -a --format "{{.Names}}" | grep "_e2e-" 2>/dev/null || true)

if [ -z "$CONTAINERS" ]; then
    echo "   No orphaned e2e containers found"
else
    CONTAINER_COUNT=$(echo "$CONTAINERS" | wc -l | tr -d ' ')
    echo "   Found $CONTAINER_COUNT orphaned e2e containers:"
    echo "$CONTAINERS" | sed 's/^/   - /'
    echo "$CONTAINERS" | xargs docker rm -f
    echo "   ✅ E2E containers removed"
fi

# Remove random-named exited containers from supabase images (orphaned from failed cleanup)
echo ""
echo "🐳 Checking for orphaned random-named Supabase containers..."
# Find exited containers using supabase images that aren't part of a named project.
# Uses image filter to find supabase containers, then excludes known dev instances.
RANDOM_CONTAINERS=""
while IFS=$'\t' read -r name image; do
    # Skip containers that belong to a named supabase project (dev or e2e)
    if echo "$name" | grep -qE "^supabase_"; then
        continue
    fi
    # This is a random-named container using a supabase image
    if [ -z "$RANDOM_CONTAINERS" ]; then
        RANDOM_CONTAINERS="$name"
    else
        RANDOM_CONTAINERS="$RANDOM_CONTAINERS
$name"
    fi
done < <(docker ps -a --filter "status=exited" --format "{{.Names}}\t{{.Image}}" \
    | grep "public.ecr.aws/supabase/" 2>/dev/null || true)

if [ -z "$RANDOM_CONTAINERS" ]; then
    echo "   No orphaned random-named containers found"
else
    RANDOM_COUNT=$(echo "$RANDOM_CONTAINERS" | wc -l | tr -d ' ')
    echo "   Found $RANDOM_COUNT orphaned random-named Supabase containers:"
    echo "$RANDOM_CONTAINERS" | sed 's/^/   - /'
    echo "$RANDOM_CONTAINERS" | xargs docker rm
    echo "   ✅ Random-named containers removed"
fi

# Remove orphaned e2e Docker volumes
echo ""
echo "📦 Removing orphaned E2E Docker volumes..."
E2E_VOLUMES=$(docker volume ls -q | grep "_e2e-" 2>/dev/null || true)

if [ -z "$E2E_VOLUMES" ]; then
    echo "   No orphaned e2e volumes found"
else
    VOLUME_COUNT=$(echo "$E2E_VOLUMES" | wc -l | tr -d ' ')
    echo "   Found $VOLUME_COUNT orphaned e2e volumes"
    echo "$E2E_VOLUMES" | xargs docker volume rm 2>/dev/null || true
    echo "   ✅ E2E volumes removed"
fi

# Remove dangling supabase volumes (not referenced by any container)
echo ""
echo "📦 Checking for dangling Supabase volumes..."
DANGLING_VOLUMES=$(docker volume ls -q --filter "dangling=true" | grep "^supabase_" 2>/dev/null || true)

if [ -z "$DANGLING_VOLUMES" ]; then
    echo "   No dangling Supabase volumes found"
else
    DANGLING_COUNT=$(echo "$DANGLING_VOLUMES" | wc -l | tr -d ' ')
    echo "   Found $DANGLING_COUNT dangling Supabase volumes:"
    echo "$DANGLING_VOLUMES" | sed 's/^/   - /'
    echo "$DANGLING_VOLUMES" | xargs docker volume rm 2>/dev/null || true
    echo "   ✅ Dangling volumes removed"
fi

# Remove e2e Docker networks (not a blanket prune - only targets e2e networks)
echo ""
echo "🌐 Removing orphaned E2E networks..."
NETWORKS=$(docker network ls --format "{{.Name}}" | grep "_e2e-" 2>/dev/null || true)

if [ -z "$NETWORKS" ]; then
    echo "   No orphaned e2e networks found"
else
    echo "   Found orphaned e2e networks:"
    echo "$NETWORKS" | sed 's/^/   - /'
    echo "$NETWORKS" | xargs docker network rm 2>/dev/null || true
    echo "   ✅ E2E networks removed"
fi

# Remove temporary directories
echo ""
echo "🗑️  Removing temporary directories..."
TEMP_DIR="/tmp/supabase-e2e"

if [ ! -d "$TEMP_DIR" ]; then
    echo "   No temporary directories found"
elif [ -z "$(ls -A "$TEMP_DIR" 2>/dev/null)" ]; then
    echo "   Temporary directory is empty"
else
    echo "   Found temporary directories:"
    ls -1 "$TEMP_DIR" | sed 's/^/   - /'
    rm -rf "${TEMP_DIR:?}"/*
    echo "   ✅ Directories removed"
fi

# Show disk space reclaimed
echo ""
echo "💾 Docker disk usage after cleanup:"
docker system df

echo ""
echo "✨ Cleanup complete!"
