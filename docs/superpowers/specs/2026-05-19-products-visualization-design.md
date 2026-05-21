# Products Visualization Design
**Date:** 2026-05-19  
**Status:** Approved  
**Scope:** Phase 1 - List View & Image Upload

## Overview
Improve product visualization by replacing generic icons with actual product photos and redesigning the ProductCatalog from a grid view to a clean list view. This makes the POS interface more intuitive and professional. A future "fast counter" view with large product cards is planned but not included in this phase.

## Architecture

### Backend Changes

#### New Endpoint: Image Upload
- **Endpoint:** `POST /api/v1/products/upload-image`
- **Purpose:** Upload product images to S3 and return the URL
- **Request:** 
  - Form data with `file` (multipart/form-data)
  - File types: jpg, png, webp
  - Max size: 5MB
- **Response:** `{ "image_url": "https://s3.../product-123.jpg" }`
- **Error handling:** Return 400 for invalid file types/size, 413 for too large

#### Existing Model
- `Product.image_url` already exists
- No schema changes needed
- Just need to properly use the existing field

### Frontend Components

#### 1. ProductDetail Page (ProductDetail.jsx)
**Changes to image handling:**
- Replace manual URL input (lines 273-284) with:
  - File input for uploading
  - Image preview (if image_url exists)
  - Delete button to clear the image
  - Show upload progress/spinner while uploading
  - Error messages for failed uploads

**Flow:**
1. User selects file from input
2. Upload to backend `/api/v1/products/upload-image`
3. On success: set formData.image_url to returned URL, show preview
4. On error: show error message, allow retry
5. User can clear image by clicking delete button
6. Save product as normal (image_url is included)

#### 2. ProductCatalog Component (ProductCatalog.jsx)
**Current state:** Grid (2-4 columns) with generic 📦 icon

**Changes:**
- Convert grid layout to **vertical list/table**
- Each row displays:
  - **Left:** Product image thumbnail (80x80px), fallback to 📦 icon if no image
  - **Middle:** Product name + category name (optional)
  - **Right:** Price/variants info
- Keep category filter tabs above the list
- Maintain click behavior: clicking row selects the product
- Smooth transitions on hover

**Styling:** Use Galia colors, match existing POS aesthetic

#### 3. Products Page (Products.jsx)
**Current state:** Table without images

**Changes:**
- Add image column as **first column** (before "Producto")
- Image thumbnail: 60x60px, fallback to 📦 if missing
- Image should be clickable to open ProductDetail
- Maintain pagination, search, category filter
- No other layout changes

### Data Flow

```
ProductDetail (create/edit)
├─ User selects image file
├─ Upload to POST /api/v1/products/upload-image
├─ Receive image_url from backend
├─ Set formData.image_url
├─ Show image preview
└─ Save product with image_url

ProductCatalog (POS view)
├─ Fetch products (already includes image_url)
├─ Render list instead of grid
└─ Display image thumbnails (80x80px)

Products (Admin view)
├─ Fetch products (already includes image_url)
├─ Add image thumbnail column
└─ Display thumbnails (60x60px)
```

## Technical Details

### Image Upload Implementation
- Use FormData API to send multipart file
- Send to backend endpoint
- Handle loading state during upload
- Validate file on frontend before sending (type, size)
- Show preview immediately on success
- Allow clearing image (set image_url to empty)

### Image Fallbacks
- If no image: show generic icon 📦
- Prevent broken image links (use alt text)
- Consider lazy loading for thumbnail lists

### List View Layout (ProductCatalog)
- Use flexbox or grid for alignment
- Row height: ~100px to accommodate 80x80 image
- Responsive on mobile (might stack to single column if needed)
- Maintain category filter UX

## Testing Scope

**Manual testing required:**
- Upload product image and verify it displays
- Delete product image and verify fallback icon appears
- ProductCatalog renders list view correctly
- Products page shows image thumbnails
- Images display correctly after page reload
- Broken/missing images show fallback icon
- Responsive behavior on different screen sizes

**Not included:** End-to-end tests (kept out of scope for this phase)

## Future Work

**Mostrador Rápido (Fast Counter):**
- New POS view with large product cards (200x200px images)
- Gallery-style layout
- Planned for later phase

## Notes

- `image_url` field already exists, no migration needed
- S3 configuration already in place
- File upload endpoint may reuse existing S3 integration patterns
- ProductDetail form already has tab structure, image upload fits in "Información" tab
