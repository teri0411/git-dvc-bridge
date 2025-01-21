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
cat > ~/bin/git << 'EOF'
#!/usr/bin/env bash

# Full path to git executable
GIT_EXEC=/usr/bin/git

# Check if wrapper is already running
if [ -n "$GIT_WRAPPER_RUNNING" ]; then
    exec $GIT_EXEC "$@"
fi
export GIT_WRAPPER_RUNNING=1

check_dvc_file() {
    local path="$1"
    local current_path="$path"
    local git_root=$($GIT_EXEC rev-parse --show-toplevel)
    
    # 현재 경로에 .dvc 파일이 있는지 확인
    if [ -f "${path}.dvc" ]; then
        echo "current"
        return 0
    fi
    
    # 디렉토리인 경우 해당 디렉토리 내의 .dvc 파일 확인
    if [ -d "$path" ]; then
        if [ -f "$path/$path.dvc" ]; then
            echo "current"
            return 0
        fi
    fi
    
    # 상위 디렉토리의 .dvc 파일 확인 (.git 디렉토리까지만)
    while [ "$current_path" != "." ] && [ "$(cd "$current_path" && pwd)" != "$git_root" ]; do
        current_path=$(dirname "$current_path")
        if [ -f "$current_path/$current_path.dvc" ]; then
            echo "parent"
            return 0
        fi
    done
    
    echo "none"
    return 1
}

if [ "$1" = "add" ]; then
    echo "Detected git add command..."
    shift
    for arg in "$@"; do
        echo "Processing file: $arg"
        # Handle .dvc files
        if [[ "$arg" == *.dvc ]]; then
            echo "Processing .dvc file: $arg"
            if [ ! -f "$arg" ]; then
                echo "Warning: $arg file does not exist, skipping DVC processing"
                continue
            fi
            # Get the directory of the .dvc file
            dvc_dir=$(dirname "$arg")
            dvc_path=$(grep "path:" "$arg" | cut -d: -f2 | tr -d " ")
            if [ ! -z "$dvc_path" ]; then
                # If dvc_path is not absolute, make it relative to the .dvc file location
                if [[ "$dvc_path" != /* ]]; then
                    dvc_path="$dvc_dir/$dvc_path"
                fi
                echo "Updating DVC tracking... (path: $dvc_path)"
                dvc add "$dvc_path"
            fi
            $GIT_EXEC add "$arg"
            continue
        fi
        
        # Check if .dvc file exists for this path
        dvc_status=$(check_dvc_file "$arg")
        if [ "$dvc_status" = "current" ]; then
            echo "$arg has .dvc file, updating DVC tracking"
            dvc add "$arg"
            echo "Adding $arg.dvc to git"
            $GIT_EXEC add "$arg.dvc"
        elif [ "$dvc_status" = "parent" ]; then
            # 상위 디렉토리가 DVC로 추적되고 있으면 일반 git add 실행
            echo "Parent directory is tracked by DVC, proceeding with git add: $arg"
            $GIT_EXEC add "$arg"
        else
            # .dvc 파일이 없으면 일반 git add 실행
            echo "No .dvc file found, proceeding with git add: $arg"
            $GIT_EXEC add "$arg"
        fi
    done
else
    $GIT_EXEC "$@"
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
echo "1. git add data - will automatically run dvc add if data.dvc exists"
echo "   or git add data.dvc - will automatically run dvc add data"
echo "2. git commit -m 'message'"
echo "3. git push - will automatically run dvc push"
echo ""
echo "When creating a new Git repository, run this script again after git init."
