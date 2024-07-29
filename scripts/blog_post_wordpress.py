import markdown
from config import wordpress_server, wordpress_blog_id, wordpress_username, wordpress_password

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

def delete_post_wp(post_id, server, username, password):
    """Delete a post from WordPress"""
    result = server.metaWeblog.deletePost('', post_id, username, password, True)
    print(f"Wordpress Delete post result: {result}")
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
