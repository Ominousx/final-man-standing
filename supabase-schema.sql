-- Enable Row Level Security
ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS picks ENABLE ROW LEVEL SECURITY;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  is_alive BOOLEAN DEFAULT true,
  wins INTEGER DEFAULT 0,
  losses INTEGER DEFAULT 0,
  rank INTEGER DEFAULT 1,
  current_match_id UUID,
  eliminated_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  team_a TEXT NOT NULL,
  team_b TEXT NOT NULL,
  stage TEXT NOT NULL,
  status TEXT DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'in-progress', 'completed')),
  winner TEXT,
  start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Picks table
CREATE TABLE IF NOT EXISTS picks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
  selected_team TEXT NOT NULL,
  is_correct BOOLEAN,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_current_match ON users(current_match_id);
CREATE INDEX IF NOT EXISTS idx_picks_user_match ON picks(user_id, match_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);

-- Row Level Security Policies
-- Users can read their own data and public leaderboard data
CREATE POLICY "Users can view own data" ON users
  FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can view leaderboard" ON users
  FOR SELECT USING (true);

CREATE POLICY "Users can update own data" ON users
  FOR UPDATE USING (auth.uid()::text = id::text);

-- Matches are readable by all authenticated users
CREATE POLICY "Matches are viewable by all" ON matches
  FOR SELECT USING (true);

-- Picks are readable by the user who made them
CREATE POLICY "Users can view own picks" ON picks
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create own picks" ON picks
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Insert some sample data
INSERT INTO matches (team_a, team_b, stage, status) VALUES
  ('Sentinels', 'G2', 'Upper Final', 'upcoming'),
  ('NRG', 'Cloud9', 'Lower Final', 'upcoming'),
  ('Paper Rex', 'Team Liquid', 'Grand Final', 'upcoming')
ON CONFLICT DO NOTHING;

