import os
import xmlrpc.client

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
