"""Check what's actually in the Notion page"""
from src.curator.notion_sync import NotionSync

sync = NotionSync()
page_id = '2d76b8ea-578a-81f6-a663-f1e1c53fb6b5'

blocks = sync.client.blocks.children.list(page_id)

print('ACTUAL CONTENT IN NOTION PAGE:')
print('='*70)

for i, block in enumerate(blocks['results'], 1):
    block_type = block['type']
    content = block.get(block_type, {})

    if 'rich_text' in content and content['rich_text']:
        text = content['rich_text'][0].get('plain_text', '')
        print(f'{i}. [{block_type}]')
        print(f'   {text}')
        print()
    elif block_type == 'code':
        code_content = content.get('rich_text', [])
        if code_content:
            code_text = code_content[0].get('plain_text', '')
            print(f'{i}. [code]')
            print(f'   {code_text[:200]}...')
            print()
    else:
        print(f'{i}. [{block_type}] (no text content)')
        print()
