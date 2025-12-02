# Updated Deployment Instructions - VoxSplit

## The Issue

Render.com was looking for a Dockerfile. I've fixed the configuration file (`render.yaml`) to work properly.

## New Deployment Steps (Even Easier!)

### Option 1: Manual Deployment (Recommended - 10 minutes)

Since the automatic Blueprint deployment isn't working, let's deploy manually. It's actually simpler!

#### Step 1: Get Your Hugging Face Token (3 minutes)

1. Go to **https://huggingface.co/join** and create a free account
2. Accept model terms:
   - Visit https://huggingface.co/pyannote/speaker-diarization-3.1 and click "Agree and access repository"
   - Visit https://huggingface.co/pyannote/segmentation-3.0 and click "Agree and access repository"
3. Get your token:
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Name: `voxsplit`
   - Role: "Read"
   - Click "Generate token"
   - **COPY THIS TOKEN** (you'll need it soon!)

#### Step 2: Deploy Backend (5 minutes)

1. Go to **https://dashboard.render.com/**
2. Click "New +" button (top right)
3. Select "Web Service"
4. Click "Connect a repository" or "Build and deploy from a Git repository"
5. Find and select **ziadamal/audiosplitter**
6. Click "Connect"

**Configure the Backend:**
- **Name:** `voxsplit-backend`
- **Region:** Oregon (US West) - or closest to you
- **Branch:** main
- **Root Directory:** `backend`
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Free

**Add Environment Variables** (click "Advanced"):

| Key | Value |
|-----|-------|
| `HF_TOKEN` | (paste your Hugging Face token here) |
| `DEBUG` | `false` |
| `MAX_FILE_SIZE_MB` | `500` |
| `DEMUCS_MODEL` | `htdemucs` |
| `DIARIZATION_MODEL` | `pyannote/speaker-diarization-3.1` |

7. Click "Create Web Service"
8. Wait 10-15 minutes for deployment
9. **COPY THE URL** when you see "Live" (e.g., `https://voxsplit-backend.onrender.com`)

#### Step 3: Deploy Frontend (3 minutes)

1. Click "New +" button again
2. Select "Web Service"
3. Select your **ziadamal/audiosplitter** repository
4. Click "Connect"

**Configure the Frontend:**
- **Name:** `voxsplit-frontend`
- **Region:** Oregon (US West) - same as backend
- **Branch:** main
- **Root Directory:** `frontend`
- **Runtime:** Node
- **Build Command:** `npm install && npm run build`
- **Start Command:** `npx serve -s dist -l $PORT`
- **Instance Type:** Free

**Add Environment Variables** (click "Advanced"):

| Key | Value |
|-----|-------|
| `VITE_API_URL` | (paste your backend URL from Step 2) |

5. Click "Create Web Service"
6. Wait 5-10 minutes for deployment
7. When you see "Live", **click the URL** - your website is online!

### Step 4: Done! 🎉

Your VoxSplit website is now permanently deployed and accessible to anyone!

---

## Troubleshooting

### Backend deployment fails

**Check the logs:**
- Click on your backend service in Render dashboard
- Click "Logs" tab
- Look for error messages

**Common issues:**
- Missing Hugging Face token → Add it in Environment Variables
- Wrong Python version → Render should auto-detect Python 3.11

### Frontend can't connect to backend

**Make sure:**
- Backend URL is correct in frontend environment variables
- Backend shows "Live" status
- Backend URL starts with `https://`

### "Application Error" on frontend

- Wait 2-3 minutes - build might still be in progress
- Check build logs for errors
- Make sure build command is: `npm install && npm run build`
- Make sure start command is: `npx serve -s dist -l $PORT`

---

## What Changed?

I fixed the `render.yaml` file to use the correct configuration:
- Changed `env:` to `runtime:`
- Added `rootDir:` to specify backend/frontend folders
- Fixed the static site configuration for frontend
- Simplified the build commands

---

## Your URLs After Deployment

Save these:
- **Backend API:** https://voxsplit-backend.onrender.com
- **Frontend (Your Website):** https://voxsplit-frontend.onrender.com
- **API Docs:** https://voxsplit-backend.onrender.com/docs

---

## Need Help?

If you're stuck, let me know which step you're on and what error message you're seeing!
