from pathlib import Path
import xmlrpc.client

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
