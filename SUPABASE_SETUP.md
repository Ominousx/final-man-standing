# 🚀 Supabase Setup Guide for VCT Survivor

This guide will help you set up Supabase as the database for your VCT Survivor app.

## 📋 Prerequisites

- A Supabase account (free at [supabase.com](https://supabase.com))
- Node.js and npm installed
- Your VCT Survivor app running locally

## 🗄️ Step 1: Create Supabase Project

1. **Go to [supabase.com](https://supabase.com)** and sign up/login
2. **Click "New Project"**
3. **Choose your organization**
4. **Fill in project details:**
   - Name: `vct-survivor` (or any name you prefer)
   - Database Password: Create a strong password
   - Region: Choose closest to your users
5. **Click "Create new project"**
6. **Wait for setup to complete** (usually 2-3 minutes)

## 🔑 Step 2: Get API Keys

1. **In your project dashboard, go to Settings → API**
2. **Copy these values:**
   - **Project URL** (looks like: `https://abcdefghijklmnop.supabase.co`)
   - **anon public key** (starts with `eyJ...`)

## 🌍 Step 3: Update Environment Variables

1. **Open `.env.local` in your project root**
2. **Replace the placeholder values:**

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

3. **Save the file**

## 🗃️ Step 4: Create Database Tables

1. **In Supabase dashboard, go to SQL Editor**
2. **Click "New query"**
3. **Copy and paste the contents of `supabase-schema.sql`**
4. **Click "Run"**

This will create:
- `users` table for player data
- `matches` table for tournament matches
- `picks` table for user predictions
- Proper indexes and security policies

## 🔒 Step 5: Configure Authentication (Optional)

For now, we're using email-based authentication without Supabase Auth. If you want to add proper authentication later:

1. **Go to Authentication → Settings**
2. **Enable email confirmations** (optional)
3. **Configure social providers** (optional)

## 🧪 Step 6: Test the Setup

1. **Restart your Next.js development server:**
   ```bash
   npm run dev
   ```

2. **Open your app in the browser**
3. **Try logging in with an email**
4. **Check the browser console for any errors**

## 📊 Step 7: Verify Data

1. **In Supabase dashboard, go to Table Editor**
2. **Check that tables were created:**
   - `users` - should show new users when they log in
   - `matches` - should show sample matches
   - `picks` - should show user predictions

## 🚨 Troubleshooting

### Common Issues:

1. **"Invalid API key" error:**
   - Check your `.env.local` file
   - Make sure you copied the `anon` key, not the `service_role` key

2. **"Table doesn't exist" error:**
   - Make sure you ran the SQL schema
   - Check the Table Editor in Supabase

3. **"Row Level Security" errors:**
   - The schema includes RLS policies
   - Make sure you ran the complete SQL file

4. **CORS errors:**
   - Supabase handles CORS automatically
   - If you get CORS errors, check your environment variables

### Debug Steps:

1. **Check browser console for errors**
2. **Verify environment variables are loaded:**
   ```javascript
   console.log(process.env.NEXT_PUBLIC_SUPABASE_URL)
   ```
3. **Check Supabase dashboard for failed requests**
4. **Verify table structure matches the schema**

## 🔄 Next Steps

Once Supabase is working:

1. **Add real-time subscriptions** for live leaderboard updates
2. **Implement proper user authentication** with Supabase Auth
3. **Add admin panel** for managing matches
4. **Set up automated backups** and monitoring

## 📚 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

## 🆘 Need Help?

- Check the [Supabase Discord](https://discord.supabase.com)
- Review [Supabase GitHub issues](https://github.com/supabase/supabase)
- Check the browser console for specific error messages

---

**🎉 Congratulations!** Your VCT Survivor app now has a real database instead of localStorage!

