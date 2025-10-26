"""
Test script to verify deduplication fixes work correctly
Run this to test the scraper with a simple HTML example
"""

from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin
from typing import Set

# Sample HTML with intentional duplicates
TEST_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <main>
        <article>
            <h1>Main Title</h1>
            <p>This is the introduction paragraph.</p>
            
            <div class="section">
                <h2>Section 1</h2>
                <p>Content in section 1.</p>
                
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </div>
            
            <!-- Duplicate content below -->
            <div class="duplicate">
                <h2>Section 1</h2>
                <p>Content in section 1.</p>
            </div>
            
            <div class="another-container">
                <div class="nested">
                    <h2>Section 2</h2>
                    <p>Unique content here.</p>
                    <ul>
                        <li>Nested item 1</li>
                        <li>Nested item 2</li>
                    </ul>
                </div>
            </div>
        </article>
    </main>
</body>
</html>
"""

def test_deduplication():
    """Test the deduplication logic"""
    print("🔍 Testing Deduplication Logic\n")
    print("=" * 60)
    
    # Parse HTML
    soup = BeautifulSoup(TEST_HTML, "html.parser")
    main_content = soup.find("main")
    
    # Initialize tracking sets
    processed_elements: Set[int] = set()
    seen_content: Set[str] = set()
    text_parts = []
    
    # Simple processor for testing
    def process_element(el):
        if id(el) in processed_elements:
            print(f"⏭️  Skipped (already processed): <{el.name}>")
            return None
        
        element_text = el.get_text(strip=True)
        if not element_text:
            return None
            
        processed_elements.add(id(el))
        
        if el.name in ['h1', 'h2', 'h3']:
            return f"\n{'#' * int(el.name[1])} {element_text}\n"
        elif el.name == 'p':
            return element_text + "\n"
        elif el.name == 'ul':
            items = []
            for li in el.find_all("li", recursive=False):
                if id(li) not in processed_elements:
                    processed_elements.add(id(li))
                    items.append(f"- {li.get_text(strip=True)}")
            return "\n".join(items) + "\n" if items else ""
        elif el.name in ['div', 'article', 'section']:
            results = []
            for child in el.children:
                if hasattr(child, 'name'):
                    if id(child) not in processed_elements:
                        result = process_element(child)
                        if result:
                            results.append(result)
            return "\n".join(results) if results else None
        return None
    
    # Process all elements
    print("\n📋 Processing Elements:\n")
    for element in main_content.children:
        if hasattr(element, 'name') and element.name:
            if id(element) not in processed_elements:
                result = process_element(element)
                if result and result.strip():
                    normalized = result.strip().lower()
                    if normalized not in seen_content:
                        text_parts.append(result)
                        seen_content.add(normalized)
                        print(f"✅ Added: <{element.name}>")
                    else:
                        print(f"🚫 Duplicate detected: <{element.name}>")
    
    # Output results
    print("\n" + "=" * 60)
    print("\n📄 Final Output:\n")
    print("-" * 60)
    output = "\n".join(text_parts)
    print(output)
    print("-" * 60)
    
    # Count occurrences
    print("\n📊 Statistics:\n")
    print(f"Total elements processed: {len(processed_elements)}")
    print(f"Unique content blocks: {len(seen_content)}")
    print(f"Output lines: {len(output.splitlines())}")
    
    # Check for duplicates in output
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    duplicates = len(lines) - len(set(lines))
    
    if duplicates == 0:
        print("\n✅ SUCCESS: No duplicate lines in output!")
    else:
        print(f"\n❌ FAILED: {duplicates} duplicate lines found!")
    
    # Verify specific content
    print("\n🔎 Content Verification:\n")
    checks = [
        ("Section 1", output.count("Section 1") == 1, "Section 1 appears only once"),
        ("Content in section 1", output.count("Content in section 1") == 1, "Section 1 content not duplicated"),
        ("Item 1", output.count("Item 1") == 1, "List items not duplicated"),
        ("Section 2", "Section 2" in output, "Section 2 is present"),
        ("Nested item", "Nested item" in output, "Nested list items present"),
    ]
    
    all_passed = True
    for check_name, condition, description in checks:
        status = "✅" if condition else "❌"
        print(f"{status} {description}")
        if not condition:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed and duplicates == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)

if __name__ == "__main__":
    test_deduplication()
