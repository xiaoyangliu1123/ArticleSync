import re
from urllib.parse import urlparse
from pathlib import Path
from publish_set_info import get_publish_set_info
from image_upload import upload_image

def process_markdown(md_path, server, blog_id, username, password):
    """Process Markdown file, upload images, replace URLs, and remove publishSet section"""
    with open(md_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Find all images
    images = re.findall(r'!\[.*?\]\((.*?)\)', content)
    for image_path in images:
        if urlparse(image_path).scheme == '':
            # Only process local images
            new_url = upload_image(image_path, server, blog_id, username, password)
            content = content.replace(image_path, new_url)

    # Extract publishSet information
    categories, keywords, delete_flag = get_publish_set_info(content)

    # Remove publishSet and everything after it
    content = re.sub(r'# ArticleSync publishSet.*', '', content, flags=re.DOTALL)
    
    return content.strip(), categories, keywords, delete_flag
