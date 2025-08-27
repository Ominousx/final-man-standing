// Data management for VCT Survivor app
export interface User {
  id: string;
  name: string;
  email: string;
  isAlive: boolean;
  wins: number;
  losses: number;
  rank: number;
  eliminatedAt?: string;
}

export interface Match {
  id: string;
  teamA: string;
  teamB: string;
  stage: string;
  status: 'upcoming' | 'in-progress' | 'completed';
  winner?: string;
  startTime: string;
}

export interface UserPick {
  id: string;
  userId: string;
  matchId: string;
  selectedTeam: string;
  isCorrect?: boolean;
  timestamp: string;
}

// Mock data
const mockMatches: Match[] = [
  {
    id: "UF-1-A",
    teamA: "Sentinels",
    teamB: "G2",
    stage: "Upper Final",
    status: "upcoming",
    startTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: "LF-1-B",
    teamA: "NRG",
    teamB: "Cloud9",
    stage: "Lower Final",
    status: "upcoming",
    startTime: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString()
  }
];

const mockUsers: User[] = [
  {
    id: "user1",
    name: "Player One",
    email: "player1@example.com",
    isAlive: true,
    wins: 3,
    losses: 0,
    rank: 1
  }
];

const mockPicks: UserPick[] = [];

// Storage keys
const STORAGE_KEYS = {
  USERS: 'vct_survivor_users',
  MATCHES: 'vct_survivor_matches',
  PICKS: 'vct_survivor_picks'
};

// Helper functions
function loadFromStorage<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue;
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
}

function saveToStorage<T>(key: string, value: T): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
  }
}

function initializeData() {
  const users = loadFromStorage(STORAGE_KEYS.USERS, mockUsers);
  const matches = loadFromStorage(STORAGE_KEYS.MATCHES, mockMatches);
  const picks = loadFromStorage(STORAGE_KEYS.PICKS, mockPicks);
  return { users, matches, picks };
}

export function getUser(email: string): User {
  const { users } = initializeData();
  let user = users.find(u => u.email === email);
  
  if (!user) {
    user = {
      id: `user_${Date.now()}`,
      name: email.split('@')[0],
      email,
      isAlive: true,
      wins: 0,
      losses: 0,
      rank: users.length + 1
    };
    users.push(user);
    saveToStorage(STORAGE_KEYS.USERS, users);
  }
  
  return user;
}

export function getUserCurrentMatch(userId: string): Match | null {
  const { users, matches, picks } = initializeData();
  const user = users.find(u => u.id === userId);
  if (!user || !user.isAlive) return null;
  
  const userPicks = picks.filter(p => p.userId === userId);
  const completedMatches = userPicks.filter(p => {
    const match = matches.find(m => m.id === p.matchId);
    return match && match.status === 'completed';
  });
  
  if (completedMatches.length > 0) {
    const availableMatches = matches.filter(m => 
      m.status === 'upcoming' && 
      !userPicks.some(p => p.matchId === m.id)
    );
    if (availableMatches.length > 0) {
      return availableMatches[0];
    }
  }
  
  const firstMatch = matches.find(m => m.status === 'upcoming');
  return firstMatch || null;
}

export function assignMatchToUser(userId: string): Match | null {
  const { users, matches, picks } = initializeData();
  const user = users.find(u => u.id === userId);
  if (!user || !user.isAlive) return null;
  
  const userPicks = picks.filter(p => p.userId === userId);
  const availableMatches = matches.filter(m => 
    m.status === 'upcoming' && 
    !userPicks.some(p => p.matchId === m.id)
  );
  
  return availableMatches.length > 0 ? availableMatches[0] : null;
}

export function submitPick(userId: string, matchId: string, selectedTeam: string): boolean {
  const { users, matches, picks } = initializeData();
  const user = users.find(u => u.id === userId);
  const match = matches.find(m => m.id === matchId);
  
  if (!user || !match || match.status !== 'upcoming') {
    return false;
  }
  
  const existingPick = picks.find(p => p.userId === userId && p.matchId === matchId);
  if (existingPick) {
    return false;
  }
  
  const newPick: UserPick = {
    id: `pick_${Date.now()}`,
    userId,
    matchId,
    selectedTeam,
    timestamp: new Date().toISOString()
  };
  
  picks.push(newPick);
  saveToStorage(STORAGE_KEYS.PICKS, picks);
  return true;
}

export function completeMatch(matchId: string, winner: string): boolean {
  const { users, matches, picks } = initializeData();
  const match = matches.find(m => m.id === matchId);
  if (!match || match.status !== 'upcoming') {
    return false;
  }
  
  match.status = 'completed';
  match.winner = winner;
  
  const matchPicks = picks.filter(p => p.matchId === matchId);
  matchPicks.forEach(pick => {
    pick.isCorrect = pick.selectedTeam === winner;
    const user = users.find(u => u.id === pick.userId);
    if (user) {
      if (pick.isCorrect) {
        user.wins++;
      } else {
        user.losses++;
        user.isAlive = false;
        user.eliminatedAt = new Date().toISOString();
      }
    }
  });
  
  users.sort((a, b) => b.wins - a.wins);
  users.forEach((user, index) => {
    user.rank = index + 1;
  });
  
  saveToStorage(STORAGE_KEYS.MATCHES, matches);
  saveToStorage(STORAGE_KEYS.USERS, users);
  saveToStorage(STORAGE_KEYS.PICKS, picks);
  
  return true;
}

export function getLeaderboard(): User[] {
  const { users } = initializeData();
  return users.sort((a, b) => a.rank - b.rank);
}

export function getUserPicks(userId: string): UserPick[] {
  const { picks } = initializeData();
  return picks.filter(p => p.userId === userId);
}

export function getUserStats(userId: string): {
  totalPicks: number;
  wins: number;
  losses: number;
  pending: number;
  winRate: string;
} | null {
  const { users, picks } = initializeData();
  const user = users.find(u => u.id === userId);
  if (!user) return null;
  
  const userPicks = picks.filter(p => p.userId === userId);
  const completedPicks = userPicks.filter(p => p.isCorrect !== undefined);
  const pendingPicks = userPicks.filter(p => p.isCorrect === undefined);
  
  return {
    totalPicks: userPicks.length,
    wins: user.wins,
    losses: user.losses,
    pending: pendingPicks.length,
    winRate: completedPicks.length > 0 ? (user.wins / completedPicks.length * 100).toFixed(1) : '0.0'
  };
}
