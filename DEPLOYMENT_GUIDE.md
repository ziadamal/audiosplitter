# VoxSplit - Easy Deployment Guide (No Technical Knowledge Required)

**Estimated Time:** 15-20 minutes  
**Cost:** 100% FREE  
**Platform:** Render.com (automatic, no server management needed)

---

## What You'll Get

After following this guide, you'll have your own VoxSplit website running permanently on the internet with:

- A unique web address (URL) that you can share with anyone
- Automatic updates and maintenance
- Free hosting forever
- Professional audio separation features

---

## Before You Start

You'll need to create **2 free accounts**:

1. **GitHub Account** (to store your code)
2. **Render.com Account** (to host your website)
3. **Hugging Face Account** (for AI models - optional but recommended)

Don't worry! I'll guide you through each step.

---

## Step 1: Create a GitHub Account (5 minutes)

GitHub will store your application code.

1. Go to **https://github.com/signup**
2. Enter your email address
3. Create a password
4. Choose a username
5. Verify your email
6. Click "Create account"

**✓ Done!** You now have a GitHub account.

---

## Step 2: Upload Your Code to GitHub (10 minutes)

### Option A: Using GitHub Desktop (Easiest - Recommended)

1. **Download GitHub Desktop**
   - Go to https://desktop.github.com/
   - Click "Download for Windows" (or Mac/Linux)
   - Install the program

2. **Sign in to GitHub Desktop**
   - Open GitHub Desktop
   - Click "Sign in to GitHub.com"
   - Enter your GitHub username and password

3. **Create a New Repository**
   - Click "File" → "New Repository"
   - Name: `voxsplit-app`
   - Description: `Audio separation application`
   - Local Path: Choose where to save (e.g., Desktop)
   - Click "Create Repository"

4. **Add Your Files**
   - Open the folder where you saved the repository
   - Copy ALL files from the `audio-separator` folder into this new folder
   - Go back to GitHub Desktop
   - You'll see all files listed
   - In the bottom left, type: "Initial upload"
   - Click "Commit to main"
   - Click "Publish repository"
   - Make sure "Keep this code private" is UNCHECKED (public repository is required for free hosting)
   - Click "Publish repository"

**✓ Done!** Your code is now on GitHub.

### Option B: Using GitHub Website (Alternative)

1. **Create Repository on GitHub**
   - Go to https://github.com/new
   - Repository name: `voxsplit-app`
   - Description: `Audio separation application`
   - Select "Public"
   - Click "Create repository"

2. **Upload Files**
   - Click "uploading an existing file"
   - Drag and drop ALL files from the `audio-separator` folder
   - Scroll down and click "Commit changes"

**✓ Done!** Your code is now on GitHub.

---

## Step 3: Create a Hugging Face Account (5 minutes - Optional)

Hugging Face provides the AI models for speaker detection.

1. Go to **https://huggingface.co/join**
2. Enter your email and create a password
3. Verify your email
4. Click "Create account"

5. **Accept Model Terms** (Important!)
   - Go to https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click "Agree and access repository"
   - Go to https://huggingface.co/pyannote/segmentation-3.0
   - Click "Agree and access repository"

6. **Get Your Token**
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Name: `voxsplit-app`
   - Role: Select "Read"
   - Click "Generate token"
   - **COPY THIS TOKEN** and save it somewhere safe (you'll need it later)

**✓ Done!** You have your Hugging Face token.

---

## Step 4: Create a Render.com Account (3 minutes)

Render.com will host your website for free.

1. Go to **https://render.com/register**
2. Click "Sign up with GitHub"
3. Authorize Render to access your GitHub account
4. Verify your email if prompted

**✓ Done!** You have a Render account.

---

## Step 5: Deploy Your Application (5 minutes)

Now the magic happens! Render will automatically set up everything.

### Deploy Backend (API Server)

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com/
   - Click "New +" button (top right)
   - Select "Web Service"

2. **Connect Your Repository**
   - Find and select your `voxsplit-app` repository
   - Click "Connect"

3. **Configure Backend Service**
   - **Name:** `voxsplit-backend`
   - **Region:** Oregon (US West) - or closest to you
   - **Branch:** main
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free

4. **Add Environment Variables**
   - Click "Advanced" button
   - Click "Add Environment Variable" for each:
   
   | Key | Value |
   |-----|-------|
   | `HF_TOKEN` | (paste your Hugging Face token here) |
   | `DEBUG` | `false` |
   | `MAX_FILE_SIZE_MB` | `500` |
   | `CORS_ORIGINS` | `*` |
   | `DEMUCS_MODEL` | `htdemucs` |
   | `DIARIZATION_MODEL` | `pyannote/speaker-diarization-3.1` |

5. **Create Service**
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment (Render will show progress)
   - When you see "Live" with a green dot, copy the URL (e.g., `https://voxsplit-backend.onrender.com`)

**✓ Backend is live!**

### Deploy Frontend (Website)

1. **Create Another Web Service**
   - Click "New +" button again
   - Select "Web Service"
   - Select your `voxsplit-app` repository

2. **Configure Frontend Service**
   - **Name:** `voxsplit-frontend`
   - **Region:** Oregon (US West) - same as backend
   - **Branch:** main
   - **Root Directory:** `frontend`
   - **Runtime:** Node
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm install -g serve && serve -s dist -p $PORT`
   - **Instance Type:** Free

3. **Add Environment Variables**
   - Click "Advanced"
   - Add this variable:
   
   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | (paste your backend URL from step 5 above) |

4. **Create Service**
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment
   - When you see "Live" with a green dot, **this is your website URL!**

**✓ Your website is live!**

---

## Step 6: Use Your Website

1. Click on your frontend URL (e.g., `https://voxsplit-frontend.onrender.com`)
2. Your VoxSplit application will open
3. Upload an audio file and test it!

**🎉 Congratulations!** Your website is now permanently deployed and accessible to anyone on the internet.

---

## Important Notes

### Free Tier Limitations

Render's free tier has some limitations:

- **Automatic Sleep:** Your app will sleep after 15 minutes of inactivity
- **Wake-up Time:** First visit after sleep takes 30-60 seconds to wake up
- **Disk Space:** 1GB storage for processed files
- **Monthly Hours:** 750 hours per month (enough for most personal use)

### Keeping Your App Awake (Optional)

If you want your app to respond faster, you can use a free service like **UptimeRobot**:

1. Go to https://uptimerobot.com/
2. Create a free account
3. Add a new monitor with your frontend URL
4. It will ping your site every 5 minutes to keep it awake

### Upgrading (Optional)

If you need better performance:

- **Render Starter Plan:** $7/month - no sleep, faster servers
- **Render Standard Plan:** $25/month - even faster, more storage

---

## Troubleshooting

### "Application Error" Message

- Wait 2-3 minutes and refresh - deployment might still be in progress
- Check Render dashboard for error logs
- Make sure all environment variables are set correctly

### "Cannot connect to backend"

- Make sure you copied the backend URL correctly to the frontend environment variable
- Check that both services show "Live" status in Render dashboard

### Speaker diarization not working

- Make sure you added your Hugging Face token
- Verify you accepted the model terms on Hugging Face
- Check that the token has "Read" permissions

### Files not uploading

- Check file size (max 500MB)
- Make sure file format is supported (MP3, WAV, M4A, FLAC, OGG, AAC)
- Try a smaller file first to test

---

## Your Website URLs

After deployment, save these URLs:

- **Your Website (Frontend):** `https://voxsplit-frontend.onrender.com` (or your custom name)
- **API Documentation:** `https://voxsplit-backend.onrender.com/docs`
- **GitHub Repository:** `https://github.com/YOUR_USERNAME/voxsplit-app`

---

## Updating Your Website

If you want to make changes later:

1. Update files in your GitHub repository
2. Render will automatically detect changes and redeploy
3. Wait 5-10 minutes for the update to complete

---

## Getting Help

If you need assistance:

- **Render Support:** https://render.com/docs
- **GitHub Help:** https://docs.github.com/
- **Hugging Face Help:** https://huggingface.co/docs

---

## Summary Checklist

- [ ] Created GitHub account
- [ ] Uploaded code to GitHub
- [ ] Created Hugging Face account
- [ ] Got Hugging Face token
- [ ] Created Render account
- [ ] Deployed backend service
- [ ] Deployed frontend service
- [ ] Tested the website
- [ ] Saved all URLs

**Total Cost:** $0 (100% Free)  
**Maintenance Required:** None (automatic)  
**Your Website:** Permanently online!

---

**🎉 You did it! You now have a professional audio separation website running permanently on the internet, and you didn't need any technical knowledge!**
