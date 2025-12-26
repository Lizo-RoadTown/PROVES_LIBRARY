"""
Verify a documentation page before extraction

Checks:
1. URL is accessible (200 OK)
2. Page has actual content (not empty, not just navigation)
3. Returns sample of content for human verification
"""
import httpx


def verify_page(url: str) -> dict:
    """
    Verify a documentation page is suitable for extraction.

    Returns:
        {
            "valid": bool,
            "status_code": int,
            "content_length": int,
            "has_content": bool,
            "sample": str,  # First 500 chars
            "error": str or None
        }
    """
    try:
        headers = {
            "User-Agent": "PROVES-Library-Curator/1.0 (knowledge extraction for CubeSat safety)"
        }

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)

        if response.status_code != 200:
            return {
                "valid": False,
                "status_code": response.status_code,
                "content_length": 0,
                "has_content": False,
                "sample": "",
                "error": f"HTTP {response.status_code}"
            }

        content = response.text
        content_length = len(content)

        # Strip HTML for analysis
        import re
        text_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<[^>]+>', ' ', text_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()

        # Check for actual content (more than just navigation)
        has_content = len(text_content) > 500

        return {
            "valid": has_content,
            "status_code": response.status_code,
            "content_length": content_length,
            "has_content": has_content,
            "sample": text_content[:500],
            "error": None if has_content else "Page too short or empty"
        }

    except Exception as e:
        return {
            "valid": False,
            "status_code": 0,
            "content_length": 0,
            "has_content": False,
            "sample": "",
            "error": str(e)
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python verify_page.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    result = verify_page(url)

    print(f"URL: {url}")
    print(f"Valid: {'✅' if result['valid'] else '❌'}")
    print(f"Status: {result['status_code']}")
    print(f"Content Length: {result['content_length']} bytes")
    print(f"Has Content: {result['has_content']}")
    if result['error']:
        print(f"Error: {result['error']}")
    print()
    print("Sample (first 500 chars):")
    print("-" * 80)
    print(result['sample'])
    print("-" * 80)
