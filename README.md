# Git-DVC Bridge

A tool that automatically integrates Git and DVC to simplify data version management.

## Advantages

### 1. Workflow Automation
- Automatically executes `dvc add` when adding `.dvc` files with `git add`
- Automatically performs `dvc push` when executing `git push`
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

## Usage

After installation and setup, you can use Git commands as usual:

1. `dvc add data` (Initial data tracking)
2. `git add data.dvc` (automatically runs dvc add)
3. `git commit -m "message"`
4. `git push` (automatically runs dvc push)

## Key Features

- Automatically runs dvc add when .dvc files are detected during git add
- Automatically runs dvc push when git push is executed
- Auto-detection and handling of multiple DVC repositories

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
