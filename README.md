# 🖼️ Image & PDF Management System with AI Chatbot

A comprehensive Flask-based file management system with RESTful API and an intelligent chatbot interface for seamless interaction with your media library.

[![Live Demo - Main App](https://img.shields.io/badge/Live%20Demo-Main%20App-blue?style=for-the-badge)](https://imageapi.pythonanywhere.com/)
[![Live Demo - Chatbot](https://img.shields.io/badge/Live%20Demo-Chatbot-green?style=for-the-badge)](https://apifetch.pythonanywhere.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-black?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Chatbot Commands](#chatbot-commands)
- [Screenshots](#screenshots)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

This project consists of two main components:

1. **Main Application (`app.py`)** - A complete file management system with user authentication, folder organization, and RESTful API
2. **AI Chatbot (`chatbot.py`)** - An intelligent conversational interface for querying and managing your files using natural language

### Live Demos

- **Main App**: [https://imageapi.pythonanywhere.com/](https://imageapi.pythonanywhere.com/)
- **Chatbot**: [https://apifetch.pythonanywhere.com/](https://apifetch.pythonanywhere.com/)

## ✨ Features

### Main Application Features

#### 🔐 User Management

- Secure user registration and authentication
- Password hashing with Werkzeug
- Unique API key generation for each user
- Session management with Flask-Login

#### 📁 Folder & File Organization

- Create and manage multiple folders
- Public/private folder visibility
- File upload with automatic metadata extraction
- Support for images (PNG, JPG, JPEG, GIF, WEBP) and PDFs
- File size: up to 10MB per file

#### 🔍 Advanced Search

- Search files by name or description
- Filter by file type
- Cross-folder search capabilities

#### 📊 Metadata Extraction

- **Images**: Dimensions, file size, upload date
- **PDFs**: Page count, file size, text extraction

#### 🛡️ Security Features

- Rate limiting on API endpoints
- CSRF protection
- Secure file upload with filename sanitization
- API key authentication

#### 📱 RESTful API

- Complete CRUD operations
- JSON responses
- Comprehensive error handling
- Rate-limited endpoints (100 requests/hour)

### Chatbot Features

#### 💬 Natural Language Interface

- Conversational AI for file management
- Context-aware responses
- Multiple query patterns support

#### 🎯 Smart Commands

- List all folders and files
- Search by keywords
- Filter by descriptions
- View recent uploads
- Get collection statistics
- Browse specific folders

#### 🔄 Real-time Integration

- Direct API integration with main app
- Live data fetching
- Instant search results

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│  (Web Dashboard + Chatbot Interface)                    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                  Flask Application                       │
│  ┌──────────────────┐      ┌──────────────────┐       │
│  │   app.py         │      │   chatbot.py     │       │
│  │   (Main API)     │◄─────┤   (AI Interface) │       │
│  └──────────────────┘      └──────────────────┘       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Database Layer (SQLite)                     │
│  • Users  • Folders  • Files  • Activity Logs           │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/prajwal032004/image-pdf-management-system.git
cd image-pdf-management-system
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database

```bash
python init_db.py
```

### Step 5: Run the Applications

**Main Application:**

```bash
python app.py
```

Access at: `http://localhost:5000`

**Chatbot (in a separate terminal):**

```bash
python chatbot.py
```

Access at: `http://localhost:5000`

## 📦 Requirements

Create a `requirements.txt` file with:

```txt
Flask==2.3.0
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Flask-Limiter==3.3.1
Werkzeug==2.3.0
Pillow==10.0.0
PyPDF2==3.0.1
requests==2.31.0
```

## 📖 Usage

### Main Application Workflow

1. **Register an Account**

   - Navigate to `/register`
   - Create username, email, and password
   - Receive unique API key

2. **Login**

   - Use your credentials at `/login`
   - Access dashboard

3. **Create Folders**

   - Organize files into folders
   - Set public/private visibility

4. **Upload Files**

   - Drag & drop or browse files
   - Add descriptions for better search
   - Automatic metadata extraction

5. **Search & Manage**
   - Use search bar for quick access
   - View file details and metadata
   - Download or delete files

### Chatbot Usage

1. **Setup API Key**

   - Get your API key from main app settings
   - Enter in chatbot setup page
   - Start chatting!

2. **Example Conversations**

   ```
   You: Show all my images
   Bot: 🖼️ I found 45 images in your collection

   You: Find vacation photos
   Bot: 🔍 I found 12 results for 'vacation'

   You: Show folder "Work Documents"
   Bot: 📁 Work Documents contains 23 files

   You: Recent PDFs
   Bot: 📄 Here are your 5 most recent PDFs
   ```

## 🔌 API Documentation

### Authentication

All API requests require an API key in the header:

```
X-API-Key: your_api_key_here
```

### Endpoints

#### User Registration

```http
POST /api/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password"
}
```

#### Login

```http
POST /api/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "secure_password"
}
```

#### Get All Folders

```http
GET /api/folders
X-API-Key: your_api_key
```

#### Get Folder Details

```http
GET /api/folder/{folder_id}
X-API-Key: your_api_key
```

#### Get Images from Folder

```http
GET /api/folder/{folder_id}/images
X-API-Key: your_api_key
```

#### Get PDFs from Folder

```http
GET /api/folder/{folder_id}/pdfs
X-API-Key: your_api_key
```

#### Search Files

```http
GET /api/search?q=keyword
X-API-Key: your_api_key
```

#### Extract PDF Text

```http
GET /api/pdf/{pdf_id}/text
X-API-Key: your_api_key
```

#### Refresh API Key

```http
POST /api/refresh-key
X-API-Key: your_current_api_key
```

### Response Format

```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {
    // Response data
  }
}
```

## 🤖 Chatbot Commands

### Folder Commands

- `show folders` - List all folders
- `show folder [name]` - View specific folder contents
- `list folders` - Display folder list

### Image Commands

- `show all images` - Display all images
- `recent images` - Show latest images
- `find [keyword]` - Search images
- `images with description [keyword]` - Filter by description
- `named [filename]` - Find by filename

### PDF Commands

- `show pdfs` - Display all PDFs
- `recent pdfs` - Show latest PDFs
- `all documents` - List all documents

### Search Commands

- `search for [keyword]` - Global search
- `find [anything]` - Smart search
- `look for [term]` - Natural language search

### Statistics

- `how many` - Show collection stats
- `count` - Display totals
- `statistics` - Get summary

### Help

- `help` - Show all commands
- `what can you do` - List capabilities

## 📸 Screenshots

### Main Application Dashboard

![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Screenshot)

### Folder Management

![Folders](https://via.placeholder.com/800x400?text=Folder+Management)

### Chatbot Interface

![Chatbot](https://via.placeholder.com/800x400?text=Chatbot+Interface)

## 🛠️ Technologies Used

### Backend

- **Flask** - Web framework
- **SQLAlchemy** - ORM for database management
- **Flask-Login** - User session management
- **Flask-Limiter** - Rate limiting
- **Werkzeug** - Security utilities

### File Processing

- **Pillow** - Image processing and metadata extraction
- **PyPDF2** - PDF text extraction and page counting

### Database

- **SQLite** - Lightweight database

### Frontend

- **HTML5/CSS3** - Modern web standards
- **JavaScript** - Interactive features
- **Bootstrap** (assumed) - Responsive design

## 📁 Project Structure

```
image-pdf-management-system/
│
├── app.py                 # Main application
├── chatbot.py            # Chatbot interface
├── init_db.py            # Database initialization
├── requirements.txt      # Python dependencies
│
├── templates/            # HTML templates
│   ├── index.html
│   ├── dashboard.html
│   ├── folders.html
│   ├── folder_detail.html
│   ├── login.html
│   ├── register.html
│   ├── settings.html
│   ├── docs.html
│   ├── chatbot.html
│   ├── setup.html
│   └── error.html
│
├── static/              # Static files
│   ├── uploads/        # User uploaded files
│   ├── css/
│   └── js/
│
└── database.db         # SQLite database (created after init)
```

## 🔒 Security Best Practices

1. **Change Secret Key**: Update `SECRET_KEY` in production
2. **Environment Variables**: Use `.env` file for sensitive data
3. **HTTPS**: Always use HTTPS in production
4. **API Rate Limiting**: Configured to prevent abuse
5. **Input Validation**: All inputs are sanitized
6. **Password Hashing**: Secure password storage

## 🚀 Deployment

### PythonAnywhere Deployment

1. **Upload Files**

   ```bash
   # Upload via web interface or Git
   git clone https://github.com/prajwal032004/image-pdf-management-system.git
   ```

2. **Install Dependencies**

   ```bash
   pip install --user -r requirements.txt
   ```

3. **Configure WSGI**

   - Set working directory
   - Update WSGI configuration file

4. **Initialize Database**

   ```bash
   python init_db.py
   ```

5. **Reload Web App**

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Guidelines

- Follow PEP 8 style guide
- Add comments for complex logic
- Update documentation for new features
- Test thoroughly before submitting

## 🐛 Known Issues & Future Enhancements

### Known Issues

- PDF text extraction may fail on scanned documents
- Large file uploads (>10MB) are rejected

### Planned Features

- [ ] Multi-language support for chatbot
- [ ] Advanced image filters and editing
- [ ] Bulk file operations
- [ ] File sharing with expiration links
- [ ] Integration with cloud storage (AWS S3, Google Drive)
- [ ] Mobile app version
- [ ] Advanced analytics dashboard
- [ ] OCR for scanned PDFs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Prajwal**

- GitHub: [@prajwal032004](https://github.com/prajwal032004)
- Project Link: [https://github.com/prajwal032004/image-pdf-management-system](https://github.com/prajwal032004/image-pdf-management-system)

## 🙏 Acknowledgments

- Flask documentation and community
- PythonAnywhere for hosting
- All contributors and users

## 📞 Support

For support, please:

- Open an issue on GitHub
- Check existing documentation
- Review API documentation

---

<div align="center">

### ⭐ Star this repository if you find it helpful!

**Live Demos:**  
[Main App](https://imageapi.pythonanywhere.com/) | [Chatbot](https://apifetch.pythonanywhere.com/)

Made with ❤️ by [Prajwal](https://github.com/prajwal032004)

</div>
