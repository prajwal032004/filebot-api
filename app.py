from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from functools import wraps
import os
import secrets
import json
from PIL import Image
import PyPDF2
import io
import zipfile
from flask import session, abort
from sqlalchemy import func, desc
import csv
from io import StringIO


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # This silences the warning
)



# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    folders = db.relationship('Folder', backref='owner', lazy=True, cascade='all, delete-orphan')

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'


class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    files = db.relationship('File', backref='folder', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Folder {self.name}>'


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, default='')
    metadata_json = db.Column(db.Text, default='{}')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<File {self.filename}>'



class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action}>'

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_api_key():
    return secrets.token_urlsafe(48)


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'status': 'error', 'message': 'API key is missing'}), 401

        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401

        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def get_file_size(filepath):
    size_bytes = os.path.getsize(filepath)
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f}MB"


def get_image_dimensions(filepath):
    try:
        with Image.open(filepath) as img:
            return f"{img.width}x{img.height}"
    except:
        return "N/A"


def extract_pdf_text(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except:
        return ""

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        api_key = generate_api_key()

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            api_key=api_key
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_folders = Folder.query.filter_by(user_id=current_user.id).count()
    total_files = db.session.query(File).join(Folder).filter(Folder.user_id == current_user.id).count()
    return render_template('dashboard.html', total_folders=total_folders, total_files=total_files)


@app.route('/folders')
@login_required
def folders():
    user_folders = Folder.query.filter_by(user_id=current_user.id).all()
    return render_template('folders.html', folders=user_folders)


@app.route('/folder/create', methods=['POST'])
@login_required
def create_folder():
    folder_name = request.form.get('folder_name')
    is_public = request.form.get('is_public') == 'on'

    new_folder = Folder(
        user_id=current_user.id,
        name=folder_name,
        is_public=is_public
    )

    db.session.add(new_folder)
    db.session.commit()

    flash('Folder created successfully!', 'success')
    return redirect(url_for('folders'))


@app.route('/folder/<int:folder_id>')
@login_required
def folder_detail(folder_id):
    folder = Folder.query.get_or_404(folder_id)

    if folder.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('folders'))

    return render_template('folder_detail.html', folder=folder)


@app.route('/folder/<int:folder_id>/upload', methods=['POST'])
@login_required
def upload_file(folder_id):
    folder = Folder.query.get_or_404(folder_id)

    if folder.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400

    file = request.files['file']
    description = request.form.get('description', '')

    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"

        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)

        filepath = os.path.join(user_folder, unique_filename)
        file.save(filepath)

        relative_path = f"{current_user.id}/{unique_filename}"

        file_type = filename.rsplit('.', 1)[1].lower()

        metadata = {
            'file_size': get_file_size(filepath),
            'uploaded_at': datetime.now().isoformat()
        }

        if file_type in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            metadata['dimensions'] = get_image_dimensions(filepath)
        elif file_type == 'pdf':
            try:
                with open(filepath, 'rb') as pdf_file:
                    reader = PyPDF2.PdfReader(pdf_file)
                    metadata['page_count'] = len(reader.pages)
            except:
                metadata['page_count'] = 0

        new_file = File(
            folder_id=folder_id,
            filename=filename,
            file_type=file_type,
            file_path=relative_path,
            description=description,
            metadata_json=json.dumps(metadata)
        )

        db.session.add(new_file)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully',
            'data': {
                'id': new_file.id,
                'filename': new_file.filename,
                'url': url_for('static', filename=f'uploads/{relative_path}', _external=True)
            }
        })

    return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400


@app.route('/folder/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)

    if folder.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('folders'))

    db.session.delete(folder)
    db.session.commit()

    flash('Folder deleted successfully!', 'success')
    return redirect(url_for('folders'))


@app.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    folder = Folder.query.get(file.folder_id)

    if folder.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    try:
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], file.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        print(f"Error deleting file: {e}")

    db.session.delete(file)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'File deleted successfully'})

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/settings/regenerate-key', methods=['POST'])
@login_required
def regenerate_key():
    current_user.api_key = generate_api_key()
    db.session.commit()
    flash('API key regenerated successfully!', 'success')
    return redirect(url_for('settings'))


@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/api')
def api_info():
    return jsonify({
        'name': 'Image API',
        'version': '1.0.0',
        'endpoints': {
            'folders': '/api/folders',
            'search': '/api/search',
            'images': '/api/folder/{id}/images',
            'pdfs': '/api/folder/{id}/pdfs'
        }
    })

@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per hour")
def api_register():
    data = request.get_json()

    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'status': 'error', 'message': 'Username already exists'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'status': 'error', 'message': 'Email already registered'}), 400

    hashed_password = generate_password_hash(data['password'])
    api_key = generate_api_key()

    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        api_key=api_key
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'User registered successfully',
        'data': {'api_key': api_key}
    }), 201


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per hour")
def api_login():
    data = request.get_json()

    if not data or not all(k in data for k in ['email', 'password']):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({
            'status': 'success',
            'data': {
                'api_key': user.api_key,
                'username': user.username
            }
        })

    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401


@app.route('/api/folders', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def api_get_folders():
    folders = Folder.query.filter_by(user_id=request.current_user.id).all()

    return jsonify({
        'status': 'success',
        'data': [{
            'id': folder.id,
            'name': folder.name,
            'created_at': folder.created_at.isoformat(),
            'is_public': folder.is_public,
            'file_count': len(folder.files)
        } for folder in folders]
    })


@app.route('/api/folder/<int:folder_id>', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def api_get_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)

    if folder.user_id != request.current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    return jsonify({
        'status': 'success',
        'data': {
            'id': folder.id,
            'name': folder.name,
            'created_at': folder.created_at.isoformat(),
            'is_public': folder.is_public,
            'files': [{
                'id': f.id,
                'filename': f.filename,
                'file_type': f.file_type,
                'description': f.description,
                'uploaded_at': f.uploaded_at.isoformat()
            } for f in folder.files]
        }
    })


@app.route('/api/folder/<int:folder_id>/images', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def api_get_folder_images(folder_id):
    folder = Folder.query.get_or_404(folder_id)

    if folder.user_id != request.current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    images = [f for f in folder.files if f.file_type in ['png', 'jpg', 'jpeg', 'gif', 'webp']]

    return jsonify({
        'status': 'success',
        'data': [{
            'id': img.id,
            'filename': img.filename,
            'url': url_for('static', filename=f'uploads/{img.file_path}', _external=True),
            'description': img.description,
            'metadata': json.loads(img.metadata_json)
        } for img in images]
    })


@app.route('/api/folder/<int:folder_id>/pdfs', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def api_get_folder_pdfs(folder_id):
    folder = Folder.query.get_or_404(folder_id)

    if folder.user_id != request.current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    pdfs = [f for f in folder.files if f.file_type == 'pdf']

    return jsonify({
        'status': 'success',
        'data': [{
            'id': pdf.id,
            'filename': pdf.filename,
            'url': url_for('static', filename=f'uploads/{pdf.file_path}', _external=True),
            'description': pdf.description,
            'metadata': json.loads(pdf.metadata_json)
        } for pdf in pdfs]
    })


@app.route('/api/image/<int:image_id>', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def api_get_image(image_id):
    file = File.query.get_or_404(image_id)
    folder = Folder.query.get(file.folder_id)

    if folder.user_id != request.current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    return jsonify({
        'status': 'success',
        'data': {
            'id': file.id,
            'name': file.filename,
            'url': url_for('static', filename=f'uploads/{file.file_path}', _external=True),
            'description': file.description,
            'metadata': json.loads(file.metadata_json)
        }
    })


@app.route('/api/pdf/<int:pdf_id>', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def api_get_pdf(pdf_id):
    file = File.query.get_or_404(pdf_id)
    folder = Folder.query.get(file.folder_id)

    if folder.user_id != request.current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    return jsonify({
        'status': 'success',
        'data': {
            'id': file.id,
            'name': file.filename,
            'url': url_for('static', filename=f'uploads/{file.file_path}', _external=True),
            'description': file.description,
            'metadata': json.loads(file.metadata_json)
        }
    })


@app.route('/api/pdf/<int:pdf_id>/text', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def api_get_pdf_text(pdf_id):
    file = File.query.get_or_404(pdf_id)
    folder = Folder.query.get(file.folder_id)

    if folder.user_id != request.current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    full_path = os.path.join(app.config['UPLOAD_FOLDER'], file.file_path)
    text = extract_pdf_text(full_path)

    return jsonify({
        'status': 'success',
        'data': {
            'id': file.id,
            'filename': file.filename,
            'text': text
        }
    })


@app.route('/api/search', methods=['GET'])
@limiter.limit("100 per hour")
@require_api_key
def api_search():
    query = request.args.get('q', '')

    if not query:
        return jsonify({'status': 'error', 'message': 'Search query is required'}), 400

    user_folders = Folder.query.filter_by(user_id=request.current_user.id).all()
    folder_ids = [f.id for f in user_folders]

    files = File.query.filter(
        File.folder_id.in_(folder_ids),
        db.or_(
            File.filename.contains(query),
            File.description.contains(query)
        )
    ).all()

    return jsonify({
        'status': 'success',
        'data': [{
            'id': f.id,
            'filename': f.filename,
            'file_type': f.file_type,
            'description': f.description,
            'url': url_for('static', filename=f'uploads/{f.file_path}', _external=True)
        } for f in files]
    })


@app.route('/api/refresh-key', methods=['POST'])
@limiter.limit("3 per hour")
@require_api_key
def api_refresh_key():
    new_key = generate_api_key()
    request.current_user.api_key = new_key
    db.session.commit()

    return jsonify({
        'status': 'success',
        'data': {'api_key': new_key}
    })

@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')

@app.errorhandler(400)
def bad_request_error(e):
    if request.path.startswith("/api/"):
        return jsonify({'status': 'error', 'message': 'Bad Request'}), 400
    flash('Bad request. Please check your input.', 'error')
    return render_template('error.html', code=400, message='Bad Request'), 400


@app.errorhandler(401)
def unauthorized_error(e):
    if request.path.startswith("/api/"):
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 401
    flash('You must be logged in to access this page.', 'error')
    return redirect(url_for('login'))


@app.errorhandler(403)
def forbidden_error(e):
    if request.path.startswith("/api/"):
        return jsonify({'status': 'error', 'message': 'Access forbidden'}), 403
    flash('Access denied. You do not have permission to view this page.', 'error')
    return render_template('error.html', code=403, message='Forbidden'), 403


@app.errorhandler(404)
def not_found_error(e):
    if request.path.startswith("/api/"):
        return jsonify({'status': 'error', 'message': 'Resource not found'}), 404
    return render_template('error.html', code=404, message='Page Not Found'), 404


@app.errorhandler(413)
def file_too_large_error(e):
    if request.path.startswith("/api/"):
        return jsonify({'status': 'error', 'message': 'File too large (max 10MB)'}), 413
    flash('File too large! Maximum size is 10MB.', 'error')
    return redirect(request.referrer or url_for('dashboard'))


@app.errorhandler(429)
def rate_limit_error(e):
    if request.path.startswith("/api/"):
        return jsonify({'status': 'error', 'message': 'Rate limit exceeded. Try again later.'}), 429
    flash('You are sending too many requests. Please slow down.', 'error')
    return render_template('error.html', code=429, message='Too Many Requests'), 429


@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"Internal Server Error: {e}")
    if request.path.startswith("/api/"):
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    return render_template('error.html', code=500, message='Internal Server Error'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)