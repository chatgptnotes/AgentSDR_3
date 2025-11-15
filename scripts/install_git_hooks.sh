#!/bin/bash
# Install Git Hooks for Auto Version Increment

HOOKS_DIR=".git/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create pre-push hook to increment version
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# Auto-increment version before push

echo "Incrementing version..."
./venv/bin/python scripts/increment_version.py

# Add version.json to the commit if it changed
if git diff --quiet version.json; then
    echo "Version unchanged"
else
    echo "Version updated, adding to git..."
    git add version.json
    # Amend the last commit with the version update
    git commit --amend --no-edit --no-verify
fi
EOF

chmod +x "$HOOKS_DIR/pre-push"

echo "✅ Git hooks installed successfully!"
echo "Version will auto-increment on git push"
