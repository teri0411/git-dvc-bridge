"""Git-DVC bridge for automating DVC operations with Git commands."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Iterator

# Constants
GIT_PATHS = "/usr/bin:/bin:/usr/local/bin"
GIT_WRAPPER_ENV = "GIT_WRAPPER_RUNNING"
BASHRC_EXPORT = 'export PATH="{}/bin:$PATH"'
DEFAULT_HOOKS_DIR = ".git-hooks"


class GitDVCError(Exception):
    """Custom exception for Git-DVC bridge errors."""

    pass


def run_command(cmd: List[str], cwd: Optional[str] = None) -> None:
    """Execute a shell command with error handling.

    Args:
        cmd: Command and arguments as list
        cwd: Working directory for command execution

    Raises:
        GitDVCError: If command execution fails
    """
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(cmd)}")
        print(f"Error: {e}")
        sys.exit(e.returncode)


def find_git() -> str:
    """Find the original git executable.

    Returns:
        Path to git executable

    Raises:
        GitDVCError: If git executable not found
    """
    git_path = shutil.which("git", path=GIT_PATHS)
    if not git_path:
        raise GitDVCError("Could not find git executable")
    return git_path


def create_git_wrapper(git_path: str) -> str:
    """Create git wrapper script content.

    Args:
        git_path: Path to original git executable

    Returns:
        Wrapper script content
    """
    return f'''#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

GIT_EXEC = "{git_path}"

if os.environ.get("{GIT_WRAPPER_ENV}"):
    os.execvp(GIT_EXEC, [GIT_EXEC] + sys.argv[1:])

os.environ["{GIT_WRAPPER_ENV}"] = "1"

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {{' '.join(cmd)}}")
        print(f"Error: {{e}}")
        sys.exit(e.returncode)

def handle_dvc_file(file_path):
    """Handle .dvc file processing"""
    if os.path.isfile(file_path):
        try:
            with open(file_path) as f:
                content = f.read()
                import re
                match = re.search(r'path:\\s*(.+)', content)
                if match:
                    dvc_path = match.group(1).strip()
                    if dvc_path and not os.path.isabs(dvc_path):
                        dvc_dir = os.path.dirname(file_path)
                        dvc_path = os.path.join(dvc_dir, dvc_path)
                        print(f"Updating DVC tracking... (path: {{dvc_path}})")
                        run_command(["dvc", "add", dvc_path])
        except Exception as e:
            print(f"Warning: Could not process .dvc file: {{e}}")
    run_command([GIT_EXEC, "add", file_path])

def check_dvc_file(path):
    """Check if a .dvc file exists in the same directory as the path."""
    path = Path(path)
    
    # Check if .dvc file exists in current path
    if path.with_suffix(path.suffix + '.dvc').is_file():
        return True, str(path.with_suffix(path.suffix + '.dvc')), False
    
    # If it's a directory, check for .dvc file inside
    if path.is_dir():
        dvc_file = path / (path.name + '.dvc')
        if dvc_file.is_file():
            return True, str(dvc_file), False
    
    # Check parent directories for .dvc files (up to git root)
    current = path
    git_root = subprocess.check_output(
        [GIT_EXEC, "rev-parse", "--show-toplevel"],
        universal_newlines=True
    ).strip()
    
    while current != current.parent and str(current.absolute()) != git_root:
        current = current.parent
        dvc_file = current / (current.name + '.dvc')
        if dvc_file.is_file():
            return True, str(dvc_file), True
    
    return False, None, False

def handle_regular_file(file_path):
    """Handle regular file processing"""
    has_dvc, dvc_file, is_parent_dvc = check_dvc_file(file_path)
    if has_dvc:
        if is_parent_dvc:
            print(f"Parent directory is tracked by DVC, proceeding with git add: {{file_path}}")
            run_command([GIT_EXEC, "add", file_path])
        else:
            print(f"{{file_path}} has .dvc file, updating DVC tracking")
            run_command(["dvc", "add", file_path])
            print(f"Adding {{dvc_file}} to git")
            run_command([GIT_EXEC, "add", dvc_file])
    else:
        run_command([GIT_EXEC, "add", file_path])

def handle_directory():
    """Handle directory processing (git add .)"""
    try:
        files = subprocess.check_output(
            [GIT_EXEC, "ls-files", "--others", "--exclude-standard", "--cached"],
            universal_newlines=True,
            stderr=subprocess.DEVNULL
        ).splitlines()
        
        for file_path in files:
            # Skip special files
            if file_path in ['.dvcignore', '.gitignore'] or file_path.startswith(('.git/', '.dvc/')):
                subprocess.run([GIT_EXEC, "add", file_path], stderr=subprocess.DEVNULL)
                continue
            
            # Handle .dvc files
            if file_path.endswith(".dvc"):
                handle_dvc_file(file_path)
                continue
            
            # Process regular files
            handle_regular_file(file_path)
            
    except subprocess.CalledProcessError:
        os.execvp(GIT_EXEC, [GIT_EXEC, "add", "."])

if len(sys.argv) > 1:
    if sys.argv[1] == "add":
        args = sys.argv[2:]
        for arg in args:
            # Special handling for current directory
            if arg == ".":
                handle_directory()
                continue
            
            # Handle .dvc files
            if arg.endswith(".dvc"):
                handle_dvc_file(arg)
                continue
            
            # Handle regular files
            handle_regular_file(arg)
    elif sys.argv[1] == "diff":
        try:
            print("\\n=== Git Diff ===")
            subprocess.run([GIT_EXEC] + sys.argv[1:], check=False)
            print("\\n=== DVC Diff ===")
            subprocess.run(["dvc", "diff"], check=False)
        except FileNotFoundError:
            print("DVC not found, proceeding with git diff only")
            subprocess.run([GIT_EXEC] + sys.argv[1:], check=False)
    elif sys.argv[1] == "pull":
        try:
            print("\\n=== Git Pull ===")
            subprocess.run([GIT_EXEC] + sys.argv[1:], check=True)
            print("\\n=== DVC Pull ===")
            subprocess.run(["dvc", "pull"], check=True)
        except FileNotFoundError:
            print("DVC not found, proceeding with git pull only")
            subprocess.run([GIT_EXEC] + sys.argv[1:], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during pull: {{e}}")
            sys.exit(e.returncode)
    elif sys.argv[1] == "status":
        # Run git status and dvc data status --granular
        try:
            print("\\n=== Git Status ===")
            subprocess.run([GIT_EXEC, "status"], check=False)
            print("\\n=== DVC Data Status ===")
            subprocess.run(["dvc", "data", "status", "--granular"], check=False)
        except FileNotFoundError:
            print("DVC not found, proceeding with git status only")
    else:
        os.execvp(GIT_EXEC, [GIT_EXEC] + sys.argv[1:])
else:
    os.execvp(GIT_EXEC, [GIT_EXEC] + sys.argv[1:])

'''


def create_pre_push_hook() -> str:
    """Create pre-push hook script content.

    Returns:
        Pre-push hook script content
    """
    return '''#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(cmd)}")
        print(f"Error: {e}")
        sys.exit(e.returncode)

def find_dvc_repos(start_path):
    """Find all DVC repositories under the given path."""
    for path in Path(start_path).rglob(".dvc"):
        if path.is_dir():
            yield path.parent

def main():
    print("Current directory:", os.getcwd())
    
    git_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        universal_newlines=True
    ).strip()
    
    print("Git root directory:", git_root)
    
    found_repos = False
    for repo in find_dvc_repos(git_root):
        found_repos = True
        print("DVC repository found:", repo)
        print("Executing DVC push before Git push...")
        run_command(["dvc", "push"], cwd=repo)
    
    if not found_repos:
        print("No DVC repository found in Git repository.")

if __name__ == "__main__":
    main()
'''


def setup_git_wrapper() -> None:
    """Setup git wrapper script in user's bin directory."""
    bin_dir = Path.home() / "bin"
    bin_dir.mkdir(exist_ok=True)

    # Update PATH in bashrc if needed
    bashrc = Path.home() / ".bashrc"
    path_export = BASHRC_EXPORT.format(Path.home())

    if bashrc.exists() and path_export not in bashrc.read_text():
        with open(bashrc, "a") as f:
            f.write(f"\n{path_export}\n")

    # Create and configure wrapper script
    wrapper_path = bin_dir / "git"
    wrapper_content = create_git_wrapper(find_git())

    with open(wrapper_path, "w") as f:
        f.write(wrapper_content)
    wrapper_path.chmod(0o755)


def setup_git_hooks() -> None:
    """Setup git hooks for DVC integration."""
    hooks_dir = Path.home() / DEFAULT_HOOKS_DIR
    hooks_dir.mkdir(exist_ok=True)

    # Create and configure pre-push hook
    pre_push_path = hooks_dir / "pre-push"
    pre_push_content = create_pre_push_hook()

    with open(pre_push_path, "w") as f:
        f.write(pre_push_content)
    pre_push_path.chmod(0o755)

    # Configure git to use hooks directory
    run_command(["git", "config", "--global", "core.hooksPath", str(hooks_dir)])


def print_usage_instructions() -> None:
    """Print post-installation usage instructions."""
    print("Installation complete!")
    print("Please restart your terminal or run:")
    print("source ~/.bashrc")
    print("")
    print("Now you can use Git commands as usual:")
    print("1. git add data - will automatically run dvc add if data.dvc exists")
    print("   or git add data.dvc - will automatically run dvc add data")
    print("2. git commit -m 'message'")
    print("3. git push - will automatically run dvc push")
    print("")
    print("When creating a new Git repository, run 'git init' first.")


def main() -> None:
    """Main entry point for the git-dvc-bridge command."""
    try:
        setup_git_wrapper()
        setup_git_hooks()
        print_usage_instructions()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
