# Git-DVC Bridge

A tool that automatically integrates Git and DVC to simplify data version management.

## Advantages

### 1. Workflow Automation
- Automatically executes `dvc add` when adding `.dvc` files with `git add`
- Automatically performs `dvc push` when executing `git push`
- Automatically runs `dvc pull` after `git pull` to sync data
- Prevents mistakes by eliminating manual DVC commands

### 2. User-Friendly Experience
- Handles DVC operations using existing Git commands
- No need to learn additional commands
- Maintains Git workflow while leveraging DVC features

### 3. Consistency Guarantee
- Automated synchronization between Git and DVC repositories
- Prevents mismatches between `.dvc` files and actual data
- Maintains data version consistency across team members

### 4. Error Prevention
- Prevents missing `dvc add` operations
- Prevents missing `dvc push` operations
- Prevents direct Git tracking of data files

### 5. Enhanced Collaboration
- Ensures consistent workflow across team members
- Standardizes data version control
- Easy onboarding for new team members

### 6. Easy Installation and Management
- One-time system-wide installation
- No additional per-project configuration needed
- Automated Git hook management

### 7. Improved Development Productivity
- Reduces repetitive command inputs
- Shortens data management tasks
- Reduces debugging time from version control mistakes

## Installation

You can install this package in three ways:

1. From PyPI (Not available yet):
```bash
# Install the package
pip install git-dvc-bridge

# Setup Git hooks and wrapper
git-dvc-bridge
```

2. Directly from GitHub:
```bash
# Install the package
pip install git+https://github.com/teri0411/git-dvc-bridge.git

# Setup Git hooks and wrapper
git-dvc-bridge
source ~/.bashrc
```

3. Manual Installation:
```bash
# Clone the repository
git clone https://github.com/teri0411/git-dvc-bridge.git
cd git-dvc-bridge

# Run the installation script
./scripts/install-git-hooks.sh
```

## Features

- Automatically runs `dvc add` when adding files tracked by DVC
- Automatically runs `dvc push` before Git push via pre-push hook
- Automatically runs `dvc pull` after Git pull to sync data
- Shows both Git and DVC status with `git status`
- Shows both Git and DVC diff with `git diff`

## Usage

After installation, you can use Git commands as usual:

1. `git add <file>` - Automatically runs `dvc add` if the file is tracked by DVC
2. `git commit -m "message"` - Commits changes as usual
3. `git push` - Automatically runs `dvc push` before pushing to ensure data is synced
4. `git pull` - Automatically runs `dvc pull` after pulling to sync data
5. `git status` - Shows both Git and DVC status
6. `git diff` - Shows both Git and DVC diff

## Key Features

- Automatically runs dvc add when .dvc files are detected during git add
- Automatically runs dvc push when git push is executed
- Auto-detection and handling of multiple DVC repositories
- Automatically runs `dvc data status --granular` when `git status` is executed
- Automatically runs `dvc diff` when `git diff` is executed

## Additional Features

- When executing the `git status` command, `dvc data status --granular` is automatically executed, allowing you to check the detailed status of DVC data.
- When executing the `git diff` command, `dvc diff` is automatically executed, making it easy to identify differences between data versions.

## --granular Option Explanation

The `--granular` option provides a more detailed view of the DVC data status, helping you clearly understand how each part of the data file has changed.

## Uninstall

```bash
#uninstall the package
pip uninstall git-dvc-bridge

# Remove Git hooks configuration
./uninstall-git-hooks.sh
source ~/.bashrc
```

## License

MIT License
