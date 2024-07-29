import re

def get_publish_set_info(content):
    """Extract categories, keywords, and delete flag from the publishSet at the end of the content"""
    categories = []
    keywords = ""
    delete_flag = False

    pattern = r'# ArticleSync publishSet\n(?:category:([^,\n]+(?:,[^,\n]+)*)\n?)?(?:keywords:([^\n]*)\n?)?(delete)?'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if match:
        if match.group(1):
            categories = [cat.strip() for cat in match.group(1).split(',')]
        if match.group(2):
            keywords = match.group(2).strip()
        if match.group(3):
            delete_flag = True
    
    return categories, keywords, delete_flag
