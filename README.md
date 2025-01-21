# Git-DVC Bridge

A tool that automatically integrates Git and DVC to simplify data version management.

## Installation

You can install this package in three ways:

1. From PyPI (Not available yet):
```bash
pip install git-dvc-bridge
```

2. Directly from GitHub:
```bash
pip install git+https://github.com/teri0411/git-dvc-bridge.git
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

After installation, run the following command to set up Git-DVC bridge:

```bash
git-dvc-bridge
```

Then you can use Git commands as usual:

1. `dvc add data` (Initial data tracking)
2. `git add data.dvc` (automatically runs dvc add)
3. `git commit -m "message"`
4. `git push` (automatically runs dvc push)

## Key Features

- Automatically runs dvc add when .dvc files are detected during git add
- Automatically runs dvc push when git push is executed
- Auto-detection and handling of multiple DVC repositories

## Uninstall

Depending on how you installed the package, use one of these methods to uninstall:

1. If installed via pip (PyPI or GitHub):
```bash
# Remove the package
pip uninstall git-dvc-bridge

# Remove Git hooks configuration
git config --global --unset core.hooksPath
```

2. If installed manually:
```bash
# Remove Git hooks configuration
git config --global --unset core.hooksPath

# Remove the cloned repository (optional)
rm -rf /path/to/git-dvc-bridge
```

## License

MIT License
