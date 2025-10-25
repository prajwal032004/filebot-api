from flask import Flask, render_template, request, jsonify, session
import requests
import os
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

BASE_URL = "https://imageapi.pythonanywhere.com"

def get_all_folders(api_key):
    """Fetch all folders"""
    try:
        response = requests.get(f"{BASE_URL}/api/folders", headers={"X-API-Key": api_key})
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    except Exception as e:
        print(f"Error fetching folders: {e}")
        return []

def get_folder_by_name(folder_name, api_key):
    """Get folder by name (case insensitive)"""
    folders = get_all_folders(api_key)
    for folder in folders:
        if folder['name'].lower() == folder_name.lower():
            return folder
    return None

def get_folder_by_id(folder_id, api_key):
    """Get specific folder details"""
    try:
        response = requests.get(f"{BASE_URL}/api/folder/{folder_id}", headers={"X-API-Key": api_key})
        if response.status_code == 200:
            return response.json().get('data', None)
        return None
    except Exception as e:
        print(f"Error fetching folder: {e}")
        return None

def get_all_images(api_key):
    """Fetch all images from all folders"""
    try:
        folders = get_all_folders(api_key)
        all_images = []
        for folder in folders:
            images_response = requests.get(f"{BASE_URL}/api/folder/{folder['id']}/images", headers={"X-API-Key": api_key})
            if images_response.status_code == 200:
                images = images_response.json().get('data', [])
                for img in images:
                    img['folder_name'] = folder['name']
                    img['folder_id'] = folder['id']
                all_images.extend(images)
        return all_images
    except Exception as e:
        print(f"Error fetching images: {e}")
        return []

def get_images_from_folder(folder_id, api_key):
    """Get images from specific folder"""
    try:
        response = requests.get(f"{BASE_URL}/api/folder/{folder_id}/images", headers={"X-API-Key": api_key})
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    except Exception as e:
        print(f"Error fetching images: {e}")
        return []

def get_all_pdfs(api_key):
    """Fetch all PDFs from all folders"""
    try:
        folders = get_all_folders(api_key)
        all_pdfs = []
        for folder in folders:
            pdfs_response = requests.get(f"{BASE_URL}/api/folder/{folder['id']}/pdfs", headers={"X-API-Key": api_key})
            if pdfs_response.status_code == 200:
                pdfs = pdfs_response.json().get('data', [])
                for pdf in pdfs:
                    pdf['folder_name'] = folder['name']
                    pdf['folder_id'] = folder['id']
                all_pdfs.extend(pdfs)
        return all_pdfs
    except Exception as e:
        print(f"Error fetching PDFs: {e}")
        return []

def get_pdfs_from_folder(folder_id, api_key):
    """Get PDFs from specific folder"""
    try:
        response = requests.get(f"{BASE_URL}/api/folder/{folder_id}/pdfs", headers={"X-API-Key": api_key})
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    except Exception as e:
        print(f"Error fetching PDFs: {e}")
        return []

def search_images(query, api_key):
    """Search images by name or description"""
    try:
        response = requests.get(f"{BASE_URL}/api/search", params={"q": query}, headers={"X-API-Key": api_key})
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    except Exception as e:
        print(f"Error searching: {e}")
        return []

def get_image_by_id(image_id, api_key):
    """Get specific image details"""
    try:
        response = requests.get(f"{BASE_URL}/api/image/{image_id}", headers={"X-API-Key": api_key})
        if response.status_code == 200:
            return response.json().get('data', None)
        return None
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None

def extract_pdf_text(pdf_id, api_key):
    """Extract text from PDF"""
    try:
        response = requests.get(f"{BASE_URL}/api/pdf/{pdf_id}/text", headers={"X-API-Key": api_key})
        if response.status_code == 200:
            return response.json().get('data', {}).get('text', '')
        return None
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

def count_items(api_key):
    """Count total images and PDFs"""
    images = get_all_images(api_key)
    pdfs = get_all_pdfs(api_key)
    folders = get_all_folders(api_key)
    return {
        'images': len(images),
        'pdfs': len(pdfs),
        'folders': len(folders),
        'total': len(images) + len(pdfs)
    }

def filter_by_description(items, keyword):
    """Filter items by description containing keyword"""
    filtered = []
    keyword_lower = keyword.lower()
    for item in items:
        desc = item.get('description', '').lower()
        if keyword_lower in desc:
            filtered.append(item)
    return filtered

def filter_by_filename(items, keyword):
    """Filter items by filename containing keyword"""
    filtered = []
    keyword_lower = keyword.lower()
    for item in items:
        filename = item.get('filename', '').lower()
        if keyword_lower in filename:
            filtered.append(item)
    return filtered

def get_recent_items(items, limit=10):
    """Get most recent items"""
    sorted_items = sorted(items, key=lambda x: x.get('uploaded_at', ''), reverse=True)
    return sorted_items[:limit]

def process_message(message, api_key):
    """Process user message and return appropriate response"""
    message_lower = message.lower().strip()

    # Greetings
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']):
        return {
            'type': 'text',
            'message': """Hello! I'm your Image Assistant. I can help you find images and PDFs. Try asking me:
• Show all images
• Find images about [topic]
• Show PDFs
• List folders
• Search for [name]"""
        }

    # Show all folders
    if any(phrase in message_lower for phrase in ['show folders', 'list folders', 'all folders', 'show all folders', 'display folders', 'what folders', 'my folders', 'view folders', 'get folders', 'folders list']):
        folders = get_all_folders(api_key)
        if folders:
            folder_list = '\n'.join([f"📁 {f['name']} ({f['file_count']} files)" for f in folders])
            return {
                'type': 'text',
                'message': f"You have {len(folders)} folders:\n\n{folder_list}\n\nTo view a folder's contents, ask 'Show folder [name]'"
            }
        return {'type': 'text', 'message': 'No folders found in your collection.'}

    # Show specific folder
    folder_patterns = [
        r'show .* folder',
        r'display .* folder',
        r'view .* folder',
        r'open .* folder',
        r'show folder (.*)',
        r'(.*) folder images',
        r'(.*) folder contents',
        r'files in (.*) folder',
        r'what.*in (.*) folder',
        r'show me (.*) folder',
        r'list (.*) folder',
        r'get (.*) folder',
        r'(.*) folder files',
        r'see (.*) folder',
        r'browse (.*) folder'
    ]

    for pattern in folder_patterns:
        match = re.search(pattern, message_lower)
        if match:
            folder_name = match.group(1).strip()
            folder = get_folder_by_name(folder_name, api_key)
            if folder:
                folder_details = get_folder_by_id(folder['id'], api_key)
                if folder_details:
                    files = folder_details.get('files', [])
                    images = [f for f in files if f['file_type'].lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp']]
                    pdfs = [f for f in files if f['file_type'].lower() == 'pdf']

                    response = {
                        'type': 'mixed',
                        'message': f"📁 {folder['name']} contains {len(files)} files:",
                        'images': [],
                        'pdfs': []
                    }

                    if images:
                        for img in images:
                            img['folder_name'] = folder['name']
                        response['images'] = images

                    if pdfs:
                        for pdf in pdfs:
                            pdf['folder_name'] = folder['name']
                        response['pdfs'] = pdfs

                    return response

            return {'type': 'text', 'message': f"Sorry, I couldn't find a folder named '{folder_name}'. Use 'show folders' to see all available folders."}

    # Show all images
    if any(phrase in message_lower for phrase in ['show all images', 'all images', 'list images', 'display images', 'show images', 'view all images', 'get all images', 'my images', 'show me images', 'display all images']):
        images = get_all_images(api_key)
        if images:
            return {
                'type': 'images',
                'message': f"🖼️ I found {len(images)} images in your collection:",
                'data': images
            }
        return {'type': 'text', 'message': 'No images found in your collection.'}

    # Show PDFs
    if any(phrase in message_lower for phrase in ['show pdfs', 'all pdfs', 'list pdfs', 'display pdfs', 'show documents', 'all documents', 'list documents', 'my pdfs', 'view pdfs', 'get pdfs']):
        pdfs = get_all_pdfs(api_key)
        if pdfs:
            return {
                'type': 'pdfs',
                'message': f"📄 I found {len(pdfs)} PDF documents:",
                'data': pdfs
            }
        return {'type': 'text', 'message': 'No PDFs found in your collection.'}

    # Count/Statistics
    if any(phrase in message_lower for phrase in ['how many', 'count', 'total', 'statistics', 'stats', 'number of', 'how much', 'quantity', 'amount', 'summary']):
        counts = count_items(api_key)
        return {
            'type': 'text',
            'message': f"""📊 Your Collection Summary:
📁 Folders: {counts['folders']}
🖼️ Images: {counts['images']}
📄 PDFs: {counts['pdfs']}
📦 Total Files: {counts['total']}"""
        }

    # Recent items
    if any(phrase in message_lower for phrase in ['recent', 'latest', 'newest', 'new', 'last', 'most recent']):
        if 'pdf' in message_lower or 'document' in message_lower:
            pdfs = get_all_pdfs(api_key)
            recent = get_recent_items(pdfs, 5)
            if recent:
                return {
                    'type': 'pdfs',
                    'message': f"📄 Here are your {len(recent)} most recent PDFs:",
                    'data': recent
                }
        else:
            images = get_all_images(api_key)
            recent = get_recent_items(images, 5)
            if recent:
                return {
                    'type': 'images',
                    'message': f"🖼️ Here are your {len(recent)} most recent images:",
                    'data': recent
                }
        return {'type': 'text', 'message': 'No recent items found.'}

    # Search by description
    desc_patterns = [
        r'with description (.*)',
        r'description (.*)',
        r'described as (.*)',
        r'with desc (.*)',
        r'description contains (.*)',
        r'desc (.*)',
        r'having description (.*)',
        r'description is (.*)',
        r'desc is (.*)',
        r'description has (.*)'
    ]

    for pattern in desc_patterns:
        match = re.search(pattern, message_lower)
        if match:
            keyword = match.group(1).strip()
            images = get_all_images(api_key)
            filtered = filter_by_description(images, keyword)
            if filtered:
                return {
                    'type': 'images',
                    'message': f"🔍 Found {len(filtered)} images with description containing '{keyword}':",
                    'data': filtered
                }
            return {'type': 'text', 'message': f"No images found with description containing '{keyword}'."}

    # Search by filename
    filename_patterns = [
        r'named (.*)',
        r'filename (.*)',
        r'file called (.*)',
        r'file named (.*)',
        r'with name (.*)',
        r'name contains (.*)',
        r'name is (.*)',
        r'called (.*)',
        r'file name (.*)',
        r'with filename (.*)'
    ]

    for pattern in filename_patterns:
        match = re.search(pattern, message_lower)
        if match:
            keyword = match.group(1).strip()
            images = get_all_images(api_key)
            filtered = filter_by_filename(images, keyword)
            if filtered:
                return {
                    'type': 'images',
                    'message': f"🔍 Found {len(filtered)} images with filename containing '{keyword}':",
                    'data': filtered
                }
            return {'type': 'text', 'message': f"No images found with filename containing '{keyword}'."}

    # General search
    if any(word in message_lower for word in ['find', 'search', 'look for', 'looking for', 'get', 'show me', 'locate', 'discover', 'fetch']):
        search_terms = message_lower
        for word in ['find', 'search', 'show me', 'show', 'get', 'look for', 'looking for', 'images about', 'images of', 'pictures of', 'locate', 'discover', 'fetch', 'for']:
            search_terms = search_terms.replace(word, '').strip()

        if search_terms:
            results = search_images(search_terms, api_key)
            if results:
                return {
                    'type': 'images',
                    'message': f"🔍 I found {len(results)} results for '{search_terms}':",
                    'data': results
                }
            return {'type': 'text', 'message': f"Sorry, I couldn't find any images matching '{search_terms}'. Try a different search term!"}

    # Help
    if any(word in message_lower for word in ['help', 'commands', 'what can you do', 'capabilities', 'options']):
        return {
            'type': 'text',
            'message': """Here's what I can do:

📁 Folders:
• "Show all folders" - List all folders
• "Show folder [name]" - View specific folder

🖼️ Images:
• "Show all images" - Display all images
• "Find [keyword]" - Search images
• "Recent images" - Show latest images
• "Images with description [keyword]"

📄 PDFs:
• "Show PDFs" - Display all PDFs
• "Recent PDFs" - Show latest PDFs

🔍 Search:
• "Search for [keyword]" - Search everything
• "Named [filename]" - Find by filename
• "Description contains [keyword]" - Find by description

📊 Statistics:
• "How many" - Show collection stats
• "Count" - Show totals

Just ask me naturally and I'll help you find what you need!"""
        }

    # Thank you
    if any(phrase in message_lower for phrase in ['thank', 'thanks', 'appreciate']):
        return {
            'type': 'text',
            'message': "You're welcome! Feel free to ask me anything else!"
        }

    # Goodbye
    if any(word in message_lower for word in ['bye', 'goodbye', 'see you']):
        return {
            'type': 'text',
            'message': 'Goodbye! Come back anytime you need help with your images and PDFs!'
        }

    # Default: try to search with the entire message
    results = search_images(message, api_key)
    if results:
        return {
            'type': 'images',
            'message': f"🔍 I found {len(results)} results for your query:",
            'data': results
        }

    # If nothing matches, provide helpful suggestions
    return {
        'type': 'text',
        'message': """I'm not sure what you're looking for. Try:
• "Show all images"
• "Show folders"
• "Find [keyword]"
• "Recent images"
• "Help" for more options"""
    }

@app.route('/')
def index():
    return render_template('setup.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    api_key = data.get('api_key', '')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    if not api_key:
        return jsonify({'error': 'API key required'}), 401

    response = process_message(user_message, api_key)

    # Handle mixed type (both images and PDFs)
    if response.get('type') == 'mixed':
        return jsonify({
            'type': 'mixed',
            'message': response['message'],
            'images': response.get('images', []),
            'pdfs': response.get('pdfs', [])
        })

    return jsonify(response)

@app.route('/verify-api-key', methods=['POST'])
def verify_api_key():
    """Verify if the API key is valid"""
    data = request.json
    api_key = data.get('api_key', '')
    
    if not api_key:
        return jsonify({'valid': False, 'message': 'API key is required'}), 400
    
    try:
        # Test the API key by fetching folders
        response = requests.get(f"{BASE_URL}/api/folders", headers={"X-API-Key": api_key})
        if response.status_code == 200:
            return jsonify({'valid': True, 'message': 'API key is valid'})
        else:
            return jsonify({'valid': False, 'message': 'Invalid API key'}), 401
    except Exception as e:
        return jsonify({'valid': False, 'message': 'Error verifying API key'}), 500

if __name__ == '__main__':
    app.run(debug=True)