import argparse
from pathlib import Path
from config import cnblogs_server, cnblogs_blog_id, cnblogs_username, cnblogs_password
from config import wordpress_server, wordpress_blog_id, wordpress_username, wordpress_password
from markdown_processing import process_markdown
from blog_post_cnblogs import publish_post_cn
from blog_post_wordpress import publish_post_wp

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
