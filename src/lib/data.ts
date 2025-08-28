// Data management for VCT Survivor app using Supabase
import { supabase, TABLES } from './supabase'

export interface User {
  id: string;
  name: string;
  email: string;
  is_alive: boolean;
  wins: number;
  losses: number;
  rank: number;
  eliminated_at?: string;
  current_match_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Match {
  id: string;
  team_a: string;
  team_b: string;
  stage: string;
  status: 'upcoming' | 'in-progress' | 'completed';
  winner?: string;
  start_time: string;
  created_at: string;
  updated_at: string;
}

export interface UserPick {
  id: string;
  user_id: string;
  match_id: string;
  selected_team: string;
  is_correct?: boolean;
  timestamp: string;
  created_at: string;
}

// Helper function to handle Supabase errors
function handleSupabaseError(error: any, operation: string) {
  console.error(`Supabase ${operation} error:`, error);
  throw new Error(`Failed to ${operation}: ${error.message}`);
}

export async function getUser(email: string): Promise<User> {
  try {
    console.log(`🔍 getUser called for email: ${email}`);
    
    // Check if user exists
    const { data: existingUser, error: fetchError } = await supabase
      .from(TABLES.USERS)
      .select('*')
      .eq('email', email)
      .single();

    if (fetchError && fetchError.code !== 'PGRST116') {
      console.log(`❌ Error fetching user:`, fetchError);
      throw fetchError;
    }

    if (existingUser) {
      console.log(`✅ Found existing user:`, existingUser);
      return existingUser;
    }

    console.log(`🆕 User not found, creating new user...`);
    
    // Create new user
    const newUser = {
      name: email.split('@')[0],
      email,
      is_alive: true,
      wins: 0,
      losses: 0,
      rank: 1
    };

    console.log(`📝 Inserting new user:`, newUser);

    const { data: user, error: insertError } = await supabase
      .from(TABLES.USERS)
      .insert(newUser)
      .select()
      .single();

    if (insertError) {
      console.error(`❌ Failed to insert user:`, insertError);
      throw insertError;
    }
    
    console.log(`✅ Successfully created user:`, user);
    return user;
  } catch (error) {
    console.error(`💥 Error in getUser:`, error);
    handleSupabaseError(error, 'get user');
  }
}

export async function getUserCurrentMatch(userId: string): Promise<Match | null> {
  try {
    console.log(`🔍 getUserCurrentMatch called for user: ${userId}`);
    
    // Get user data
    const { data: user, error: userError } = await supabase
      .from(TABLES.USERS)
      .select('*')
      .eq('id', userId)
      .single();

    if (userError) throw userError;
    if (!user || !user.is_alive) return null;

    console.log(`👤 User data:`, {
      id: user.id,
      email: user.email,
      current_match_id: user.current_match_id,
      is_alive: user.is_alive
    });

    // FIRST PRIORITY: Check if user already has a match assigned
    if (user.current_match_id) {
      console.log(`🎯 User has current_match_id: ${user.current_match_id}`);
      
      const { data: assignedMatch, error: matchError } = await supabase
        .from(TABLES.MATCHES)
        .select('*')
        .eq('id', user.current_match_id)
        .eq('status', 'upcoming')
        .single();

      if (matchError && matchError.code !== 'PGRST116') throw matchError;
      if (assignedMatch) {
        console.log(`✅ Returning existing assigned match: ${assignedMatch.team_a} vs ${assignedMatch.team_b}`);
        return assignedMatch;
      } else {
        console.log(`❌ Assigned match not found or not upcoming`);
      }
    } else {
      console.log(`❌ User has NO current_match_id`);
    }

    // SECOND PRIORITY: Check if user has a pending pick
    const { data: pendingPick, error: pickError } = await supabase
      .from(TABLES.PICKS)
      .select('*')
      .eq('user_id', userId)
      .is('is_correct', null)
      .single();

    if (pickError && pickError.code !== 'PGRST116') throw pickError;

    if (pendingPick) {
      const { data: match, error: matchError } = await supabase
        .from(TABLES.MATCHES)
        .select('*')
        .eq('id', pendingPick.match_id)
        .eq('status', 'upcoming')
        .single();

      if (matchError && matchError.code !== 'PGRST116') throw matchError;
      if (match) {
        console.log(`User ${userId} has pending pick for match: ${match.team_a} vs ${match.team_b}`);
        return match;
      }
    }

    // Get user's completed picks
    const { data: userPicks, error: picksError } = await supabase
      .from(TABLES.PICKS)
      .select('*')
      .eq('user_id', userId)
      .not('is_correct', 'is', null);

    if (picksError) throw picksError;

    // If no completed picks, assign first available match
    if (userPicks.length === 0) {
      const { data: firstMatch, error: matchError } = await supabase
        .from(TABLES.MATCHES)
        .select('*')
        .eq('status', 'upcoming')
        .limit(1)
        .single();

      if (matchError && matchError.code !== 'PGRST116') throw matchError;
      if (firstMatch) {
        // Assign match to user
        console.log(`🔄 Assigning first match to user: ${firstMatch.id} (${firstMatch.team_a} vs ${firstMatch.team_b})`);
        
        const { error: updateError } = await supabase
          .from(TABLES.USERS)
          .update({ current_match_id: firstMatch.id })
          .eq('id', userId);

        if (updateError) {
          console.error(`❌ Failed to update user with current_match_id:`, updateError);
          throw updateError;
        }
        
        console.log(`✅ Successfully assigned match ${firstMatch.id} to user ${userId}`);
        return firstMatch;
      }
      return null;
    }

    // Check if user won their last match
    const lastCompletedPick = userPicks[userPicks.length - 1];
    if (lastCompletedPick.is_correct) {
      // User won, find next available match
      const { data: availableMatches, error: matchError } = await supabase
        .from(TABLES.MATCHES)
        .select('*')
        .eq('status', 'upcoming')
        .not('id', 'in', `(${userPicks.map(p => p.match_id).join(',')})`);

      if (matchError) throw matchError;
      if (availableMatches && availableMatches.length > 0) {
        // Assign next match
        const { error: updateError } = await supabase
          .from(TABLES.USERS)
          .update({ current_match_id: availableMatches[0].id })
          .eq('id', userId);

        if (updateError) throw updateError;
        console.log(`User ${userId} assigned next match after win: ${availableMatches[0].team_a} vs ${availableMatches[0].team_b}`);
        return availableMatches[0];
      }
    }

    // User lost their last match - they're eliminated
    console.log(`User ${userId} is eliminated - no more matches`);
    return null;
  } catch (error) {
    handleSupabaseError(error, 'get user current match');
  }
}

export async function assignMatchToUser(userId: string): Promise<Match | null> {
  return getUserCurrentMatch(userId);
}

export async function submitPick(userId: string, matchId: string, selectedTeam: string): Promise<boolean> {
  try {
    // Check if user and match exist
    const { data: user, error: userError } = await supabase
      .from(TABLES.USERS)
      .select('*')
      .eq('id', userId)
      .single();

    if (userError) throw userError;
    if (!user || !user.is_alive) return false;

    const { data: match, error: matchError } = await supabase
      .from(TABLES.MATCHES)
      .select('*')
      .eq('id', matchId)
      .eq('status', 'upcoming')
      .single();

    if (matchError) throw matchError;
    if (!match) return false;

    // Check if pick already exists
    const { data: existingPick, error: pickError } = await supabase
      .from(TABLES.PICKS)
      .select('*')
      .eq('user_id', userId)
      .eq('match_id', matchId)
      .single();

    if (pickError && pickError.code !== 'PGRST116') throw pickError;
    if (existingPick) return false;

    // Create new pick
    const newPick = {
      user_id: userId,
      match_id: matchId,
      selected_team: selectedTeam
    };

    const { error: insertError } = await supabase
      .from(TABLES.PICKS)
      .insert(newPick);

    if (insertError) throw insertError;
    return true;
  } catch (error) {
    handleSupabaseError(error, 'submit pick');
  }
}

export async function completeMatch(matchId: string, winner: string): Promise<boolean> {
  try {
    // Update match status
    const { error: matchError } = await supabase
      .from(TABLES.MATCHES)
      .update({ 
        status: 'completed', 
        winner,
        updated_at: new Date().toISOString()
      })
      .eq('id', matchId)
      .eq('status', 'upcoming');

    if (matchError) throw matchError;

    // Get all picks for this match
    const { data: matchPicks, error: picksError } = await supabase
      .from(TABLES.PICKS)
      .select('*')
      .eq('match_id', matchId);

    if (picksError) throw picksError;

    // Update user stats and clear current match
    for (const pick of matchPicks) {
      const isCorrect = pick.selected_team === winner;
      
      const { error: pickUpdateError } = await supabase
        .from(TABLES.PICKS)
        .update({ is_correct: isCorrect })
        .eq('id', pick.id);

      if (pickUpdateError) throw pickUpdateError;

      // Update user stats
      const updateData = isCorrect 
        ? { wins: pick.wins + 1 }
        : { 
            losses: pick.losses + 1, 
            is_alive: false, 
            eliminated_at: new Date().toISOString() 
          };

      const { error: userUpdateError } = await supabase
        .from(TABLES.USERS)
        .update(updateData)
        .eq('id', pick.user_id);

      if (userUpdateError) throw userUpdateError;

      // Clear current match assignment
      const { error: clearError } = await supabase
        .from(TABLES.USERS)
        .update({ current_match_id: null })
        .eq('id', pick.user_id);

      if (clearError) throw clearError;
    }

    // Update rankings
    await updateRankings();
    
    return true;
  } catch (error) {
    handleSupabaseError(error, 'complete match');
  }
}

async function updateRankings(): Promise<void> {
  try {
    const { data: users, error: usersError } = await supabase
      .from(TABLES.USERS)
      .select('*')
      .order('wins', { ascending: false });

    if (usersError) throw usersError;

    // Update rankings
    for (let i = 0; i < users.length; i++) {
      const { error: updateError } = await supabase
        .from(TABLES.USERS)
        .update({ rank: i + 1 })
        .eq('id', users[i].id);

      if (updateError) throw updateError;
    }
  } catch (error) {
    handleSupabaseError(error, 'update rankings');
  }
}

export async function getLeaderboard(): Promise<User[]> {
  try {
    const { data: users, error } = await supabase
      .from(TABLES.USERS)
      .select('*')
      .order('rank', { ascending: true });

    if (error) throw error;
    return users || [];
  } catch (error) {
    handleSupabaseError(error, 'get leaderboard');
  }
}

export async function getUserPicks(userId: string): Promise<UserPick[]> {
  try {
    const { data: picks, error } = await supabase
      .from(TABLES.PICKS)
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: true });

    if (error) throw error;
    return picks || [];
  } catch (error) {
    handleSupabaseError(error, 'get user picks');
  }
}

export async function getUserStats(userId: string): Promise<{
  totalPicks: number;
  wins: number;
  losses: number;
  pending: number;
  winRate: string;
} | null> {
  try {
    const { data: user, error: userError } = await supabase
      .from(TABLES.USERS)
      .select('*')
      .eq('id', userId)
      .single();

    if (userError) throw userError;
    if (!user) return null;

    const { data: picks, error: picksError } = await supabase
      .from(TABLES.PICKS)
      .select('*')
      .eq('user_id', userId);

    if (picksError) throw picksError;

    const completedPicks = picks.filter(p => p.is_correct !== null);
    const pendingPicks = picks.filter(p => p.is_correct === null);

    return {
      totalPicks: picks.length,
      wins: user.wins,
      losses: user.losses,
      pending: pendingPicks.length,
      winRate: completedPicks.length > 0 ? (user.wins / completedPicks.length * 100).toFixed(1) : '0.0'
    };
  } catch (error) {
    handleSupabaseError(error, 'get user stats');
  }
}
