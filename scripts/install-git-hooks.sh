#!/bin/bash

echo "Starting script..."

# Find original git executable
echo "Finding Git executable..."
ORIGINAL_GIT=/usr/bin/git
echo "Found Git path: $ORIGINAL_GIT"

# Create bin directory
echo "Creating bin directory..."
mkdir -p ~/bin

# Add ~/bin to PATH
echo "Checking PATH configuration..."
if ! grep -q "export PATH=\"$HOME/bin:$PATH\"" ~/.bashrc; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
fi
export PATH="$HOME/bin:$PATH"

# Create Git wrapper script
echo "Creating Git wrapper script..."
cat > ~/bin/git << EOF
#!/usr/bin/env bash

# Full path to git executable
GIT_EXEC=/usr/bin/git

# Check if wrapper is already running
if [ -n "\$GIT_WRAPPER_RUNNING" ]; then
    exec \$GIT_EXEC "\$@"
fi
export GIT_WRAPPER_RUNNING=1

if [ "\$1" = "add" ]; then
    echo "Detected git add command..."
    shift
    for arg in "\$@"; do
        echo "Processing file: \$arg"
        if [ -f "\$arg" ] && [[ "\$arg" == *.dvc ]]; then
            dvc_path=\$(grep "path:" "\$arg" | cut -d: -f2 | tr -d " ")
            if [ ! -z "\$dvc_path" ]; then
                echo "Updating DVC tracking... (path: \$dvc_path)"
                dvc add "\$dvc_path"
            fi
        fi
        echo "Executing Git add: \$arg"
        \$GIT_EXEC add "\$arg"
    done
else
    \$GIT_EXEC "\$@"
fi
EOF

echo "Setting execute permission for Git wrapper script..."
chmod +x ~/bin/git

# Create pre-push hook
echo "Creating pre-push hook..."
mkdir -p ~/.git-hooks
cat > ~/.git-hooks/pre-push << 'EOF'
#!/bin/bash

# Find Git repository root directory (.git directory location)
GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"
echo "Git project root: $GIT_ROOT"

# Find .dvc directories only within Git project
dvc_dirs=$(find . -type d -name ".dvc" ! -path "*/\.*/*")

if [ -n "$dvc_dirs" ]; then
    while IFS= read -r dvc_dir; do
        # Parent directory of .dvc is the DVC repository
        dvc_repo=$(dirname "$dvc_dir")
        echo "Found DVC repository: $dvc_repo"
        cd "$GIT_ROOT/$dvc_repo"
        echo "Running DVC push before Git push..."
        dvc push
        cd "$GIT_ROOT"  # Return to Git root for next search
    done <<< "$dvc_dirs"
else
    echo "No DVC repository found in Git repository."
fi

exit 0
EOF

chmod +x ~/.git-hooks/pre-push

# Configure Git to use hooks directory
echo "Setting Git hooks directory..."
/usr/bin/git config --global core.hooksPath ~/.git-hooks

echo "Installation complete!"
echo "Please restart your terminal or run:"
echo "source ~/.bashrc"
echo ""
echo "Now you can use Git commands as usual:"
echo "1. dvc add data (only once initially)"
echo "2. git add data.dvc (automatically runs dvc add)"
echo "3. git commit -m 'message'"
echo "4. git push (automatically runs dvc push)"

echo ""
echo "When creating a new Git repository, run this script again after git init."
