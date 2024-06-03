import os
import re
import xmlrpc.client
from urllib.parse import urlparse
from pathlib import Path
import markdown
import argparse

# Read MetaWeblog API information from environment variables
url = os.getenv('CNBLOGS_BLOG_URL')
username = os.getenv('CNBLOGS_BLOG_USERNAME')
password = os.getenv('CNBLOGS_BLOG_PASSWORD')
blog_id = os.getenv('CNBLOGS_BLOG_ID')

server = xmlrpc.client.ServerProxy(url)

def upload_image(image_path):
    """Upload image to CNBlogs and return URL"""
    try:
        with open(image_path, 'rb') as img:
            media = {
                'name': Path(image_path).name,
                'type': 'image/jpeg',  # Modify based on your image type
                'bits': xmlrpc.client.Binary(img.read()),
            }
            response = server.metaWeblog.newMediaObject(blog_id, username, password, media)
            print(f"Uploaded image {image_path}, response: {response}")
            return response['url']
    except Exception as e:
        print(f"Failed to upload image {image_path}: {e}")
        return image_path  # Return original path if upload fails

def process_markdown(md_path):
    """Process Markdown file, upload images and replace URLs"""
    try:
        with open(md_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"Failed to read markdown file {md_path}: {e}")
        return ""

    # Find all images
    images = re.findall(r'!\[.*?\]\((.*?)\)', content)
    for image_path in images:
        if urlparse(image_path).scheme == '':
            # Only process local images
            new_url = upload_image(image_path)
            content = content.replace(image_path, new_url)

    return content

def get_post_id_by_title(title):
    """Get the post ID by title"""
    try:
        posts = server.metaWeblog.getRecentPosts(blog_id, username, password, 100)
        for post in posts:
            if post['title'] == title:
                return post['postid']
    except Exception as e:
        print(f"Failed to get post by title {title}: {e}")
    return None

def get_categories():
    """Get existing categories"""
    try:
        categories = server.metaWeblog.getCategories(blog_id, username, password)
        print(f"Retrieved categories: {categories}")
        return {cat['title']: cat['categoryid'] for cat in categories}
    except Exception as e:
        print(f"Failed to get categories: {e}")
        return {}

def create_category_if_not_exists(category, parent_id=0):
    """Create category if it does not exist"""
    existing_categories = get_categories()
    if category not in existing_categories:
        # Create a new category
        new_category = {
            'name': category,
            'parent_id': parent_id,
            'description': category
        }
        try:
            response = server.wp.newCategory(blog_id, username, password, new_category)
            print(f"Created new category: {category} with ID: {response}")
            return response
        except Exception as e:
            print(f"Failed to create category {category}: {e}")
            return None
    return existing_categories[category]

def ensure_categories(categories):
    """Ensure all categories exist, respecting hierarchy"""
    parent_id = 0  # Root level
    for category in categories:
        parent_id = create_category_if_not_exists(category, parent_id)
        if parent_id is None:
            print(f"Skipping category creation for {category} due to error.")
            return False
    return True

def extract_categories_from_path(file_path):
    """Extract categories from file path (max three levels)"""
    parts = Path(file_path).parts
    categories = list(parts[1:min(4, len(parts) - 1)])  # Skip the first part and limit to three levels
    return categories

def publish_post(markdown_content, title, categories):
    """Publish or update Markdown document to CNBlogs"""
    html_content = markdown.markdown(markdown_content)  # Convert Markdown to HTML
    post = {
        'title': title,
        'description': html_content,
        'categories': categories,
    }

    post_id = get_post_id_by_title(title)
    if post_id:
        try:
            published = server.metaWeblog.editPost(post_id, username, password, post, True)
            print(f"Post updated successfully, post ID: {post_id}")
        except Exception as e:
            print(f"Failed to update post {title}: {e}")
    else:
        try:
            published = server.metaWeblog.newPost(blog_id, username, password, post, True)
            print(f"Post published successfully, post ID: {published}")
        except Exception as e:
            print(f"Failed to publish post {title}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Process and publish a markdown file.')
    parser.add_argument('markdown_file', type=str, help='Path to the markdown file to be processed')
    args = parser.parse_args()

    # Ensure the file path is correctly decoded
    markdown_file_path = Path(args.markdown_file.encode('utf-8').decode('unicode_escape'))
    title = markdown_file_path.stem  # Extract the file name without extension
    print(f"Processing file: {markdown_file_path}, extracted title: {title}")

    # Process the Markdown file, upload images and replace URLs
    updated_markdown = process_markdown(markdown_file_path)
    print(f"Processed markdown content: {updated_markdown[:100]}...")  # Print first 100 characters for debugging

    # Extract categories from the file path
    categories = extract_categories_from_path(markdown_file_path)

    # Ensure categories exist
    if not ensure_categories(categories):
        print("Failed to ensure categories exist, aborting post publication.")
        return

    # Publish the post (either create new or update existing)
    publish_post(updated_markdown, title, categories)

if __name__ == '__main__':
    main()
