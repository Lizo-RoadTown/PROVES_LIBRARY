#!/usr/bin/env python3
"""Fix Liquid template syntax errors in markdown files"""

def fix_liquid_syntax(filepath):
    """Wrap code blocks containing {{ with raw tags"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output = []
    in_code_block = False
    code_block_lines = []

    for line in lines:
        if line.strip().startswith('```python'):
            in_code_block = True
            code_block_lines = [line]
        elif line.strip() == '```' and in_code_block:
            code_block_lines.append(line)
            in_code_block = False

            # Check if this code block has {{ (Liquid syntax)
            block_text = ''.join(code_block_lines)
            if '{{' in block_text:
                # Wrap with raw tags
                output.append('{% raw %}\n')
                output.extend(code_block_lines)
                output.append('{% endraw %}\n')
            else:
                output.extend(code_block_lines)

            code_block_lines = []
        elif in_code_block:
            code_block_lines.append(line)
        else:
            output.append(line)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(output)

    print(f"Fixed Liquid syntax in {filepath}")

if __name__ == '__main__':
    fix_liquid_syntax('docs/AGENTIC_ARCHITECTURE.md')
