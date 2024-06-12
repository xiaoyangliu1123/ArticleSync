import os
from http import server
import re
import xmlrpc.client
from urllib.parse import urlparse
from pathlib import Path
import markdown  
import argparse

# Read MetaWeblog API information from environment variables
cnblogs_url = os.getenv('CNBLOGS_BLOG_URL')
cnblogs_username = os.getenv('CNBLOGS_BLOG_USERNAME')
cnblogs_password = os.getenv('CNBLOGS_BLOG_PASSWORD')
cnblogs_blog_id = os.getenv('CNBLOGS_BLOG_ID')

wordpress_url = os.getenv('WORDPRESS_BLOG_URL')
wordpress_username = os.getenv('WORDPRESS_BLOG_USERNAME')
wordpress_password = os.getenv('WORDPRESS_BLOG_PASSWORD')
wordpress_blog_id = os.getenv('WORDPRESS_BLOG_ID')

cnblogs_server = xmlrpc.client.ServerProxy(cnblogs_url, allow_none=True)
wordpress_server = xmlrpc.client.ServerProxy(wordpress_url, allow_none=True)

def upload_image(image_path, server, blog_id, username, password):
    """Upload image to specified blog and return URL"""
    with open(image_path, 'rb') as img:
        media = {
            'name': Path(image_path).name,
            'type': 'image/jpeg',  # Modify based on your image type
            'bits': xmlrpc.client.Binary(img.read()),
        }
        response = server.metaWeblog.newMediaObject(blog_id, username, password, media)
        return response['url']
    
def get_publish_set_info(content):
    """Extract categories, keywords, and delete flag from the publishSet at the end of the content"""
    categories = []
    keywords = ""
    delete_flag = False
    
    match = re.search(r'# ArticleSync publishSet\n(category:.*\n)?(keywords:.*)(\ndelete:(true|false))?', content, re.DOTALL | re.IGNORECASE)
    if match:
        if match.group(1):
            categories = [cat.strip() for cat in match.group(1).split(':')[1].split(',')]
        if match.group(2):
            keywords = match.group(2).split(':')[1].strip()
        if match.group(3) and match.group(4).strip().lower() == 'true':
            delete_flag = True
    
    return categories, keywords, delete_flag

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

def get_existing_post_id(title, server, blog_id, username, password):
    """Check if a post with the given title already exists and return its ID"""
    recent_posts = server.metaWeblog.getRecentPosts(blog_id, username, password, 100)
    for post in recent_posts:
        if post['title'] == title:
            return post['postid']
    return None

def create_category_if_not_exists_wp(server, blog_id, username, password, category_name):
    """Create a category if it does not exist on WordPress and return its ID"""
    categories = server.wp.getCategories(blog_id, username, password)
    for category in categories:
        if category['categoryName'] == category_name:
            return category['categoryId']
    
    new_category = {
        'name': category_name,
    }
    category_id = server.wp.newCategory(blog_id, username, password, new_category)
    return category_id

def get_category_ids_wp(categories, server, blog_id, username, password):
    """Get or create categories on WordPress and return their IDs"""
    existing_categories = server.wp.getCategories(blog_id, username, password)
    existing_category_dict = {cat['categoryName']: cat['categoryId'] for cat in existing_categories}

    category_ids = []
    for category in categories:
        if category in existing_category_dict:
            category_ids.append(existing_category_dict[category])
        else:
            category_id = create_category_if_not_exists_wp(server, blog_id, username, password, category)
            category_ids.append(category_id)
    return category_ids

def create_category_if_not_exists_cn(server, blog_id, username, password, category_name):
    """Create a category if it does not exist on CNBlogs and return its ID"""
    categories = server.metaWeblog.getCategories(blog_id, username, password)
    for category in categories:
        if category['title'] == category_name:
            return category['categoryid']
    
    new_category = {
        'name': category_name,
    }
    category_id = server.wp.newCategory(blog_id, username, password, new_category)
    return category_id

def get_category_ids_cn(categories, server, blog_id, username, password):
    """Get or create categories on CNBlogs and return their IDs"""
    category_ids = []
    for category in categories:
        category_id = create_category_if_not_exists_cn(server, blog_id, username, password, category)
        category_ids.append(category_id)
    return category_ids

def delete_post_cn(post_id, server, username, password):
    """Delete a post from CNBlogs"""
    result = server.blogger.deletePost('', post_id, username, password, True)
    print(f"Delete post result: {result}")
    return result

def publish_post_cn(markdown_content, title, categories, keywords, delete_flag, server, blog_id, username, password):
    """Publish or update a Markdown document to CNBlogs"""
    existing_post_id = get_existing_post_id(title, server, blog_id, username, password)
    
    if delete_flag:
        if existing_post_id:
            delete_post_cn(existing_post_id, server, username, password)
        return
    
    html_content = markdown.markdown(markdown_content)  # Convert Markdown to HTML
    post = {
        'title': title,
        'description': html_content,
        'categories': categories,  # Ensure we pass category names, not IDs
        'mt_keywords': keywords
    }
    
    if existing_post_id:
        post['postid'] = existing_post_id
        result = server.metaWeblog.editPost(existing_post_id, username, password, post, True)
        return existing_post_id
    else:
        published = server.metaWeblog.newPost(blog_id, username, password, post, True)
        return published

def delete_post_wp(post_id, server, username, password):
    """Delete a post from WordPress"""
    result = server.metaWeblog.deletePost('', post_id, username, password, True)
    print(f"Delete post result: {result}")
    return result

def publish_post_wp(markdown_content, title, categories, keywords, delete_flag, server, blog_id, username, password):
    """Publish or update a Markdown document to WordPress"""
    existing_post_id = get_existing_post_id(title, server, blog_id, username, password)
    
    if delete_flag:
        if existing_post_id:
            delete_post_wp(existing_post_id, server, username, password)
        return
    
    html_content = markdown.markdown(markdown_content)  # Convert Markdown to HTML

    # Prepare the post dictionary
    post = {
        'title': title,
        'description': html_content,
        'categories': categories,  # Pass category names directly
        'mt_keywords': [kw.strip() for kw in keywords.split(',')]  # Convert keywords to a list and strip whitespace
    }
    
    if existing_post_id:
        post['postid'] = existing_post_id
        result = server.metaWeblog.editPost(existing_post_id, username, password, post, True)
        return existing_post_id
    else:
        published = server.metaWeblog.newPost(blog_id, username, password, post, True)
        return published

def main():
    parser = argparse.ArgumentParser(description='Process and publish a markdown file.')
    parser.add_argument('markdown_file', type=str, help='Path to the markdown file to be processed')
    args = parser.parse_args()

    # Extract Markdown file name as the blog post title
    markdown_file_path = Path(args.markdown_file)
    title = markdown_file_path.stem  # Extract the file name without extension

    # Process and publish to CNBlogs
    updated_markdown_cn, categories_cn, keywords_cn, delete_flag_cn = process_markdown(args.markdown_file, cnblogs_server, cnblogs_blog_id, cnblogs_username, cnblogs_password)
    publish_post_cn(updated_markdown_cn, title, categories_cn, keywords_cn, delete_flag_cn, cnblogs_server, cnblogs_blog_id, cnblogs_username, cnblogs_password)
    
    # Process and publish to WordPress
    updated_markdown_wp, categories_wp, keywords_wp, delete_flag_wp = process_markdown(args.markdown_file, wordpress_server, wordpress_blog_id, wordpress_username, wordpress_password)
    publish_post_wp(updated_markdown_wp, title, categories_wp, keywords_wp, delete_flag_wp, wordpress_server, wordpress_blog_id, wordpress_username, wordpress_password)

if __name__ == '__main__':
    main()
