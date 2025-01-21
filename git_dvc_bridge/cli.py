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

def process_dvc_file(file_path: str) -> Optional[str]:
    """Extract and validate DVC path from .dvc file.
    
    Args:
        file_path: Path to .dvc file
    
    Returns:
        Extracted path or None if invalid
    """
    try:
        with open(file_path) as f:
            for line in f:
                if line.startswith("path:"):
                    dvc_path = line.split(":")[1].strip()
                    return dvc_path if dvc_path else None
    except Exception as e:
        print(f"Warning: Could not process .dvc file: {e}")
    return None

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

def check_dvc_file(path):
    """Check if a .dvc file exists in the same directory as the path."""
    path = Path(path)
    
    # 현재 경로에 .dvc 파일이 있는지 확인
    if path.with_suffix(path.suffix + '.dvc').is_file():
        return True, str(path.with_suffix(path.suffix + '.dvc')), False
    
    # 디렉토리인 경우 해당 디렉토리 내의 .dvc 파일 확인
    if path.is_dir():
        dvc_file = path / (path.name + '.dvc')
        if dvc_file.is_file():
            return True, str(dvc_file), False
    
    # 상위 디렉토리의 .dvc 파일 확인 (.git 디렉토리까지만)
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

if len(sys.argv) > 1 and sys.argv[1] == "add":
    print("Detected git add command...")
    args = sys.argv[2:]
    for arg in args:
        print(f"Processing file: {{arg}}")
        # Handle .dvc files
        if arg.endswith(".dvc"):
            if os.path.isfile(arg):
                try:
                    with open(arg) as f:
                        content = f.read()
                        import re
                        match = re.search(r'path:\\s*(.+)', content)
                        if match:
                            dvc_path = match.group(1).strip()
                            if dvc_path:
                                # If dvc_path is not absolute, make it relative to the .dvc file location
                                if not os.path.isabs(dvc_path):
                                    dvc_dir = os.path.dirname(arg)
                                    dvc_path = os.path.join(dvc_dir, dvc_path)
                                print(f"Updating DVC tracking... (path: {{dvc_path}})")
                                run_command(["dvc", "add", dvc_path])
                except Exception as e:
                    print(f"Warning: Could not process .dvc file: {{e}}")
            run_command([GIT_EXEC, "add", arg])
            continue
        
        # Check if .dvc file exists for this path
        has_dvc, dvc_file, is_parent_dvc = check_dvc_file(arg)
        if has_dvc:
            if is_parent_dvc:
                print(f"Parent directory is tracked by DVC, proceeding with git add: {{arg}}")
                run_command([GIT_EXEC, "add", arg])
            else:
                print(f"{{arg}} has .dvc file, updating DVC tracking")
                run_command(["dvc", "add", arg])
                print(f"Adding {{dvc_file}} to git")
                run_command([GIT_EXEC, "add", dvc_file])
        else:
            # No .dvc file, proceed with normal git add
            print(f"No .dvc file found, proceeding with git add: {{arg}}")
            run_command([GIT_EXEC, "add", arg])
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
    print("Git-DVC bridge installation completed!")
    print("\nNow you can use Git commands as usual:")
    print("1. dvc add data (only once initially)")
    print("2. git add data.dvc (automatically runs dvc add)")
    print("3. git commit -m 'message'")
    print("4. git push (automatically runs dvc push)")
    print("\nPlease restart your terminal or run:")
    print("source ~/.bashrc")

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
