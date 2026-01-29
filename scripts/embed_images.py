import base64
import re

def embed_images_in_html():
    with open('apresentacao_ministerio.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    image_pattern = r'src="(attached_assets/[^"]+)"'
    matches = re.findall(image_pattern, html_content)
    
    for image_path in set(matches):
        try:
            with open(image_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            ext = image_path.split('.')[-1].lower()
            mime_type = 'image/png' if ext == 'png' else 'image/jpeg'
            
            data_uri = f'data:{mime_type};base64,{img_data}'
            html_content = html_content.replace(f'src="{image_path}"', f'src="{data_uri}"')
            print(f"Embedded: {image_path}")
        except FileNotFoundError:
            print(f"Not found: {image_path}")
    
    with open('apresentacao_ministerio_offline.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\nSalvo: apresentacao_ministerio_offline.html")

if __name__ == '__main__':
    embed_images_in_html()
