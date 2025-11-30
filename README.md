# 🔒 Secure Collab Drive

A full-stack secure file sharing application with military-grade encryption and granular access controls. Perfect for teams that need to collaborate on sensitive documents with peace of mind.

## ✨ Key Features

- **🔐 AES Encryption** - All uploaded files are encrypted using AES-256 encryption before storage
- **👥 Dual Access System** - Granular permission management with "View" and "Edit" roles
- **🔄 Real-time Collaboration** - Multiple users can access and manage files simultaneously  
- **🎨 Modern UI** - Clean, responsive interface built with Tailwind CSS
- **📤 Secure File Upload/Download** - Encrypted file transfer with integrity verification
- **📂 File Management** - Upload, download, delete, and organize encrypted files
- **🔑 User Authentication** - Secure login system with session management

## 🛠️ Tech Stack

**Backend:**
- Python 3.x
- Flask (Web framework)
- SQLite (Database)
- Cryptography library (AES encryption)

**Frontend:**
- HTML5/CSS3
- JavaScript (ES6+)
- Tailwind CSS
- Dynamic AJAX requests

## 🚀 Getting Started

### Prerequisites

```bash
python >= 3.8
pip (Python package manager)
```

### Installation

1. Clone the repository
```bash
git clone https://github.com/scmandolikar/secure-collab-drive.git
cd secure-collab-drive
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the application
```bash
python app.py
```

4. Open your browser and navigate to
```
http://localhost:5000
```

## 📝 How It Works

### Encryption Process
1. User uploads a file through the web interface
2. Server generates a unique AES encryption key
3. File is encrypted using AES-256 in CBC mode
4. Encrypted file is stored securely
5. Encryption key is securely managed in the database

### Permission System
- **View Access**: Users can view and download files
- **Edit Access**: Users can view, download, upload, and delete files
- Admin can modify permissions for all users

## 📚 Project Structure

```
secure-collab-drive/
├── app.py              # Main Flask application
├── client.py           # Client-side utilities
├── index.html          # Main web interface
├── requirements.txt    # Python dependencies
└── test_document.txt   # Sample test file
```

## 🔒 Security Features

- **End-to-end encryption** for all file transfers
- **Secure key management** with database-backed storage
- **Permission-based access control** (PBAC)
- **Session management** to prevent unauthorized access
- **Input validation** to prevent injection attacks

## 📌 Use Cases

- **Corporate file sharing** - Share confidential documents within teams
- **Healthcare** - Secure patient record management
- **Legal firms** - Encrypted document collaboration
- **Educational institutions** - Secure assignment submissions
- **Remote teams** - Collaborative workspace with security

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 📧 Contact

**Sakshath Mandolikar**
- Email: scmandolikar@gmail.com
- GitHub: [@scmandolikar](https://github.com/scmandolikar)
- LinkedIn: [Sakshath Mandolikar](https://www.linkedin.com/in/sakshath-mandolikar-8432b8396)

---

**Built with ❤️ by Sakshath Mandolikar** | TY BScIT Student | Academic Project
