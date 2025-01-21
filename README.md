# Git-DVC Bridge

A tool that automatically integrates Git and DVC to simplify data version management.

## Installation

```bash
pip install git-dvc-bridge
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

Remove hooks path from Git global configuration:

```bash
git config --global --unset core.hooksPath
```

## License

MIT License
