# CIRKELLINE KNOWLEDGE SYSTEM - TESTING GUIDE

**Last Updated:** October 21, 2025
**Status:** Admin-Shared Upload Feature - FULLY TESTED ✅

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Manual Testing](#manual-testing)
4. [Automated Testing](#automated-testing)
5. [Test Scenarios](#test-scenarios)
6. [Verification Checklist](#verification-checklist)

---

## 🎯 OVERVIEW

This guide covers testing the complete knowledge management system, including:
- Private document uploads
- **Admin-shared document uploads (NEW)**
- Document listing with proper filtering
- Document deletion
- RAG (Retrieval-Augmented Generation) with access control
- Sidebar UI updates

---

## ✅ PREREQUISITES

### 1. Server Running

```bash
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py
```

Server should be accessible at `http://localhost:7777`

### 2. Test User Accounts

| User | Type | User ID | Password |
|------|------|---------|----------|
| Rasmus | Admin | `2c0a495c-3e56-4f12-ba68-a2d89e2deb71` | (your password) |
| Ivo | Admin | `ee461076-8cbb-4626-947b-956f293cf7bf` | (your password) |
| Regular User | Regular | `6f174494-1055-474c-8d6f-73afb6610745` | (your password) |

### 3. Test Documents

Create these test files in `/tmp/`:

```bash
echo "Rasmus's private technical notes about Cirkelline architecture." > /tmp/rasmus_private.txt
echo "Ivo's private contract and business strategy notes." > /tmp/ivo_private.txt
echo "Regular user's vacation plans and personal notes." > /tmp/regular_user_doc.txt
echo "Company-wide policy document shared with all admins. Contains important HR policies." > /tmp/company_policy.txt
```

---

## 🧪 MANUAL TESTING

### Test Suite 1: Admin-Shared Document Upload (CRITICAL)

**Purpose:** Verify that admins can create and share documents with other admins.

**Test Steps:**

1. **Login as Ivo (Admin)**
   - Navigate to `http://localhost:3000`
   - Login with Ivo's credentials
   - Verify you see the chat interface

2. **Upload Admin-Shared Document**
   - Click the upload button in sidebar
   - Select `/tmp/company_policy.txt`
   - **✅ CHECK THE "Share with all admins" CHECKBOX**
   - Click "Upload"
   - Wait for upload to complete

3. **Verify in Ivo's UI**
   - Check the sidebar - document should appear in **"Shared Documents"** section
   - Should NOT appear in "My Documents" section
   - Document should show "Shared by Ivo"

4. **Verify in Database**
   ```bash
   PGPASSWORD=cirkelline123 psql -h localhost -p 5532 -U cirkelline -d cirkelline -c "
   SELECT name, metadata FROM ai.agno_knowledge
   WHERE name = 'company_policy.txt';
   "
   ```

   **Expected metadata:**
   ```json
   {
     "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
     "user_type": "Admin",
     "access_level": "admin-shared",  ← MUST BE admin-shared!
     "uploaded_by": "ee461076-8cbb-4626-947b-956f293cf7bf",
     "uploaded_at": "2025-10-21T21:18:33.044160",
     "uploaded_via": "frontend_chat",
     "shared_by_name": "Ivo"  ← MUST HAVE THIS FIELD!
   }
   ```

5. **Login as Rasmus (Another Admin)**
   - Logout from Ivo's account
   - Login with Rasmus's credentials
   - Check sidebar - `company_policy.txt` should appear in **"Shared Documents"**
   - Should show "Shared by Ivo"

6. **Test Cirkelline Access (Rasmus)**
   - Send message: "What documents do I have access to?"
   - Cirkelline should list BOTH:
     - Any private documents Rasmus uploaded
     - `company_policy.txt` (shared by Ivo)

7. **Verify Backend Logs**
   - Check terminal where `my_os.py` is running
   - Should see: `📤 Creating ADMIN-SHARED document for all admins`
   - Should see metadata with `access_level: "admin-shared"`

**Success Criteria:**
- ✅ Document appears in "Shared Documents" for Ivo
- ✅ Document appears in "Shared Documents" for Rasmus
- ✅ Metadata has `access_level: "admin-shared"`
- ✅ Metadata has `shared_by_name: "Ivo"`
- ✅ Cirkelline can access the document when Rasmus asks
- ✅ Backend logs show "Creating ADMIN-SHARED document"

---

### Test Suite 2: Private Document Upload

**Purpose:** Verify that all users can create private documents.

**Test Steps:**

1. **Login as Rasmus (Admin)**
   - Upload `/tmp/rasmus_private.txt`
   - **❌ DO NOT CHECK "Share with all admins"**
   - Click "Upload"

2. **Verify in Rasmus's UI**
   - Document should appear in **"My Documents"** section
   - Should NOT appear in "Shared Documents"

3. **Verify Isolation**
   - Login as Ivo (Admin)
   - Check sidebar - should NOT see `rasmus_private.txt`
   - Send message: "What documents do I have?"
   - Cirkelline should NOT mention `rasmus_private.txt`

4. **Verify Database**
   ```bash
   PGPASSWORD=cirkelline123 psql -h localhost -p 5532 -U cirkelline -d cirkelline -c "
   SELECT name, metadata->>'access_level' as access_level
   FROM ai.agno_knowledge
   WHERE name = 'rasmus_private.txt';
   "
   ```

   **Expected:**
   ```
   name              | access_level
   ------------------|-------------
   rasmus_private.txt| private
   ```

**Success Criteria:**
- ✅ Document appears only in uploader's "My Documents"
- ✅ Other users (even admins) cannot see the document
- ✅ Metadata has `access_level: "private"`
- ✅ No `shared_by_name` field in metadata

---

### Test Suite 3: Regular User Restrictions

**Purpose:** Verify that regular users cannot create admin-shared documents.

**Test Steps:**

1. **Login as Regular User**
   - Navigate to upload dialog
   - Select `/tmp/regular_user_doc.txt`
   - **✅ TRY TO CHECK "Share with all admins"**

2. **Expected Behavior:**
   - Checkbox should be DISABLED or HIDDEN for regular users
   - OR: If checkbox is enabled, upload should fail with 403 error

3. **If Upload Allowed (Bug Test):**
   ```bash
   # Upload via API to test backend validation
   curl -X POST http://localhost:7777/api/knowledge/upload \
     -H "Authorization: Bearer $REGULAR_USER_TOKEN" \
     -F "file=@/tmp/test.txt" \
     -F "is_shared=true"
   ```

   **Expected Response:**
   ```json
   {
     "detail": "Only admins can share documents with other admins"
   }
   ```

**Success Criteria:**
- ✅ Regular users cannot access the "Share with all admins" option
- ✅ Backend returns 403 error if regular user tries to set `is_shared=true`
- ✅ Regular users can still upload private documents normally

---

### Test Suite 4: Document Deletion

**Purpose:** Verify proper deletion and permission checks.

**Test Steps:**

1. **Admin Deletes Own Admin-Shared Document**
   - Login as Ivo
   - Find `company_policy.txt` in "Shared Documents"
   - Click delete button
   - Confirm deletion

2. **Verify Deletion**
   - Document should disappear from Ivo's sidebar
   - Login as Rasmus - document should also disappear from his sidebar
   - Check database:
     ```bash
     PGPASSWORD=cirkelline123 psql -h localhost -p 5532 -U cirkelline -d cirkelline -c "
     SELECT name FROM ai.agno_knowledge WHERE name = 'company_policy.txt';
     "
     ```
     Should return 0 rows

3. **User Cannot Delete Other's Documents**
   - Login as Ivo, upload private doc
   - Login as Rasmus
   - Rasmus should NOT see delete button for Ivo's private doc
   - If attempted via API, should get 404 error

**Success Criteria:**
- ✅ Admins can delete their own admin-shared documents
- ✅ Deletion removes document for all admins
- ✅ Users cannot delete other users' documents
- ✅ Cascading delete removes vector embeddings

---

### Test Suite 5: RAG with Access Control

**Purpose:** Verify Cirkelline only accesses documents the user can see.

**Test Scenario:**
- Rasmus has `rasmus_private.txt` (private)
- Ivo has `ivo_private.txt` (private)
- Ivo uploaded `company_policy.txt` (admin-shared)

**Test Steps:**

1. **Login as Rasmus (Admin)**
   - Send: "What documents do I have access to?"
   - **Expected Response:**
     - Should mention `rasmus_private.txt`
     - Should mention `company_policy.txt` (shared by Ivo)
     - Should NOT mention `ivo_private.txt`

2. **Login as Ivo (Admin)**
   - Send: "List my documents"
   - **Expected Response:**
     - Should mention `ivo_private.txt`
     - Should mention `company_policy.txt` (shared by me)
     - Should NOT mention `rasmus_private.txt`

3. **Login as Regular User**
   - Upload `regular_user_doc.txt` (private)
   - Send: "What documents can I access?"
   - **Expected Response:**
     - Should mention ONLY `regular_user_doc.txt`
     - Should NOT mention any admin documents

**Success Criteria:**
- ✅ Each user sees only their private documents + admin-shared (if admin)
- ✅ No cross-user document leakage
- ✅ Cirkelline respects access control in RAG responses

---

## 🤖 AUTOMATED TESTING

### Script 1: Upload Test Documents

**File:** `/home/eenvy/Desktop/cirkelline/test_upload.py`

```bash
cd ~/Desktop/cirkelline
python test_upload.py
```

**What it does:**
- Uploads 4 test documents:
  - `rasmus_private.txt` (Rasmus, private)
  - `ivo_private.txt` (Ivo, private)
  - `regular_user_doc.txt` (Regular user, private)
  - `company_policy.txt` (Ivo, **admin-shared**)
- Prints success confirmation

**Expected Output:**
```
================================================================================
TESTING DOCUMENT UPLOAD AND KNOWLEDGE RETRIEVAL
================================================================================

📤 Uploading test documents...
✅ Uploaded: rasmus_private.txt (owner: 2c0a495c..., access: private)
✅ Uploaded: ivo_private.txt (owner: 62563835..., access: private)
✅ Uploaded: regular_user_doc.txt (owner: 6f174494..., access: private)
✅ Uploaded: company_policy.txt (owner: 62563835..., access: admin-shared)

================================================================================
✅ TEST DOCUMENTS UPLOADED SUCCESSFULLY!
================================================================================
```

---

### Script 2: End-to-End RAG Test

**File:** `/home/eenvy/Desktop/cirkelline/test_retrieval.py`

```bash
cd ~/Desktop/cirkelline
python test_retrieval.py
```

**What it does:**
- Tests document retrieval for each user type via API calls
- Verifies Cirkelline mentions only accessible documents

**Expected Output (Excerpt):**
```
================================================================================
Testing: Ivo (Admin)
Expected documents: ['ivo_private.txt', 'company_policy.txt']
================================================================================

✅ Response received:
Status: 200

Agent said:
You have access to 2 documents:

1. ivo_private.txt - Your personal contract notes
2. company_policy.txt - Company policies (shared)

✅ Found mention of: ivo_private.txt
✅ Found mention of: company_policy.txt

✅ TEST PASSED: All expected documents mentioned!
```

---

### Script 3: Create Vector Embeddings

**File:** `/home/eenvy/Desktop/cirkelline/create_missing_vectors.py`

```bash
cd ~/Desktop/cirkelline
python create_missing_vectors.py
```

**What it does:**
- Generates vector embeddings for documents in Contents DB
- Enables semantic search functionality

---

## ✅ VERIFICATION CHECKLIST

Use this checklist after making changes to the system:

### Upload Functionality
- [ ] Admin can upload private documents
- [ ] Admin can upload admin-shared documents
- [ ] Regular user can upload private documents
- [ ] Regular user CANNOT upload admin-shared documents (403 error)
- [ ] Checkbox state is correctly sent from frontend
- [ ] Backend correctly parses `is_shared` parameter
- [ ] Metadata has correct `access_level` field
- [ ] Metadata includes `shared_by_name` for admin-shared docs

### Sidebar Display
- [ ] Private documents appear in "My Documents" section
- [ ] Admin-shared documents appear in "Shared Documents" section
- [ ] Documents refresh automatically after upload (3s interval)
- [ ] Delete button works for owned documents
- [ ] "Shared by {name}" attribution shows correctly

### Database State
- [ ] `ai.agno_knowledge` has correct metadata structure
- [ ] `ai.agno_embeddings` has vector embeddings for all documents
- [ ] Indexes on `user_id` and `access_level` are present
- [ ] No orphaned embeddings after document deletion

### Access Control
- [ ] Admins see their documents + admin-shared
- [ ] Regular users see only their documents
- [ ] No cross-user document visibility
- [ ] `/api/documents` endpoint filters correctly
- [ ] Custom retriever filters correctly

### RAG Integration
- [ ] Cirkelline lists only accessible documents
- [ ] Cirkelline can search and retrieve document contents
- [ ] No deleted documents in responses
- [ ] No conversation history leakage (uses current message only)

### Backend Logs
- [ ] Upload logs show `"Creating ADMIN-SHARED document"` or `"Creating PRIVATE document"`
- [ ] Logs include full metadata structure
- [ ] No errors during upload/retrieval/deletion
- [ ] Admin detection logs show `is_admin=True` for admins

---

## 🔍 DEBUGGING TIPS

### Issue: Document appears in wrong sidebar section

**Debug Steps:**
1. Check database metadata:
   ```sql
   SELECT name, metadata->>'access_level' FROM ai.agno_knowledge WHERE name = 'YOUR_DOC.txt';
   ```
2. Check frontend code in `DocumentsList.tsx`:
   - `myDocuments` filter: `doc.metadata.user_id === userId && doc.metadata.access_level !== 'admin-shared'`
   - `sharedDocuments` filter: `doc.metadata.access_level === 'admin-shared'`

### Issue: Backend not receiving `is_shared` parameter

**Debug Steps:**
1. Check browser network tab:
   - Request should show FormData with `is_shared: "true"` or `"false"`
2. Check backend endpoint signature:
   - Should have: `is_shared: str = Form("false")`
3. Check backend logs:
   - Should show: `📤 Creating ADMIN-SHARED document` or `📤 Creating PRIVATE document`

### Issue: Cirkelline mentions inaccessible documents

**Debug Steps:**
1. Check custom retriever logic in `my_os.py`:
   - Verify user_id is in kwargs
   - Verify filtering logic matches access rules
2. Check agent instructions (lines 832-845):
   - Must tell agent to use filtered results
3. Enable debug logging:
   ```python
   logger.info(f"Filtered {len(filtered_results)} from {len(search_results)} total")
   ```

---

## 📊 TEST COVERAGE MATRIX

| Feature | Manual Test | Automated Test | Status |
|---------|------------|----------------|--------|
| Admin Upload Private | ✅ Test Suite 2 | ✅ test_upload.py | ✅ PASS |
| Admin Upload Shared | ✅ Test Suite 1 | ✅ test_upload.py | ✅ PASS |
| Regular Upload Private | ✅ Test Suite 2 | ✅ test_upload.py | ✅ PASS |
| Regular Upload Shared Block | ✅ Test Suite 3 | ❌ Not automated | ✅ PASS |
| Sidebar Display | ✅ Test Suite 1 | ❌ Manual only | ✅ PASS |
| Document Deletion | ✅ Test Suite 4 | ❌ Not automated | ✅ PASS |
| RAG Access Control | ✅ Test Suite 5 | ✅ test_retrieval.py | ✅ PASS |
| Cross-User Isolation | ✅ Test Suite 2 | ✅ test_retrieval.py | ✅ PASS |
| Database Integrity | ✅ All suites | ❌ Manual only | ✅ PASS |

---

**Last Updated:** October 21, 2025
**Testing Status:** ALL TESTS PASSING ✅
**Production Ready:** YES ✅
