// Data management for VCT Survivor app

export interface User {
  id: string;
  email: string;
  name: string;
  isAlive: boolean;
  wins: number;
  losses: number;
  currentMatchId?: string;
  eliminatedAt?: string;
}

export interface Match {
  id: string;
  teamA: string;
  teamB: string;
  startTime: string;
  stage: string;
  status: "upcoming" | "live" | "completed";
  winner?: string;
  assignedUsers: string[]; // Track which users are assigned to this match
}

export interface UserPick {
  userId: string;
  matchId: string;
  pickedTeam: string;
  pickTime: string;
  result?: "win" | "loss" | "pending";
}

// Mock data - in a real app, this would come from a database
const mockMatches: Match[] = [
  {
    id: "UF-1-A",
    teamA: "Sentinels",
    teamB: "G2",
    startTime: "2024-01-20T15:00:00Z",
    stage: "Lower Decider",
    status: "upcoming",
    assignedUsers: []
  },
  {
    id: "UF-1-B",
    teamA: "NRG",
    teamB: "Cloud9",
    startTime: "2024-01-21T15:00:00Z",
    stage: "Upper Final",
    status: "upcoming",
    assignedUsers: []
  },
  {
    id: "UF-2-A",
    teamA: "Team Liquid",
    teamB: "NAVI",
    startTime: "2024-01-22T15:00:00Z",
    stage: "Grand Final",
    status: "upcoming",
    assignedUsers: []
  },
  {
    id: "UF-2-B",
    teamA: "Paper Rex",
    teamB: "TALON",
    startTime: "2024-01-23T15:00:00Z",
    stage: "Championship",
    status: "upcoming",
    assignedUsers: []
  }
];

const mockUsers: User[] = [];
const mockPicks: UserPick[] = [];

// Local storage keys
const STORAGE_KEYS = {
  USERS: 'vct_survivor_users',
  MATCHES: 'vct_survivor_matches',
  PICKS: 'vct_survivor_picks'
};

// Load data from localStorage
function loadFromStorage<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue;
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : defaultValue;
  } catch {
    return defaultValue;
  }
}

// Save data to localStorage
function saveToStorage<T>(key: string, data: T): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
  }
}

// Initialize data
export function initializeData() {
  // Load existing data or use defaults
  const users = loadFromStorage(STORAGE_KEYS.USERS, mockUsers);
  const matches = loadFromStorage(STORAGE_KEYS.MATCHES, mockMatches);
  const picks = loadFromStorage(STORAGE_KEYS.PICKS, mockPicks);
  
  return { users, matches, picks };
}

// Get or create user
export function getUser(email: string): User {
  const { users } = initializeData();
  let user = users.find(u => u.email === email);
  
  if (!user) {
    user = {
      id: `user_${Date.now()}`,
      email,
      name: email.split('@')[0],
      isAlive: true,
      wins: 0,
      losses: 0
    };
    users.push(user);
    saveToStorage(STORAGE_KEYS.USERS, users);
  }
  
  return user;
}

// Get user's current match assignment
export function getUserCurrentMatch(userId: string): Match | null {
  const { users, matches } = initializeData();
  const user = users.find(u => u.id === userId);
  
  if (!user || !user.currentMatchId) return null;
  
  return matches.find(m => m.id === user.currentMatchId) || null;
}

// Assign a new match to user (only if they don't have one or previous is completed)
export function assignMatchToUser(userId: string): Match | null {
  const { users, matches } = initializeData();
  const user = users.find(u => u.id === userId);
  
  if (!user) return null;
  
  // Check if user already has a current match
  if (user.currentMatchId) {
    const currentMatch = matches.find(m => m.id === user.currentMatchId);
    if (currentMatch && currentMatch.status !== "completed") {
      return currentMatch; // Return existing match
    }
  }
  
  // Find available matches (not completed, not full)
  const availableMatches = matches.filter(m => 
    m.status === "upcoming" && 
    m.assignedUsers.length < 100 && // Limit users per match
    !m.assignedUsers.includes(userId)
  );
  
  if (availableMatches.length === 0) return null;
  
  // Randomly select a match
  const randomIndex = Math.floor(Math.random() * availableMatches.length);
  const selectedMatch = availableMatches[randomIndex];
  
  // Update user's current match
  user.currentMatchId = selectedMatch.id;
  selectedMatch.assignedUsers.push(userId);
  
  // Save changes
  saveToStorage(STORAGE_KEYS.USERS, users);
  saveToStorage(STORAGE_KEYS.MATCHES, matches);
  
  return selectedMatch;
}

// Submit user's pick
export function submitPick(userId: string, matchId: string, pickedTeam: string): boolean {
  const { users, matches, picks } = initializeData();
  
  // Check if user is assigned to this match
  const user = users.find(u => u.id === userId);
  const match = matches.find(m => m.id === matchId);
  
  if (!user || !match || user.currentMatchId !== matchId) {
    return false;
  }
  
  // Check if user already picked
  const existingPick = picks.find(p => p.userId === userId && p.matchId === matchId);
  if (existingPick) {
    return false;
  }
  
  // Create new pick
  const newPick: UserPick = {
    userId,
    matchId,
    pickedTeam,
    pickTime: new Date().toISOString(),
    result: "pending"
  };
  
  picks.push(newPick);
  saveToStorage(STORAGE_KEYS.PICKS, picks);
  
  return true;
}

// Complete a match and update results
export function completeMatch(matchId: string, winner: string): void {
  const { matches, picks, users } = initializeData();
  const match = matches.find(m => m.id === matchId);
  
  if (!match) return;
  
  // Update match status
  match.status = "completed";
  match.winner = winner;
  
  // Update all picks for this match
  picks.forEach(pick => {
    if (pick.matchId === matchId) {
      pick.result = pick.pickedTeam === winner ? "win" : "loss";
    }
  });
  
  // Update user stats and assign new matches
  users.forEach(user => {
    if (user.currentMatchId === matchId) {
      const userPick = picks.find(p => p.userId === user.id && p.matchId === matchId);
      
      if (userPick) {
        if (userPick.result === "win") {
          user.wins++;
        } else {
          user.losses++;
          user.isAlive = false;
          user.eliminatedAt = `Stage ${match.stage}`;
        }
        
        // Clear current match so they can get a new one
        user.currentMatchId = undefined;
      }
    }
  });
  
  // Save all changes
  saveToStorage(STORAGE_KEYS.MATCHES, matches);
  saveToStorage(STORAGE_KEYS.PICKS, picks);
  saveToStorage(STORAGE_KEYS.USERS, users);
}

// Get leaderboard
export function getLeaderboard(): User[] {
  const { users } = initializeData();
  
  return users
    .sort((a, b) => {
      // Alive users first, then by wins (descending)
      if (a.isAlive !== b.isAlive) {
        return b.isAlive ? 1 : -1;
      }
      return b.wins - a.wins;
    })
    .map((user, index) => ({
      ...user,
      rank: index + 1
    }));
}

// Get user's pick history
export function getUserPicks(userId: string): UserPick[] {
  const { picks } = initializeData();
  return picks.filter(p => p.userId === userId);
}

// Get user stats
export function getUserStats(userId: string) {
  const { users, picks } = initializeData();
  const user = users.find(u => u.id === userId);
  
  if (!user) return null;
  
  const userPicks = picks.filter(p => p.userId === userId);
  const wins = userPicks.filter(p => p.result === "win").length;
  const losses = userPicks.filter(p => p.result === "loss").length;
  const pending = userPicks.filter(p => p.result === "pending").length;
  
  return {
    ...user,
    totalPicks: userPicks.length,
    wins,
    losses,
    pending
  };
}
