import os
import sys
import json
import re
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

# Common fixes map
FIXES = {
    r"(\w+)\s*:\s*(\w+)": r"\1:::\2",  # Fix :class to :::class
}

def get_github_url(repo_owner, repo_name, branch, file_path):
    # Convert local path to relative path
    try:
        rel_path = Path(file_path).relative_to(os.getcwd()).as_posix()
    except ValueError:
        # If not relative to cwd, assume it's already relative
        rel_path = Path(file_path).as_posix()
        
    return f"https://github.com/{repo_owner}/{repo_name}/blob/{branch}/{rel_path}"

def parse_mermaid_error(error_text):
    # Extract line number and context from error text
    # Example: "Parse error on line 5: ... nodeId(Node) A :className --> B ... Expecting ..., got 'COLON'"
    line_match = re.search(r"Parse error on line (\d+)", error_text)
    if line_match:
        return int(line_match.group(1))
    return None

def fix_file(file_path, error_details):
    print(f"Attempting to fix {file_path}...")
    content = Path(file_path).read_text(encoding='utf-8')
    lines = content.splitlines()
    
    # This is a simplified fixer. A real one would need to map the mermaid block line number 
    # to the file line number.
    # For now, let's apply global regex fixes for known issues if we detect them in the error.
    
    fixed = False
    new_content = content
    
    # Fix 1: Class syntax :class -> :::class
    # If error mentions 'COLON' and we see the pattern
    if "got 'COLON'" in error_details or "Expecting" in error_details:
        # Look for "Node :Class" pattern
        # Regex: Identifier space? : space? Identifier (but not in a string or label)
        # This is risky to do globally, but let's try to be specific
        
        # Pattern: Node :Class -->
        pattern = r"(\S+)\s+:[a-zA-Z0-9_]+\s"
        # This is hard to regex safely without parsing.
        
        # Let's use the specific fix I verified: " :className" -> ":::className"
        # We'll look for " :[word]" and replace with ":::[word]" inside mermaid blocks
        
        mermaid_blocks = re.finditer(r"```mermaid\n(.*?)```", new_content, re.DOTALL)
        
        offset_correction = 0
        
        for block in mermaid_blocks:
            block_content = block.group(1)
            # Check for the bad syntax
            # A :class
            # A[label] :class
            
            # Regex for :class that should be :::class
            # It usually appears after a node ID or definition
            # We want to avoid "Title: Subtitle" in labels
            
            # Safe heuristic: " :class" where class is a simple identifier, followed by newline or arrow
            new_block_content = re.sub(r"(\s+):([a-zA-Z0-9_]+)(?=\s|;|-->|-\.|==)", r"\1:::\2", block_content)
            
            if new_block_content != block_content:
                # Apply replacement
                start = block.start(1) + offset_correction
                end = block.end(1) + offset_correction
                new_content = new_content[:start] + new_block_content + new_content[end:]
                offset_correction += len(new_block_content) - len(block_content)
                fixed = True
                print(f"  Fixed class syntax in mermaid block.")

    if fixed:
        Path(file_path).write_text(new_content, encoding='utf-8')
        print(f"  Saved changes to {file_path}")
        return True
    else:
        print(f"  Could not automatically fix {file_path}. Manual intervention required.")
        return False

def verify_files(files, repo_owner, repo_name, branch, fix=False):
    results = {"passed": [], "failed": [], "fixed": []}
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for file_path in files:
            url = get_github_url(repo_owner, repo_name, branch, file_path)
            print(f"Checking {file_path} at {url}...")
            
            try:
                page.goto(url, timeout=90000)
                page.wait_for_load_state("networkidle", timeout=90000)
                # Wait a bit for mermaid to render
                time.sleep(2)
                
                # Check for errors
                # "Unable to render rich display" is the GitHub container for the error
                error_elements = page.get_by_text("Unable to render rich display").all()
                
                # Filter out the documentation text itself (which we know exists in MERMAID_RULES.md)
                # We can check if the element is inside a markdown-body but NOT inside a code block or specific section?
                # Actually, the error usually appears as a specific UI element.
                # GitHub renders errors in a `div.flash-error` or similar, but "Unable to render rich display" is text.
                
                real_errors = []
                for err in error_elements:
                    # Check if this is just text in the document
                    # If it's a real error, it usually has a "Parse error" sibling or child
                    # or it's inside a specific container.
                    # For now, let's assume if we see "Parse error" nearby, it's real.
                    
                    # Look for "Parse error" on the page
                    parse_errors = page.get_by_text("Parse error").all()
                    if parse_errors:
                        real_errors.extend([e.inner_text() for e in parse_errors])
                        break # Found errors
                
                if real_errors:
                    print(f"  FAILED: Found {len(real_errors)} errors.")
                    results["failed"].append({"file": file_path, "errors": real_errors})
                    
                    if fix:
                        # Try to fix
                        error_text = "\n".join(real_errors)
                        if fix_file(file_path, error_text):
                            results["fixed"].append(file_path)
                            # Remove from failed if fixed? No, keep track.
                else:
                    print("  PASSED")
                    results["passed"].append(file_path)
                    
            except Exception as e:
                print(f"  ERROR checking file: {e}")
                results["failed"].append({"file": file_path, "errors": [str(e)]})
                
        browser.close()
        
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Mermaid rendering on GitHub")
    parser.add_argument("--files", nargs="+", help="List of files to check")
    parser.add_argument("--branch", default="verification-auto", help="Branch to check")
    parser.add_argument("--owner", default="phantom-man", help="Repo owner")
    parser.add_argument("--repo", default="PROVES_LIBRARY", help="Repo name")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix errors")
    
    args = parser.parse_args()
    
    if not args.files:
        # Default to finding all .md files in docs/diagrams if no files provided
        # This is just a fallback
        args.files = [str(p) for p in Path("docs/diagrams").glob("*.md")]
        
    print(f"Verifying {len(args.files)} files on branch '{args.branch}'...")
    
    results = verify_files(args.files, args.owner, args.repo, args.branch, args.fix)
    
    print("\n--- Summary ---")
    print(f"Passed: {len(results['passed'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Fixed: {len(results['fixed'])}")
    
    if results["failed"]:
        print("\nFiles with errors:")
        for item in results["failed"]:
            print(f"- {item['file']}")
        sys.exit(1)
    sys.exit(0)
