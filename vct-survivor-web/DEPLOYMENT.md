# 🚀 Deployment Guide - VCT Survivor

This guide will help you deploy your VCT Survivor app so your friends can play it!

## 🌟 Quick Deploy Options

### Option 1: Vercel (Recommended - Free & Easy)

1. **Fork this repository** to your GitHub account
2. **Go to [Vercel.com](https://vercel.com)** and sign up with GitHub
3. **Click "New Project"** and import your forked repository
4. **Deploy automatically** - Vercel will detect it's a Next.js app
5. **Get your live URL** - Share with friends!

**✅ Pros:** Free, automatic deployments, great performance  
**⏱️ Time:** 2 minutes

### Option 2: Netlify (Free Alternative)

1. **Fork this repository** to your GitHub account
2. **Go to [Netlify.com](https://netlify.com)** and sign up with GitHub
3. **Click "New site from Git"** and connect your repository
4. **Set build command:** `npm run build`
5. **Set publish directory:** `.next`
6. **Deploy!**

**✅ Pros:** Free, good performance, easy setup  
**⏱️ Time:** 3 minutes

### Option 3: Railway (Free Tier)

1. **Fork this repository** to your GitHub account
2. **Go to [Railway.app](https://railway.app)** and sign up with GitHub
3. **Click "New Project"** → "Deploy from GitHub repo"
4. **Select your repository** and deploy
5. **Get your live URL!**

**✅ Pros:** Free tier, good performance  
**⏱️ Time:** 5 minutes

---

## 🔧 Manual Deployment Steps

### Prerequisites
- Node.js 18+ installed
- Git installed
- GitHub account

### Step 1: Prepare Your Repository

```bash
# Clone your repository
git clone https://github.com/yourusername/vct-survivor.git
cd vct-survivor

# Install dependencies
npm install

# Test locally
npm run dev
```

### Step 2: Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --yes
```

### Step 3: Get Your Live URL

After deployment, Vercel will give you:
- **Production URL** (e.g., `https://vct-survivor-abc123.vercel.app`)
- **Preview URLs** for each branch

---

## 🌐 Custom Domain (Optional)

### Add Custom Domain in Vercel

1. **Go to your project dashboard** in Vercel
2. **Click "Settings"** → "Domains"
3. **Add your domain** (e.g., `vctsurvivor.com`)
4. **Update DNS records** as instructed
5. **Wait for propagation** (up to 24 hours)

---

## 📱 Share with Friends

### Your Live App URL
Once deployed, share this URL with your friends:
```
https://your-app-name.vercel.app
```

### Social Media Ready
- **Twitter**: "🎮 Just launched VCT Survivor! Predict Valorant matches and become the last one standing! Play now: [URL]"
- **Discord**: "🏆 VCT Survivor is live! Join the tournament: [URL]"
- **Instagram**: "New Valorant prediction game is live! Link in bio 🎯"

---

## 🔄 Automatic Updates

### GitHub Actions (Already Set Up)
- **Automatic deployment** on every push to main branch
- **No manual work** needed after initial setup
- **Instant updates** when you make changes

### Manual Updates
```bash
# Make your changes
git add .
git commit -m "Update app features"
git push origin main

# Vercel automatically deploys!
```

---

## 🆘 Troubleshooting

### Common Issues

**Build Fails**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Deployment Errors**
- Check your Node.js version (18+ required)
- Verify all dependencies are installed
- Check build logs in Vercel dashboard

**App Not Working**
- Verify environment variables are set
- Check browser console for errors
- Test locally first with `npm run dev`

---

## 📊 Performance Tips

### Optimize for Production
```bash
# Build optimization
npm run build

# Analyze bundle size
npm run analyze

# Test production build
npm start
```

### Vercel Optimizations
- **Automatic image optimization**
- **Edge functions** for better performance
- **Global CDN** for fast loading worldwide

---

## 🎯 Next Steps

1. **Deploy your app** using one of the options above
2. **Share the URL** with your friends
3. **Monitor usage** in your hosting dashboard
4. **Make updates** and watch them deploy automatically!

---

## 🆘 Need Help?

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)
- **GitHub Issues**: Open an issue in your repository

---

**Happy Deploying! 🚀✨**

Your friends will love playing VCT Survivor!
