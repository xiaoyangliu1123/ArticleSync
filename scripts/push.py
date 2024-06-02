import os
from http import server
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

# Debug information to ensure variables are correctly read
print(f'URL: {url}')
print(f'Username: {username}')
print(f'Blog ID: {blog_id}')

# Ensure the URL is valid
if not url.startswith(('http://', 'https://')):
    raise ValueError("URL must start with 'http://' or 'https://'")

server = xmlrpc.client.ServerProxy(url)

def upload_image(image_path):
    """Upload image to CNBlogs and return URL"""
    with open(image_path, 'rb') as img:
        media = {
            'name': Path(image_path).name,
            'type': 'image/jpeg',  # Modify based on your image type
            'bits': xmlrpc.client.Binary(img.read()),
        }
        response = server.metaWeblog.newMediaObject(blog_id, username, password, media)
        return response['url']

def process_markdown(md_path):
    """Process Markdown file, upload images and replace URLs"""
    with open(md_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Find all images
    images = re.findall(r'!\[.*?\]\((.*?)\)', content)
    for image_path in images:
        if urlparse(image_path).scheme == '':
            # Only process local images
            new_url = upload_image(image_path)
            content = content.replace(image_path, new_url)

    return content

def publish_post(markdown_content, title, categories):
    """Publish Markdown document to CNBlogs"""
    html_content = markdown.markdown(markdown_content)  # Convert Markdown to HTML
    post = {
        'title': title,
        'description': html_content,
        'categories': categories,
    }
    published = server.metaWeblog.newPost(blog_id, username, password, post, True)
    return published

def main():
    parser = argparse.ArgumentParser(description='Process and publish a markdown file.')
    parser.add_argument('markdown_file', type=str, help='Path to the markdown file to be processed')
    args = parser.parse_args()

    # Extract Markdown file name as the blog post title
    markdown_file_path = Path(args.markdown_file)
    title = markdown_file_path.stem  # Extract the file name without extension

    # Process the Markdown file, upload images and replace URLs
    updated_markdown = process_markdown(args.markdown_file)

    # Set the categories of the post (adjust as needed)
    categories = ["Markdown", "Tutorial"]

    # Publish the post
    post_id = publish_post(updated_markdown, title, categories)
    print(f"Post published successfully, post ID: {post_id}")

if __name__ == '__main__':
    main()
