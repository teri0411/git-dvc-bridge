#!/bin/bash

echo "Restoring Git configuration..."

# Reset Git hooks path to default
git config --global --unset core.hooksPath
echo "Reset Git hooks path to default"

# Remove Git wrapper
if [ -f ~/bin/git ]; then
    rm ~/bin/git
    echo "Removed Git wrapper"
fi

# Remove Git hooks directory
if [ -d ~/.git-hooks ]; then
    rm -rf ~/.git-hooks
    echo "Removed Git hooks directory"
fi

# Remove PATH modification from .bashrc
if [ -f ~/.bashrc ]; then
    sed -i '/export PATH="$HOME\/bin:$PATH"/d' ~/.bashrc
    echo "Removed PATH modification from .bashrc"
fi

echo "Uninstallation complete!"
echo "Please restart your terminal or run:"
echo "source ~/.bashrc"
