#!/bin/bash

# Find original git executable
ORIGINAL_GIT=/usr/bin/git

# Create bin directory
mkdir -p ~/bin 2>/dev/null

# Add ~/bin to PATH
if ! grep -q "export PATH=\"$HOME/bin:$PATH\"" ~/.bashrc; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc 2>/dev/null
fi
export PATH="$HOME/bin:$PATH" 2>/dev/null

# Create Git wrapper script
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
    local git_root=$($GIT_EXEC rev-parse --show-toplevel 2>/dev/null)
    
    # Check if .dvc file exists in current path
    if [ -f "${path}.dvc" ]; then
        echo "current"
        return 0
    fi
    
    # If it's a directory, check for .dvc file inside
    if [ -d "$path" ]; then
        if [ -f "$path/$path.dvc" ]; then
            echo "current"
            return 0
        fi
        
        # Check parent directories for .dvc files (up to git root)
        while [ "$current_path" != "." ] && [ "$(cd "$(dirname "$current_path")" && pwd)" != "$git_root" ]; do
            current_path=$(dirname "$current_path")
            if [ -f "$current_path/$current_path.dvc" ]; then
                echo "parent"
                return 0
            fi
        done
    else
        # For files, check parent directories
        while [ "$current_path" != "." ] && [ "$(cd "$(dirname "$current_path")" && pwd 2>/dev/null)" != "$git_root" ]; do
            current_path=$(dirname "$current_path")
            if [ -f "$current_path/$current_path.dvc" ]; then
                echo "parent"
                return 0
            fi
        done
    fi
    
    echo "none"
    return 1
}

if [ "$1" = "add" ]; then
    shift
    for arg in "$@"; do
        # Special handling for current directory
        if [ "$arg" = "." ]; then
            # Use git ls-files to respect .gitignore
            $GIT_EXEC ls-files --others --exclude-standard --cached | while read file; do
                # Skip .dvcignore and other internal files
                if [[ "$file" == ".dvcignore" ]] || [[ "$file" == ".gitignore" ]] || [[ "$file" == ".git/"* ]] || [[ "$file" == ".dvc/"* ]]; then
                    $GIT_EXEC add "$file" 2>/dev/null
                    continue
                fi
                
                if [[ "$file" == *.dvc ]]; then
                    # Get the directory of the .dvc file
                    dvc_dir=$(dirname "$file")
                    dvc_path=$(grep "path:" "$file" | cut -d: -f2 | tr -d " ")
                    if [ ! -z "$dvc_path" ]; then
                        if [[ "$dvc_path" != /* ]]; then
                            dvc_path="$dvc_dir/$dvc_path"
                        fi
                        echo "Updating DVC tracking... (path: $dvc_path)"
                        dvc add "$dvc_path"
                    fi
                    $GIT_EXEC add "$file" 2>/dev/null
                    continue
                fi
                
                # Check if .dvc file exists for this path
                dvc_status=$(check_dvc_file "$file")
                if [ "$dvc_status" = "current" ]; then
                    echo "Processing DVC tracked file: $file"
                    dvc add "$file"
                    $GIT_EXEC add "$file.dvc" 2>/dev/null
                elif [ "$dvc_status" = "parent" ]; then
                    $GIT_EXEC add "$file" 2>/dev/null
                else
                    $GIT_EXEC add "$file" 2>/dev/null
                fi
            done
            continue
        fi
        
        # Handle .dvc files
        if [[ "$arg" == *.dvc ]]; then
            if [ ! -f "$arg" ]; then
                echo "Warning: $arg file does not exist, skipping DVC processing"
                continue
            fi
            dvc_dir=$(dirname "$arg")
            dvc_path=$(grep "path:" "$arg" | cut -d: -f2 | tr -d " ")
            if [ ! -z "$dvc_path" ]; then
                if [[ "$dvc_path" != /* ]]; then
                    dvc_path="$dvc_dir/$dvc_path"
                fi
                echo "Updating DVC tracking... (path: $dvc_path)"
                dvc add "$dvc_path"
            fi
            $GIT_EXEC add "$arg" 2>/dev/null
            continue
        fi
        
        # Check if .dvc file exists for this path
        dvc_status=$(check_dvc_file "$arg")
        if [ "$dvc_status" = "current" ]; then
            echo "Processing DVC tracked file: $arg"
            dvc add "$arg"
            $GIT_EXEC add "$arg.dvc" 2>/dev/null
        elif [ "$dvc_status" = "parent" ]; then
            $GIT_EXEC add "$arg" 2>/dev/null
        else
            $GIT_EXEC add "$arg" 2>/dev/null
        fi
    done
else
    $GIT_EXEC "$@"
fi
EOF

chmod +x ~/bin/git 2>/dev/null

# Create pre-push hook
mkdir -p ~/.git-hooks 2>/dev/null
cat > ~/.git-hooks/pre-push << 'EOF'
#!/bin/bash

# Find Git repository root directory (.git directory location)
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
cd "$GIT_ROOT"

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
fi

exit 0
EOF

chmod +x ~/.git-hooks/pre-push 2>/dev/null

# Configure Git to use hooks directory
/usr/bin/git config --global core.hooksPath ~/.git-hooks 2>/dev/null
