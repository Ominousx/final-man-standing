# 🚀 Deploy VCT Survivor to GitHub Pages

## ✅ **What You Need**
- GitHub repository: `Ominousx/final-man-standing`
- GitHub account with Pages enabled

## 🎯 **Step 1: Enable GitHub Pages**

1. **Go to your GitHub repo**: `https://github.com/Ominousx/final-man-standing`
2. **Click "Settings" tab**
3. **Scroll down to "Pages" section**
4. **Under "Source", select "GitHub Actions"**
5. **Click "Save"**

## 🔧 **Step 2: Deploy Your App**

### **Option A: Automatic Deployment (Recommended)**
1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "🚀 Deploy to GitHub Pages"
   git push origin main
   ```

2. **GitHub Actions will automatically:**
   - Build your app
   - Deploy to GitHub Pages
   - Make it available at: `https://Ominousx.github.io/final-man-standing`

### **Option B: Manual Deployment**
1. **Build locally:**
   ```bash
   npm run build
   ```

2. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "🚀 Deploy to GitHub Pages"
   git push origin main
   ```

## 🌐 **Your Live App**
- **URL**: `https://Ominousx.github.io/final-man-standing`
- **Status**: Check the "Actions" tab in your GitHub repo
- **Update Time**: 2-5 minutes after pushing

## 🎮 **Features Ready**
- ✅ **Random match assignments** (one per user)
- ✅ **Persistent picks** (no refresh changes)
- ✅ **Beautiful dark gaming theme**
- ✅ **Real-time leaderboard**
- ✅ **Mobile responsive**
- ✅ **Professional UI/UX**

## 📱 **Share with Friends**
Once deployed, share your live URL:
- **Login screen** - Enter any email to start
- **Match assignment** - Random match for each user
- **Pick system** - Choose winner to survive
- **Leaderboard** - See who's winning

## 🔍 **Troubleshooting**

### **If deployment fails:**
1. Check the "Actions" tab for error messages
2. Ensure your repo is public
3. Verify GitHub Pages is enabled
4. Check that the workflow file exists in `.github/workflows/`

### **If app doesn't load:**
1. Wait 5-10 minutes for deployment
2. Check the Actions tab for completion
3. Verify the URL is correct
4. Clear browser cache

## 🎉 **You're All Set!**
Your VCT Survivor app will be live and ready for your friends to play!

**Next time you want to update:**
- Just push to GitHub
- GitHub Actions will automatically redeploy
- Your app stays up-to-date! 🚀
