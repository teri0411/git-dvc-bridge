import os
import sys
import subprocess
import shutil
from pathlib import Path

def find_git():
    """Find the original git executable."""
    git_path = shutil.which("git", path="/usr/bin:/bin:/usr/local/bin")
    if not git_path:
        raise RuntimeError("Could not find git executable")
    return git_path

def setup_git_wrapper():
    """Setup the git wrapper script."""
    bin_dir = Path.home() / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    # Add ~/bin to PATH if not already present
    bashrc = Path.home() / ".bashrc"
    path_export = f'export PATH="{bin_dir}:$PATH"'
    
    if bashrc.exists():
        if path_export not in bashrc.read_text():
            with open(bashrc, "a") as f:
                f.write(f"\n{path_export}\n")
    
    # Create git wrapper script
    wrapper_path = bin_dir / "git"
    wrapper_content = '''#!/usr/bin/env python3
import os
import sys
import subprocess

GIT_EXEC = "{git_path}"

if os.environ.get("GIT_WRAPPER_RUNNING"):
    os.execvp(GIT_EXEC, [GIT_EXEC] + sys.argv[1:])

os.environ["GIT_WRAPPER_RUNNING"] = "1"

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {{' '.join(cmd)}}")
        print(f"Error: {{e}}")
        sys.exit(e.returncode)

if len(sys.argv) > 1 and sys.argv[1] == "add":
    print("Detected git add command...")
    # Remove "add" from arguments like 'shift' in bash
    args = sys.argv[2:]
    for arg in args:
        print(f"Processing file: {{arg}}")
        # Exactly match bash script conditions
        if os.path.isfile(arg) and arg.endswith(".dvc"):
            try:
                with open(arg) as f:
                    content = f.read()
                    import re
                    # Match bash script's grep behavior
                    match = re.search(r'path:\s*(.+)', content)
                    if match:
                        dvc_path = match.group(1).strip()
                        # Match bash script's -z check
                        if dvc_path and len(dvc_path) > 0:
                            print(f"Updating DVC tracking... (path: {{dvc_path}})")
                            run_command(["dvc", "add", dvc_path])
            except Exception as e:
                print(f"Warning: Could not process .dvc file: {{e}}")
        
        # Execute git add exactly like bash script
        print(f"Executing Git add: {{arg}}")
        run_command([GIT_EXEC, "add", arg])
else:
    # Exactly match bash exec behavior
    os.execvp(GIT_EXEC, [GIT_EXEC] + sys.argv[1:])
'''.format(git_path=find_git())
    
    with open(wrapper_path, "w") as f:
        f.write(wrapper_content)
    wrapper_path.chmod(0o755)

def setup_git_hooks():
    """Setup git hooks for DVC integration."""
    hooks_dir = Path.home() / ".git-hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    # Create pre-push hook
    pre_push_path = hooks_dir / "pre-push"
    pre_push_content = '''#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {{' '.join(cmd)}}")
        print(f"Error: {{e}}")
        sys.exit(e.returncode)

def find_dvc_repos(start_path):
    """Find all DVC repositories under the given path."""
    for path in Path(start_path).rglob(".dvc"):
        if path.is_dir():
            yield path.parent

def main():
    print(f"Current directory: {{os.getcwd()}}")
    
    # Get git root directory
    git_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        universal_newlines=True
    ).strip()
    
    print(f"Git root directory: {{git_root}}")
    
    # Find and process all DVC repositories
    found_repos = False
    for repo in find_dvc_repos(git_root):
        found_repos = True
        print(f"DVC repository found: {{repo}}")
        print("Executing DVC push before Git push...")
        run_command(["dvc", "push"], cwd=repo)
    
    if not found_repos:
        print("No DVC repository found in Git repository.")

if __name__ == "__main__":
    main()
'''
    
    with open(pre_push_path, "w") as f:
        f.write(pre_push_content)
    pre_push_path.chmod(0o755)
    
    # Configure git to use the hooks
    subprocess.run(
        ["git", "config", "--global", "core.hooksPath", str(hooks_dir)],
        check=True
    )

def main():
    """Main entry point for the git-dvc-bridge command."""
    try:
        setup_git_wrapper()
        setup_git_hooks()
        print("Git-DVC bridge installation completed!")
        print("\nNow you can use Git commands as usual:")
        print("1. dvc add data (only once initially)")
        print("2. git add data.dvc (automatically runs dvc add)")
        print("3. git commit -m 'message'")
        print("4. git push (automatically runs dvc push)")
        print("\nPlease restart your terminal or run:")
        print("source ~/.bashrc")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
