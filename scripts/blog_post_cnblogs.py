import markdown
from config import cnblogs_server, cnblogs_blog_id, cnblogs_username, cnblogs_password

def get_existing_post_id(title, server, blog_id, username, password):
    """Check if a post with the given title already exists and return its ID"""
    recent_posts = server.metaWeblog.getRecentPosts(blog_id, username, password, 100)
    for post in recent_posts:
        if post['title'] == title:
            return post['postid']
    return None

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
    print(f"CNBlogs Delete post result: {result}")
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
