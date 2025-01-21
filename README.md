# Git-DVC Bridge

A tool that automatically integrates Git and DVC to simplify data version management.

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
# Remove Git hooks configuration
./uninstall-git-hooks.sh
source ~/.bashrc
```

## License

MIT License
