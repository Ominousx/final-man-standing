"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  getUser, 
  assignMatchToUser, 
  getUserCurrentMatch, 
  submitPick, 
  getLeaderboard, 
  getUserStats,
  getUserPicks,
  completeMatch,
  type User,
  type Match,
  type UserPick
} from "@/lib/data";

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [email, setEmail] = useState("");
  const [currentMatch, setCurrentMatch] = useState<Match | null>(null);
  const [leaderboard, setLeaderboard] = useState<User[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>("");
  const [userStats, setUserStats] = useState<{
    totalPicks: number;
    wins: number;
    losses: number;
    pending: number;
    winRate: string;
  } | null>(null);
  const [hasPicked, setHasPicked] = useState(false);
  const [isRevealingMatch, setIsRevealingMatch] = useState(false);
  const [showMatch, setShowMatch] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  // Load user data and match assignment
  useEffect(() => {
    if (user) {
      const loadUserData = async () => {
        // Start match reveal animation
        setIsRevealingMatch(true);
        setShowMatch(false);
        
        // Simulate match generation delay
        setTimeout(async () => {
          try {
            // Get or assign current match
            let match = await getUserCurrentMatch(user.id);
            if (!match) {
              match = await assignMatchToUser(user.id);
            }
            setCurrentMatch(match);

            // Load user stats
            const stats = await getUserStats(user.id);
            setUserStats(stats);

            // Check if user already picked for current match
            if (match) {
              const picks = await getUserPicks(user.id);
              const hasPickedForMatch = picks.some(p => p.match_id === match!.id);
              setHasPicked(hasPickedForMatch);
            }

            // Load leaderboard
            const leaderboardData = await getLeaderboard();
            setLeaderboard(leaderboardData);
            
            // End reveal animation and show match
            setIsRevealingMatch(false);
            setTimeout(() => setShowMatch(true), 300);
          } catch (error) {
            console.error('Error loading user data:', error);
            setIsRevealingMatch(false);
            setShowMatch(true);
          }
        }, 2000); // 2 second delay for dramatic effect
      };

      loadUserData();
    }
  }, [user]);

  const handleLogin = async () => {
    if (email && email.includes('@')) {
      try {
        const newUser = await getUser(email);
        setUser(newUser);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Login error:', error);
      }
    }
  };

  const handlePick = async () => {
    if (selectedTeam && currentMatch && user) {
      try {
        const success = await submitPick(user.id, currentMatch.id, selectedTeam);
        if (success) {
          setHasPicked(true);
          const stats = await getUserStats(user.id);
          setUserStats(stats);
          setSelectedTeam("");
        }
      } catch (error) {
        console.error('Pick error:', error);
      }
    }
  };

  const handleCompleteMatch = async (winner: string) => {
    if (currentMatch) {
      try {
        await completeMatch(currentMatch.id, winner);
        if (user) {
          // Check if user won or lost
          const picks = await getUserPicks(user.id);
          const userPick = picks.find(p => p.match_id === currentMatch.id);
          const userWon = userPick?.selected_team === winner;
          
          if (userWon) {
            // Show success message
            setShowSuccessMessage(true);
            setTimeout(() => setShowSuccessMessage(false), 3000);
          }
          
          // Start new match reveal animation
          setIsRevealingMatch(true);
          setShowMatch(false);
          
          setTimeout(async () => {
            try {
              let newMatch = await getUserCurrentMatch(user.id);
              if (!newMatch) {
                newMatch = await assignMatchToUser(user.id);
              }
              setCurrentMatch(newMatch);
              const leaderboardData = await getLeaderboard();
              setLeaderboard(leaderboardData);
              const stats = await getUserStats(user.id);
              setUserStats(stats);
              setHasPicked(false);
              
              // End reveal animation and show new match
              setIsRevealingMatch(false);
              setTimeout(() => setShowMatch(true), 300);
            } catch (error) {
              console.error('Error loading new match:', error);
              setIsRevealingMatch(false);
              setShowMatch(true);
            }
          }, 1500); // 1.5 second delay for new match
        }
      } catch (error) {
        console.error('Complete match error:', error);
      }
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl vct-title">VCT SURVIVOR</CardTitle>
            <CardDescription>Official Tournament Prediction Platform</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <Input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="vct-input"
              />
              <Button onClick={handleLogin} className="vct-button w-full">
                Continue
              </Button>
            </div>
            <div className="text-center text-sm text-muted-foreground">
              By continuing, you agree to our Terms of Service and Privacy Policy
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-vct-border bg-vct-dark/80 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-vct-red rounded-lg flex items-center justify-center shadow-lg">
              <span className="text-white font-black text-xl">V</span>
            </div>
            <h1 className="text-3xl vct-title">VCT SURVIVOR</h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="font-semibold">{user?.name}</div>
              <div className="text-sm text-muted-foreground">{user?.email}</div>
            </div>
            <Avatar>
              <AvatarImage src="" />
              <AvatarFallback>{user?.name?.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>
          </div>
        </div>
      </header>

      {showSuccessMessage && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50">
          <div className="bg-vct-red text-white px-8 py-4 rounded-lg shadow-2xl animate-bounce border border-vct-red/50">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🏆</span>
              <span className="font-bold text-lg">CONGRATULATIONS! You've advanced to the next match!</span>
              <span className="text-2xl">🏆</span>
            </div>
          </div>
        </div>
      )}
      
      <div className="container mx-auto px-4 py-8">
        <Tabs defaultValue="home" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-vct-card border border-vct-border p-1 rounded-lg">
            <TabsTrigger value="home" className="data-[state=active]:bg-vct-red data-[state=active]:text-white">Home</TabsTrigger>
            <TabsTrigger value="leaderboard" className="data-[state=active]:bg-vct-red data-[state=active]:text-white">Leaderboard</TabsTrigger>
            <TabsTrigger value="stats" className="data-[state=active]:bg-vct-red data-[state=active]:text-white">My Stats</TabsTrigger>
            <TabsTrigger value="schedule" className="data-[state=active]:bg-vct-red data-[state=active]:text-white">Schedule</TabsTrigger>
          </TabsList>

          <TabsContent value="home" className="space-y-6">
            <div className="text-center">
              <Badge variant={user?.is_alive ? "default" : "destructive"} className="text-lg px-6 py-2">
                {user?.is_alive ? "ALIVE" : "ELIMINATED"}
              </Badge>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card className="game-card">
                  <CardHeader className="vct-card-header">
                    <CardTitle className="vct-card-title text-center">Current Match Assignment</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {isRevealingMatch ? (
                      <div className="text-center space-y-6 py-8">
                        <div className="animate-spin w-16 h-16 border-4 border-primary border-t-transparent rounded-full mx-auto"></div>
                        <div className="space-y-2">
                          <div className="text-2xl font-bold text-primary generating-match">🎲</div>
                          <div className="text-xl font-semibold">Generating Your Match...</div>
                          <div className="text-sm text-muted-foreground">The algorithm is selecting your destiny</div>
                        </div>
                      </div>
                    ) : currentMatch && showMatch ? (
                      <>
                        <div className="text-center text-sm text-muted-foreground match-details-reveal">
                          Match ID: {currentMatch.id} • Stage: {currentMatch.stage}
                        </div>
                        
                        <div className="flex items-center justify-center space-x-8 match-reveal">
                          <div className="text-center">
                            <div className="team-logo bg-secondary flex items-center justify-center mb-2 team-logo-float">
                              <span className="text-2xl">?</span>
                            </div>
                            <div className="font-semibold team-name-reveal">{currentMatch.team_a}</div>
                          </div>
                          
                          <div className="text-2xl font-bold text-vct-red text-center vs-reveal">VS</div>
                          
                          <div className="text-center">
                            <div className="team-logo bg-secondary flex items-center justify-center mb-2 team-logo-float">
                              <span className="text-2xl">?</span>
                            </div>
                            <div className="font-semibold team-name-reveal">{currentMatch.team_b}</div>
                          </div>
                        </div>

                        {hasPicked ? (
                          <div className="text-center pick-status-reveal">
                            <Badge variant="default" className="text-lg px-6 py-2">
                              ✅ Pick Locked
                            </Badge>
                          </div>
                        ) : (
                          <div className="space-y-3 pick-form-reveal">
                            <Select value={selectedTeam} onValueChange={setSelectedTeam}>
                              <SelectTrigger>
                                <SelectValue placeholder="Select winner" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value={currentMatch.team_a}>{currentMatch.team_a}</SelectItem>
                                <SelectItem value={currentMatch.team_b}>{currentMatch.team_b}</SelectItem>
                              </SelectContent>
                            </Select>
                            <Button onClick={handlePick} className="vct-button w-full" disabled={!selectedTeam}>
                              Lock Pick ✅
                            </Button>
                          </div>
                        )}

                        <div className="border-t pt-4 admin-controls-reveal">
                          <div className="text-sm text-muted-foreground mb-2">Admin: Complete Match</div>
                          <div className="flex space-x-2">
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleCompleteMatch(currentMatch.team_a)}
                              className="border-vct-border hover:border-vct-red hover:bg-vct-red/10 text-white"
                            >
                              {currentMatch.team_a} Wins
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleCompleteMatch(currentMatch.team_b)}
                              className="border-vct-border hover:border-vct-red hover:bg-vct-red/10 text-white"
                            >
                              {currentMatch.team_b} Wins
                            </Button>
                          </div>
                        </div>
                      </>
                    ) : !user?.is_alive ? (
                      <div className="text-center space-y-6 py-12">
                        <div className="text-8xl animate-pulse">💀</div>
                        <div className="text-3xl font-bold text-destructive tracking-wider">YOU'RE ELIMINATED!</div>
                        <div className="text-muted-foreground text-lg">
                          Better luck next time! You can still view the leaderboard and stats.
                        </div>
                        <div className="pt-4">
                          <div className="w-32 h-1 bg-destructive mx-auto rounded-full"></div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center text-muted-foreground">
                        No matches available at the moment.
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <div>
                <Card className="game-card">
                  <CardHeader className="vct-card-header">
                    <CardTitle className="vct-card-title text-center">Quick Leaderboard</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {leaderboard.slice(0, 5).map((entry) => (
                        <div key={entry.id} className="flex items-center justify-between p-3 bg-secondary rounded-lg">
                          <div className="flex items-center space-x-3">
                            <Badge variant="secondary" className="w-8 h-8 p-0 flex items-center justify-center">
                              {entry.rank === 1 ? "👑" : entry.rank}
                            </Badge>
                            <span className="font-medium">{entry.name}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm bg-muted px-2 py-1 rounded">
                              {entry.wins}W
                            </span>
                            <Badge 
                              variant={entry.is_alive ? "default" : "destructive"}
                              className="text-xs"
                            >
                              {entry.is_alive ? "ALIVE" : "DEAD"}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="leaderboard" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">🏆 Global Leaderboard</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {leaderboard.map((entry) => (
                    <div key={entry.id} className="flex items-center justify-between p-4 bg-secondary rounded-lg">
                      <div className="flex items-center space-x-4">
                        <Badge variant="secondary" className="w-10 h-10 p-0 flex items-center justify-center text-lg">
                          {entry.rank === 1 ? "👑" : entry.rank === 2 ? "🥈" : entry.rank === 3 ? "🥉" : entry.rank}
                        </Badge>
                        <div>
                          <div className="font-semibold">{entry.name}</div>
                          {!entry.is_alive && entry.eliminated_at && (
                            <div className="text-sm text-muted-foreground">Eliminated at {entry.eliminated_at}</div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Badge variant="outline" className="px-3 py-1">
                          {entry.wins} WINS
                        </Badge>
                        <Badge 
                          variant={entry.is_alive ? "default" : "destructive"}
                        >
                          {entry.is_alive ? "ALIVE" : "DEAD"}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="stats" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">📊 My Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                {userStats ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-secondary rounded-lg">
                      <div className="text-3xl font-bold text-primary">{userStats.totalPicks}</div>
                      <div className="text-sm text-muted-foreground">Total Picks</div>
                    </div>
                    <div className="text-center p-4 bg-secondary rounded-lg">
                      <div className="text-3xl font-bold text-primary">{userStats.wins}</div>
                      <div className="text-sm text-muted-foreground">Wins</div>
                    </div>
                    <div className="text-center p-4 bg-secondary rounded-lg">
                      <div className="text-3xl font-bold text-primary">{userStats.losses}</div>
                      <div className="text-sm text-muted-foreground">Losses</div>
                    </div>
                    <div className="text-center p-4 bg-secondary rounded-lg">
                      <div className="text-3xl font-bold text-primary">{userStats.pending}</div>
                      <div className="text-sm text-muted-foreground">Pending</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground">No statistics available.</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="schedule" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">🗓️ Match Schedule</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {["Lower Decider", "Upper Final", "Grand Final", "Championship"].map((stage, index) => (
                    <div key={stage} className="p-4 bg-secondary rounded-lg">
                      <h3 className="font-semibold mb-3">{stage}</h3>
                      <div className="space-y-3">
                        {[1, 2].map((match) => (
                          <div key={match} className="flex items-center justify-between p-3 bg-background rounded">
                            <div className="flex items-center space-x-4">
                              <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center text-sm">
                                {match}
                              </div>
                              <div className="flex items-center space-x-3">
                                <span className="font-medium">Team A</span>
                                <span className="text-muted-foreground">vs</span>
                                <span className="font-medium">Team B</span>
                              </div>
                            </div>
                            <div className="text-sm text-muted-foreground">
                              Jan {20 + index}, 2024
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
