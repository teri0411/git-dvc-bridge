#!/bin/bash

setup_environment() {
    # Find original git executable
    ORIGINAL_GIT=/usr/bin/git

    # Create bin directory
    mkdir -p ~/bin 2>/dev/null

    # Add ~/bin to PATH
    if ! grep -q "export PATH=\"$HOME/bin:$PATH\"" ~/.bashrc; then
        echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc 2>/dev/null
    fi
    export PATH="$HOME/bin:$PATH" 2>/dev/null
}

create_git_wrapper() {
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
    local git_root=$($GIT_EXEC rev-parse --show-toplevel)
    
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
        while [ "$current_path" != "." ] && [ "$(cd "$(dirname "$current_path")" && pwd)" != "$git_root" ]; do
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

handle_dvc_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo "Warning: $file file does not exist, skipping DVC processing"
        return
    fi
    local dvc_dir=$(dirname "$file")
    local dvc_path=$(grep "path:" "$file" | cut -d: -f2 | tr -d " ")
    if [ ! -z "$dvc_path" ]; then
        if [[ "$dvc_path" != /* ]]; then
            dvc_path="$dvc_dir/$dvc_path"
        fi
        echo "Updating DVC tracking... (path: $dvc_path)"
        dvc add "$dvc_path"
    fi
    $GIT_EXEC add "$file"
}

handle_regular_file() {
    local file="$1"
    local dvc_status=$(check_dvc_file "$file")
    
    if [ "$dvc_status" = "parent" ]; then
        echo "Parent directory is tracked by DVC, proceeding with git add: $file"
        $GIT_EXEC add "$file"
    elif [ "$dvc_status" = "current" ]; then
        echo "Processing DVC tracked file: $file"
        dvc add "$file"
        $GIT_EXEC add "${file}.dvc"
    else
        $GIT_EXEC add "$file"
    fi
}

handle_directory() {
    # Use git ls-files to respect .gitignore
    $GIT_EXEC ls-files --others --exclude-standard --cached | while read file; do
        # Skip .dvcignore and other internal files
        if [[ "$file" == ".dvcignore" ]] || [[ "$file" == ".gitignore" ]] || [[ "$file" == ".git/"* ]] || [[ "$file" == ".dvc/"* ]]; then
            $GIT_EXEC add "$file"
            continue
        fi
        
        if [[ "$file" == *.dvc ]]; then
            handle_dvc_file "$file"
        else
            handle_regular_file "$file"
        fi
    done
}

# Main command processing
if [ "$1" = "add" ]; then
    shift
    for arg in "$@"; do
        if [ "$arg" = "." ]; then
            handle_directory
        elif [[ "$arg" == *.dvc ]]; then
            handle_dvc_file "$arg"
        else
            handle_regular_file "$arg"
        fi
    done
elif [ "$1" = "diff" ]; then
    # Run git diff first, then dvc diff
    echo -e "\n=== Git Diff ==="
    $GIT_EXEC diff
    echo -e "\n=== DVC Diff ==="
    if command -v dvc &> /dev/null; then
        dvc diff
    else
        echo "DVC not found, proceeding with git diff only"
    fi
elif [ "$1" = "status" ]; then
    # Run git status first, then dvc status
    echo -e "\n=== Git Status ==="
    $GIT_EXEC status
    echo -e "\n=== DVC Data Status ==="
    if command -v dvc &> /dev/null; then
        dvc data status --granular
    else
        echo "DVC not found, proceeding with git status only"
    fi
elif [ "$1" = "pull" ]; then
    # Run git pull first, then dvc pull
    echo -e "\n=== Git Pull ==="
    shift  # Remove 'pull' from arguments
    if ! $GIT_EXEC pull "$@"; then
        echo "Git pull failed"
        exit 1
    fi
    echo -e "\n=== DVC Pull ==="
    if command -v dvc &> /dev/null; then
        if ! dvc pull; then
            echo "DVC pull failed"
            exit 1
        fi
    else
        echo "DVC not found, proceeding with git pull only"
    fi
else
    exec $GIT_EXEC "$@"
fi
EOF

    chmod +x ~/bin/git
}

create_pre_push_hook() {
    # Create pre-push hook
    mkdir -p ~/.git-hooks
    cat > ~/.git-hooks/pre-push << 'EOF'
#!/bin/bash

# Find Git repository root directory (.git directory location)
GIT_ROOT=$(git rev-parse --show-toplevel)
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
        dvc push || {
            echo "Error: Failed to push DVC tracked files in $dvc_repo"
            exit 1
        }
        cd "$GIT_ROOT"  # Return to Git root for next search
    done <<< "$dvc_dirs"
fi

exit 0
EOF

    chmod +x ~/.git-hooks/pre-push
    
    # Configure git to use hooks directory
    git config --global core.hooksPath ~/.git-hooks
}

main() {
    setup_environment
    create_git_wrapper
    create_pre_push_hook
    
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
    echo "When creating a new Git repository, run 'git init' first."
}

# Run main function
main
