# Logo Integration & Branding Configuration

**Date**: 2026-05-21  
**Status**: Design Approved

## Overview

Integrate Galia Café logo into the navbar and dashboard. Enable dynamic branding configuration through an admin panel so logo and background images can be changed without code modifications.

## Requirements

### Functional Requirements
1. **Navbar Logo Display**
   - Replace "Galia" text with logo image in navbar
   - Logo scales to fit navbar height (~50-60px)
   - Logo should be clickable and navigate to dashboard (home)
   - Fallback to "Galia" text if no logo is configured

2. **Dashboard Hero Banner**
   - Full-screen banner at top of dashboard (above current dashboard cards)
   - Logo centered both horizontally and vertically
   - Configurable background (white by default)
   - Banner scrolls away with page content (not sticky)
   - Responsive: works on mobile and desktop

3. **Admin Configuration Panel**
   - New admin section: "Configuración de Branding"
   - Two file upload fields: Logo and Banner Background
   - Live preview showing how changes will look
   - Save/Update button with success feedback
   - Admin-only access

4. **Image Storage & Retrieval**
   - Store uploaded files in `frontend/public/uploads/`
   - Store configuration (file paths) in database
   - Provide API endpoints for frontend to fetch current branding

### Non-Functional Requirements
- Images load quickly (resize/optimize on upload)
- Fallbacks work seamlessly if images are missing
- Configuration persists across sessions
- Mobile-responsive design

## Architecture

### Backend Changes

**New Model**: `SiteConfig` (in `backend/app/models/`)
```
- id (PK)
- logo_path (optional, string)
- banner_background_path (optional, string)
- created_at
- updated_at
```

**New Routes** (in `backend/app/routes/admin.py` or new `config.py`):
```
GET /api/v1/config/branding
  - Returns: { logo_path, banner_background_path }
  - No auth required (public)

POST /api/v1/admin/config/branding
  - Accepts: multipart form with logo file and/or background file
  - Requires: admin role
  - Returns: updated config
```

**Image Upload Logic**:
- Save files to `frontend/public/uploads/` with timestamp-based names
- Update SiteConfig record with new paths
- Return relative URLs (e.g., `/uploads/logo-1234567890.png`)

### Frontend Changes

**Navbar Component** (`frontend/src/components/layout/Navbar.jsx`):
- Fetch logo from `/api/v1/config/branding` on mount
- Display logo image instead of "Galia" text
- Fallback to "Galia" text if logo_path is null
- Logo height matches navbar (~50-60px)
- Logo should be a link to dashboard

**Dashboard Component** (`frontend/src/pages/Dashboard.jsx`):
- Add hero banner section at top (before existing dashboard cards)
- Fetch banner background from `/api/v1/config/branding`
- Banner is full screen height on first load
- Logo centered with flexbox
- Background image or white solid color
- On scroll, banner scrolls away naturally (not sticky)

**Admin Panel** (new file or extend existing admin):
- Route: `/admin/branding` or `/admin/configuracion/branding`
- Two file input fields (logo, banner background)
- Image preview showing selected files
- Save button (POST to `/api/v1/admin/config/branding`)
- Admin-only access

### File Storage Strategy

**Location**: `frontend/public/uploads/`
**Naming**: `logo-{timestamp}.{ext}` and `banner-{timestamp}.{ext}`
**Database**: Store relative paths (e.g., `/uploads/logo-1234567890.png`)
**Fallback**: If image not found, use CSS color (white for banner, text for logo)

## Data Flow

```
1. User uploads logo/background in Admin panel
   ↓
2. Frontend sends multipart request to POST /api/v1/admin/config/branding
   ↓
3. Backend saves files to frontend/public/uploads/
   ↓
4. Backend updates SiteConfig table with file paths
   ↓
5. Backend returns updated config to frontend
   ↓
6. Frontend fetches updated config via GET /api/v1/config/branding
   ↓
7. Navbar and Dashboard display updated images
```

## Error Handling

- **Missing logo**: Display "Galia" text in navbar
- **Missing background**: Display white solid color in banner
- **File upload fails**: Show user-friendly error message
- **Image not found at runtime**: Fallback to color/text
- **Invalid file type**: Reject with error message (only PNG, JPG, SVG accepted)

## Testing Checklist

- [ ] Logo displays correctly in navbar (desktop and mobile)
- [ ] Logo links to dashboard
- [ ] Fallback text appears when no logo configured
- [ ] Dashboard banner appears full-screen on load
- [ ] Banner scrolls away with page content
- [ ] Banner background displays correctly
- [ ] Admin can upload new logo and background
- [ ] Images persist after page reload
- [ ] Images resize responsively on mobile
- [ ] Fallbacks work when images are missing
- [ ] Admin-only access enforced on config endpoint

## Success Criteria

1. Logo replaces "Galia" text in navbar
2. Dashboard has a full-screen hero banner with centered logo
3. Admin can upload and change logo/background without code changes
4. All images display correctly on desktop and mobile
5. Fallbacks work seamlessly

## Migration Plan

1. Create `SiteConfig` model and migration
2. Add API endpoints (GET/POST branding config)
3. Update Navbar component to use logo from API
4. Add hero banner to Dashboard component
5. Create Admin branding configuration page
6. Test on desktop and mobile
7. Deploy
