# Logo & Branding Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add configurable Galia Café logo to navbar and create a full-screen hero banner on dashboard with dynamic branding management via admin panel.

**Architecture:** Backend stores branding config (logo/background paths) in database; frontend fetches on load and displays in Navbar and Dashboard. Admin panel allows uploading new images. Files stored in `frontend/public/uploads/` with timestamp-based naming.

**Tech Stack:** Flask (backend), SQLAlchemy (ORM), React (frontend), axios (API calls), multipart forms (file upload)

---

## Task 1: Create SiteConfig Model

**Files:**
- Create: `backend/app/models/site_config.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create SiteConfig model file**

Create `backend/app/models/site_config.py`:

```python
from backend.app.extensions import db
from datetime import datetime

class SiteConfig(db.Model):
    __tablename__ = 'site_config'
    
    id = db.Column(db.Integer, primary_key=True)
    logo_path = db.Column(db.String(255), nullable=True)
    banner_background_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'logo_path': self.logo_path,
            'banner_background_path': self.banner_background_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
```

- [ ] **Step 2: Add SiteConfig to models __init__.py**

In `backend/app/models/__init__.py`, add:

```python
from .site_config import SiteConfig
```

- [ ] **Step 3: Create database migration**

Run in `backend/` directory:

```bash
flask db migrate -m "Add SiteConfig model for branding configuration"
```

Expected output: Migration file created in `backend/migrations/versions/`

- [ ] **Step 4: Review and run migration**

```bash
flask db upgrade
```

Expected: No errors, table `site_config` created in database

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/site_config.py backend/app/models/__init__.py backend/migrations/
git commit -m "feat: add SiteConfig model for branding configuration"
```

---

## Task 2: Create Config API Endpoints (Backend)

**Files:**
- Create: `backend/app/routes/config.py`
- Modify: `backend/app/__init__.py` (register blueprint)
- Create: `backend/tests/test_config.py`

- [ ] **Step 1: Write failing test for GET branding config**

Create `backend/tests/test_config.py`:

```python
import pytest
from backend.app.models.site_config import SiteConfig

def test_get_branding_config_returns_empty_by_default(client):
    """Test GET /api/v1/config/branding returns empty config when none exists"""
    response = client.get('/api/v1/config/branding')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['logo_path'] is None
    assert data['banner_background_path'] is None

def test_get_branding_config_returns_stored_paths(client, db):
    """Test GET returns stored config"""
    config = SiteConfig(
        logo_path='/uploads/logo-123.png',
        banner_background_path='/uploads/banner-456.png'
    )
    db.session.add(config)
    db.session.commit()
    
    response = client.get('/api/v1/config/branding')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['logo_path'] == '/uploads/logo-123.png'
    assert data['banner_background_path'] == '/uploads/banner-456.png'
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_config.py::test_get_branding_config_returns_empty_by_default -v
```

Expected: FAILED (no route defined)

- [ ] **Step 3: Create config routes blueprint**

Create `backend/app/routes/config.py`:

```python
from flask import Blueprint, jsonify
from backend.app.models.site_config import SiteConfig

config_bp = Blueprint('config', __name__, url_prefix='/api/v1/config')

@config_bp.route('/branding', methods=['GET'])
def get_branding_config():
    """Get current branding configuration (logo and banner background paths)"""
    config = SiteConfig.query.first()
    
    if not config:
        return jsonify({
            'logo_path': None,
            'banner_background_path': None
        }), 200
    
    return jsonify(config.to_dict()), 200
```

- [ ] **Step 4: Register blueprint in app __init__.py**

In `backend/app/__init__.py`, find where blueprints are registered and add:

```python
from backend.app.routes.config import config_bp
# ... in create_app function, after other blueprint registrations:
app.register_blueprint(config_bp)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend
pytest tests/test_config.py::test_get_branding_config_returns_empty_by_default -v
pytest tests/test_config.py::test_get_branding_config_returns_stored_paths -v
```

Expected: PASSED for both

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/config.py backend/tests/test_config.py
git commit -m "feat: add GET /api/v1/config/branding endpoint"
```

---

## Task 3: Add Admin POST Endpoint for Branding Upload

**Files:**
- Modify: `backend/app/routes/config.py`
- Modify: `backend/tests/test_config.py`
- Create: `backend/app/utils/file_upload.py`

- [ ] **Step 1: Write test for POST branding config with file upload**

Add to `backend/tests/test_config.py`:

```python
def test_post_branding_config_requires_admin(client, user, auth_token):
    """Test POST /api/v1/admin/config/branding requires admin role"""
    response = client.post(
        '/api/v1/admin/config/branding',
        headers={'Authorization': f'Bearer {auth_token}'},
        data={}
    )
    
    assert response.status_code == 403  # Forbidden

def test_post_branding_config_updates_logo(client, admin_user, admin_auth_token, tmp_path):
    """Test POST updates logo in config"""
    # Create a fake image file
    fake_image = tmp_path / "logo.png"
    fake_image.write_bytes(b'fake png data')
    
    with open(fake_image, 'rb') as f:
        response = client.post(
            '/api/v1/admin/config/branding',
            headers={'Authorization': f'Bearer {admin_auth_token}'},
            data={'logo': (f, 'logo.png')},
            content_type='multipart/form-data'
        )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['logo_path'] is not None
    assert data['logo_path'].startswith('/uploads/logo-')
    assert data['logo_path'].endswith('.png')
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_config.py::test_post_branding_config_requires_admin -v
```

Expected: FAILED (no POST endpoint defined)

- [ ] **Step 3: Create file upload utility**

Create `backend/app/utils/file_upload.py`:

```python
import os
from datetime import datetime
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
UPLOAD_FOLDER = 'frontend/public/uploads'

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload_file(file):
    """
    Save uploaded file with timestamp-based name.
    Returns relative path (e.g., '/uploads/logo-1234567890.png')
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Create uploads folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    new_filename = f"{file.filename.rsplit('.', 1)[0]}-{timestamp}.{ext}"
    
    filepath = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(filepath)
    
    # Return relative path for database storage
    return f'/uploads/{new_filename}'
```

- [ ] **Step 4: Add POST endpoint to config routes**

Add to `backend/app/routes/config.py`:

```python
from flask import request
from flask_login import login_required, current_user
from backend.app.extensions import db
from backend.app.utils.file_upload import save_upload_file

@config_bp.route('/branding', methods=['POST'], endpoint='update_branding')
def post_branding_config():
    """Update branding configuration (admin only)"""
    from backend.app.models.user import User
    
    # Check admin permission
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    logo_file = request.files.get('logo')
    background_file = request.files.get('background')
    
    if not logo_file and not background_file:
        return jsonify({'error': 'At least one file must be provided'}), 400
    
    try:
        config = SiteConfig.query.first()
        if not config:
            config = SiteConfig()
            db.session.add(config)
        
        if logo_file:
            config.logo_path = save_upload_file(logo_file)
        
        if background_file:
            config.banner_background_path = save_upload_file(background_file)
        
        db.session.commit()
        return jsonify(config.to_dict()), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update configuration'}), 500
```

- [ ] **Step 5: Update file_upload.py import in __init__.py**

In `backend/app/utils/__init__.py` or create if it doesn't exist, ensure imports are available.

- [ ] **Step 6: Run both POST tests**

```bash
cd backend
pytest tests/test_config.py::test_post_branding_config_requires_admin -v
pytest tests/test_config.py::test_post_branding_config_updates_logo -v
```

Expected: Both PASSED

- [ ] **Step 7: Commit**

```bash
git add backend/app/routes/config.py backend/app/utils/file_upload.py backend/tests/test_config.py
git commit -m "feat: add POST /api/v1/admin/config/branding endpoint for file upload"
```

---

## Task 4: Create Frontend Config Service

**Files:**
- Create: `frontend/src/services/configService.js`

- [ ] **Step 1: Create config service**

Create `frontend/src/services/configService.js`:

```javascript
import axios from 'axios'

const API_BASE_URL = '/api/v1'

export const configService = {
  getBrandingConfig: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/config/branding`)
      return response.data
    } catch (error) {
      console.error('Error fetching branding config:', error)
      return {
        logo_path: null,
        banner_background_path: null
      }
    }
  },

  updateBrandingConfig: async (logoFile, backgroundFile) => {
    try {
      const formData = new FormData()
      if (logoFile) formData.append('logo', logoFile)
      if (backgroundFile) formData.append('background', backgroundFile)

      const response = await axios.post(`${API_BASE_URL}/admin/config/branding`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error updating branding config:', error)
      throw error
    }
  }
}

export default configService
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/configService.js
git commit -m "feat: add configService for branding API calls"
```

---

## Task 5: Update Navbar to Display Logo

**Files:**
- Modify: `frontend/src/components/layout/Navbar.jsx`

- [ ] **Step 1: Update Navbar to fetch and display logo**

Replace the content of `frontend/src/components/layout/Navbar.jsx`:

```javascript
import { useAuth } from '@/context/AuthContext'
import { LogOut, User, Menu } from 'lucide-react'
import NotificationBell from '../notifications/NotificationBell'
import { useState, useEffect } from 'react'
import { configService } from '@/services/configService'
import { useNavigate } from 'react-router-dom'

const Navbar = ({ onMenuClick }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [logoPath, setLogoPath] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBrandingConfig = async () => {
      try {
        const config = await configService.getBrandingConfig()
        setLogoPath(config.logo_path)
      } catch (error) {
        console.error('Error loading logo:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchBrandingConfig()
  }, [])

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Error al cerrar sesión:', error)
    }
  }

  const handleLogoClick = () => {
    navigate('/dashboard')
  }

  return (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="px-4 md:px-6 py-3 md:py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 md:space-x-4">
            <button
              onClick={onMenuClick}
              className="md:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Menu className="h-6 w-6 text-gray-600" />
            </button>
            
            {/* Logo or Fallback Text */}
            <button
              onClick={handleLogoClick}
              className="flex items-center hover:opacity-80 transition-opacity"
            >
              {logoPath && !loading ? (
                <img 
                  src={logoPath} 
                  alt="Galia Logo" 
                  className="h-12 md:h-16 object-contain"
                />
              ) : (
                <h1 className="text-xl md:text-2xl font-bold text-primary">Galia</h1>
              )}
            </button>
            
            <span className="hidden sm:inline text-xs md:text-sm text-muted-foreground">Gestión de Cafetería</span>
          </div>
          
          <div className="flex items-center space-x-2 md:space-x-4">
            <NotificationBell />
            
            <div className="hidden sm:flex items-center space-x-2">
              <User className="h-4 md:h-5 w-4 md:w-5 text-muted-foreground" />
              <span className="text-xs md:text-sm font-medium truncate max-w-[120px] md:max-w-none">{user?.email}</span>
              {user?.role === 'admin' && (
                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary">
                  Admin
                </span>
              )}
            </div>
            
            <button
              onClick={handleLogout}
              className="flex items-center space-x-1 md:space-x-2 px-2 md:px-4 py-2 text-xs md:text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Salir</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/layout/Navbar.jsx
git commit -m "feat: display logo in navbar with fallback to text"
```

---

## Task 6: Add Hero Banner to Dashboard

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`

- [ ] **Step 1: Update Dashboard to add hero banner**

In `frontend/src/pages/Dashboard.jsx`, add to the imports at the top:

```javascript
import { configService } from '@/services/configService'
```

And add state for branding config in the component (after existing useState calls around line 12):

```javascript
const [brandingConfig, setBrandingConfig] = useState({
  logo_path: null,
  banner_background_path: null
})
```

Add this useEffect hook after the existing useEffect (after line 32):

```javascript
useEffect(() => {
  const fetchBrandingConfig = async () => {
    try {
      const config = await configService.getBrandingConfig()
      setBrandingConfig(config)
    } catch (error) {
      console.error('Error loading branding config:', error)
    }
  }

  fetchBrandingConfig()
}, [])
```

Now find the return statement and add the hero banner at the very beginning (before any existing content). Replace the entire return statement with this:

```javascript
return (
  <div className="min-h-screen bg-gray-50">
    {/* Hero Banner */}
    <div 
      className="h-screen w-full flex flex-col items-center justify-center relative"
      style={{
        backgroundImage: brandingConfig.banner_background_path 
          ? `url('${brandingConfig.banner_background_path}')`
          : 'none',
        backgroundColor: brandingConfig.banner_background_path ? 'transparent' : 'white',
        backgroundSize: 'cover',
        backgroundPosition: 'center'
      }}
    >
      {/* Overlay to ensure logo is visible */}
      {brandingConfig.banner_background_path && (
        <div className="absolute inset-0 bg-black/20"></div>
      )}
      
      <div className="relative z-10 flex flex-col items-center">
        {brandingConfig.logo_path ? (
          <img 
            src={brandingConfig.logo_path} 
            alt="Galia Logo" 
            className="h-40 md:h-64 object-contain"
          />
        ) : (
          <h1 className="text-6xl md:text-8xl font-bold text-primary">Galia</h1>
        )}
      </div>
    </div>

    {/* Dashboard Content */}
    <div className="max-w-7xl mx-auto px-4 py-8">
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-900">{error}</p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Cargando...</p>
        </div>
      ) : (
        <>
          {!isAdmin() ? (
            // Employee Dashboard
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* ... existing employee dashboard cards ... */}
            </div>
          ) : (
            // Admin Dashboard
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* ... existing admin dashboard cards ... */}
            </div>
          )}
        </>
      )}
    </div>
  </div>
)
```

Note: Keep all existing dashboard card content (ventas, gastos, etc.) - just wrap them in the new structure.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Dashboard.jsx
git commit -m "feat: add full-screen hero banner to dashboard"
```

---

## Task 7: Create Admin Branding Configuration Page

**Files:**
- Create: `frontend/src/pages/admin/BrandingConfig.jsx`
- Modify: Frontend routing (depends on existing admin setup)

- [ ] **Step 1: Create BrandingConfig component**

Create `frontend/src/pages/admin/BrandingConfig.jsx`:

```javascript
import { useState, useEffect } from 'react'
import { configService } from '@/services/configService'
import { Upload, Check, AlertCircle } from 'lucide-react'

const BrandingConfig = () => {
  const [logoFile, setLogoFile] = useState(null)
  const [backgroundFile, setBackgroundFile] = useState(null)
  const [currentConfig, setCurrentConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [logoPreview, setLogoPreview] = useState(null)
  const [backgroundPreview, setBackgroundPreview] = useState(null)

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await configService.getBrandingConfig()
        setCurrentConfig(config)
      } catch (error) {
        console.error('Error loading config:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchConfig()
  }, [])

  const handleLogoChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setLogoFile(file)
      const reader = new FileReader()
      reader.onload = (event) => setLogoPreview(event.target.result)
      reader.readAsDataURL(file)
    }
  }

  const handleBackgroundChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setBackgroundFile(file)
      const reader = new FileReader()
      reader.onload = (event) => setBackgroundPreview(event.target.result)
      reader.readAsDataURL(file)
    }
  }

  const handleSave = async () => {
    if (!logoFile && !backgroundFile) {
      setMessage({ type: 'warning', text: 'Select at least one file to upload' })
      return
    }

    try {
      setSaving(true)
      setMessage(null)
      
      const updatedConfig = await configService.updateBrandingConfig(logoFile, backgroundFile)
      setCurrentConfig(updatedConfig)
      setLogoFile(null)
      setBackgroundFile(null)
      setLogoPreview(null)
      setBackgroundPreview(null)
      setMessage({ type: 'success', text: 'Branding configuration updated successfully!' })
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to update configuration' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="p-6 text-center">Loading...</div>
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-2">Configuración de Branding</h1>
      <p className="text-gray-600 mb-8">Sube el logo y la imagen de fondo para personalizar la cafetería.</p>

      {message && (
        <div className={`mb-6 p-4 rounded-lg flex items-start space-x-3 ${
          message.type === 'success' ? 'bg-green-50 border border-green-200' :
          message.type === 'error' ? 'bg-red-50 border border-red-200' :
          'bg-yellow-50 border border-yellow-200'
        }`}>
          {message.type === 'success' ? (
            <Check className="h-5 w-5 text-green-600 mt-0.5" />
          ) : (
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          )}
          <p className={`text-sm font-medium ${
            message.type === 'success' ? 'text-green-900' :
            message.type === 'error' ? 'text-red-900' :
            'text-yellow-900'
          }`}>
            {message.text}
          </p>
        </div>
      )}

      <div className="space-y-8">
        {/* Logo Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
          <h2 className="text-xl font-semibold mb-4">Logo de Cafetería</h2>
          
          {currentConfig?.logo_path && !logoPreview && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 font-medium">Logo Actual:</p>
              <img 
                src={currentConfig.logo_path} 
                alt="Current Logo" 
                className="h-24 mt-2 object-contain"
              />
            </div>
          )}

          <label className="flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 p-6 rounded-lg transition">
            <Upload className="h-8 w-8 text-gray-400 mb-2" />
            <span className="text-gray-600 font-medium">Click to upload logo</span>
            <span className="text-sm text-gray-500 mt-1">PNG, JPG, SVG (recomendado)</span>
            <input 
              type="file" 
              accept="image/*" 
              onChange={handleLogoChange}
              className="hidden"
            />
          </label>

          {logoPreview && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 font-medium mb-2">Preview:</p>
              <img 
                src={logoPreview} 
                alt="Logo Preview" 
                className="h-24 object-contain"
              />
            </div>
          )}
        </div>

        {/* Background Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
          <h2 className="text-xl font-semibold mb-4">Fondo del Banner</h2>
          
          {currentConfig?.banner_background_path && !backgroundPreview && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 font-medium">Fondo Actual:</p>
              <img 
                src={currentConfig.banner_background_path} 
                alt="Current Background" 
                className="h-24 mt-2 object-cover w-full rounded"
              />
            </div>
          )}

          <label className="flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 p-6 rounded-lg transition">
            <Upload className="h-8 w-8 text-gray-400 mb-2" />
            <span className="text-gray-600 font-medium">Click to upload background</span>
            <span className="text-sm text-gray-500 mt-1">PNG, JPG (opcional)</span>
            <input 
              type="file" 
              accept="image/*" 
              onChange={handleBackgroundChange}
              className="hidden"
            />
          </label>

          {backgroundPreview && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 font-medium mb-2">Preview:</p>
              <img 
                src={backgroundPreview} 
                alt="Background Preview" 
                className="h-24 object-cover w-full rounded"
              />
            </div>
          )}
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition"
        >
          {saving ? 'Guardando...' : 'Guardar Cambios'}
        </button>
      </div>
    </div>
  )
}

export default BrandingConfig
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/admin/BrandingConfig.jsx
git commit -m "feat: create admin branding configuration page"
```

---

## Task 8: Add Route to Admin Branding Page

**Files:**
- Modify: Frontend routing (admin routes file)

- [ ] **Step 1: Locate admin routing file and add route**

Find the admin routes file (likely `frontend/src/pages/admin/` or main routing config).

Add this import at the top:

```javascript
import BrandingConfig from './BrandingConfig'
```

Add this route in your admin routes array/config:

```javascript
{
  path: '/admin/branding',
  element: <BrandingConfig />,
  requiredRole: 'admin'
}
```

Or if using a different routing pattern, add the appropriate route.

- [ ] **Step 2: Test route loads**

Navigate to `/admin/branding` in the browser. You should see the branding config page.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/admin/
git commit -m "feat: add /admin/branding route to admin panel"
```

---

## Task 9: Create Uploads Directory and Add to .gitignore

**Files:**
- Create: `frontend/public/uploads/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: Create uploads directory**

```bash
mkdir -p frontend/public/uploads
touch frontend/public/uploads/.gitkeep
```

- [ ] **Step 2: Add uploads to .gitignore**

Open `.gitignore` and add:

```
# Uploaded files
frontend/public/uploads/*
!frontend/public/uploads/.gitkeep
```

- [ ] **Step 3: Commit**

```bash
git add frontend/public/uploads/.gitkeep .gitignore
git commit -m "chore: add uploads directory to gitignore"
```

---

## Task 10: Test Full Integration Locally

**Files:**
- No files to modify

- [ ] **Step 1: Start backend**

```bash
cd backend
python run.py
```

Expected: Backend running on http://localhost:5001

- [ ] **Step 2: Start frontend**

Open new terminal:

```bash
cd frontend
npm run dev
```

Expected: Frontend running on http://localhost:5173

- [ ] **Step 3: Test GET /api/v1/config/branding returns empty config**

```bash
curl http://localhost:5001/api/v1/config/branding
```

Expected response:
```json
{
  "logo_path": null,
  "banner_background_path": null
}
```

- [ ] **Step 4: Navigate to dashboard**

Open http://localhost:5173/dashboard

Expected:
- Full-screen hero banner appears with white background
- "Galia" text shows as fallback (no logo yet)
- Navbar shows "Galia" text (no logo yet)

- [ ] **Step 5: Login as admin and navigate to /admin/branding**

http://localhost:5173/admin/branding

Expected: Admin branding config page loads with upload fields

- [ ] **Step 6: Upload logo**

- Select the Galia logo image (the one you provided)
- Click save
- Should see success message
- Current logo preview should appear

- [ ] **Step 7: Verify navbar shows logo**

Refresh dashboard page or navigate away and back

Expected:
- Navbar now shows the Galia logo instead of text
- Logo is appropriately sized to navbar height

- [ ] **Step 8: Upload background image (optional)**

- In admin panel, upload a background image
- Save changes
- Navigate to dashboard

Expected: Hero banner now shows background image with logo centered over it

- [ ] **Step 9: Test on mobile**

Resize browser window to mobile size or use responsive design mode

Expected:
- Hero banner still full-screen and centered
- Logo scales appropriately
- Images load correctly

- [ ] **Step 10: Final commit**

```bash
git status
# Should show all changes committed
git log --oneline -10
# Should show all feature commits
```

---

## Final Verification Checklist

- [ ] Logo displays in navbar (desktop and mobile)
- [ ] Logo in navbar navigates to dashboard
- [ ] Fallback text "Galia" appears when no logo configured
- [ ] Dashboard hero banner is full-screen
- [ ] Logo centered in banner
- [ ] Banner background displays correctly
- [ ] Admin can upload new logo in /admin/branding
- [ ] Admin can upload new background in /admin/branding
- [ ] Images persist after page reload
- [ ] Images are responsive on mobile
- [ ] Fallbacks work when images are missing
- [ ] All tests pass: `pytest backend/tests/test_config.py -v`
- [ ] All commits have appropriate messages
