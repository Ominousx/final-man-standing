"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface User {
  email: string;
  name: string;
}

interface Match {
  id: string;
  teamA: string;
  teamB: string;
  startTime: string;
  stage: string;
  status: "upcoming" | "live" | "completed";
  winner?: string;
}

interface LeaderboardEntry {
  rank: number;
  user: string;
  wins: number;
  status: "alive" | "eliminated";
  eliminatedAt?: string;
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [email, setEmail] = useState("");
  const [currentMatch, setCurrentMatch] = useState<Match | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>("");

  // Mock data for demonstration
  useEffect(() => {
    // Simulate loading data
    setCurrentMatch({
      id: "UF-1-A",
      teamA: "Sentinels",
      teamB: "G2",
      startTime: "2024-01-20T15:00:00Z",
      stage: "Lower Decider",
      status: "upcoming"
    });

    setLeaderboard([
      { rank: 1, user: "jhasushant1999", wins: 3, status: "alive" },
      { rank: 2, user: "kunalsoni96", wins: 2, status: "alive" },
      { rank: 3, user: "gamer123", wins: 1, status: "eliminated", eliminatedAt: "Stage 2" },
    ]);
  }, []);

  const handleLogin = () => {
    if (email && email.includes('@')) {
      setUser({ email, name: email.split('@')[0] });
      setIsAuthenticated(true);
    }
  };

  const handlePick = () => {
    if (selectedTeam && currentMatch) {
      // Handle pick submission
      console.log(`Picked ${selectedTeam} for match ${currentMatch.id}`);
    }
  };

  const formatTime = (timeString: string) => {
    const date = new Date(timeString);
    return date.toLocaleString();
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-primary">VCT SURVIVOR</CardTitle>
            <CardDescription>Official Tournament Prediction Platform</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Button onClick={handleLogin} className="w-full">
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
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg">V</span>
            </div>
            <h1 className="text-2xl font-bold">VCT SURVIVOR</h1>
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

      <div className="container mx-auto px-4 py-8">
        <Tabs defaultValue="home" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="home">Home</TabsTrigger>
            <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
            <TabsTrigger value="stats">My Stats</TabsTrigger>
            <TabsTrigger value="schedule">Schedule</TabsTrigger>
          </TabsList>

          <TabsContent value="home" className="space-y-6">
            {/* Status Badge */}
            <div className="text-center">
              <Badge variant="secondary" className="text-lg px-6 py-2">
                ALIVE
              </Badge>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Current Match */}
              <div className="lg:col-span-2">
                <Card className="game-card">
                  <CardHeader>
                    <CardTitle className="text-center text-xl">Current Match Assignment</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {currentMatch && (
                      <>
                        <div className="text-center text-sm text-muted-foreground">
                          Match ID: {currentMatch.id}
                        </div>
                        
                        <div className="flex items-center justify-center space-x-8">
                          <div className="text-center">
                            <div className="team-logo bg-secondary flex items-center justify-center mb-2">
                              <span className="text-2xl">?</span>
                            </div>
                            <div className="font-semibold">{currentMatch.teamA}</div>
                          </div>
                          
                          <div className="vs-separator">VS</div>
                          
                          <div className="text-center">
                            <div className="team-logo bg-secondary flex items-center justify-center mb-2">
                              <span className="text-2xl">?</span>
                            </div>
                            <div className="font-semibold">{currentMatch.teamB}</div>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-center">
                          <div>
                            <div className="text-sm text-muted-foreground">Starts in</div>
                            <div className="font-semibold">1d 17h 9m</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">Locks</div>
                            <div className="font-semibold">5m before</div>
                          </div>
                        </div>

                        <div className="space-y-3">
                          <Select value={selectedTeam} onValueChange={setSelectedTeam}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select winner" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value={currentMatch.teamA}>{currentMatch.teamA}</SelectItem>
                              <SelectItem value={currentMatch.teamB}>{currentMatch.teamB}</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button onClick={handlePick} className="w-full" disabled={!selectedTeam}>
                            Lock Pick ✅
                          </Button>
                        </div>
                      </>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Quick Leaderboard */}
              <div>
                <Card className="game-card">
                  <CardHeader>
                    <CardTitle className="text-center text-xl">Quick Leaderboard</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {leaderboard.slice(0, 5).map((entry) => (
                        <div key={entry.rank} className="flex items-center justify-between p-3 bg-secondary rounded-lg">
                          <div className="flex items-center space-x-3">
                            <Badge variant="secondary" className="w-8 h-8 p-0 flex items-center justify-center">
                              {entry.rank === 1 ? "👑" : entry.rank}
                            </Badge>
                            <span className="font-medium">{entry.user}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm bg-muted px-2 py-1 rounded">
                              {entry.wins}W
                            </span>
                            <Badge 
                              variant={entry.status === "alive" ? "default" : "destructive"}
                              className="text-xs"
                            >
                              {entry.status === "alive" ? "ALIVE" : "DEAD"}
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
                    <div key={entry.rank} className="flex items-center justify-between p-4 bg-secondary rounded-lg">
                      <div className="flex items-center space-x-4">
                        <Badge variant="secondary" className="w-10 h-10 p-0 flex items-center justify-center text-lg">
                          {entry.rank === 1 ? "👑" : entry.rank === 2 ? "🥈" : entry.rank === 3 ? "🥉" : entry.rank}
                        </Badge>
                        <div>
                          <div className="font-semibold">{entry.user}</div>
                          {entry.status === "eliminated" && entry.eliminatedAt && (
                            <div className="text-sm text-muted-foreground">Eliminated at {entry.eliminatedAt}</div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Badge variant="outline" className="px-3 py-1">
                          {entry.wins} WINS
                        </Badge>
                        <Badge 
                          variant={entry.status === "alive" ? "default" : "destructive"}
                        >
                          {entry.status === "alive" ? "ALIVE" : "DEAD"}
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
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-secondary rounded-lg">
                    <div className="text-3xl font-bold text-primary">3</div>
                    <div className="text-sm text-muted-foreground">Total Picks</div>
                  </div>
                  <div className="text-center p-4 bg-secondary rounded-lg">
                    <div className="text-3xl font-bold text-primary">2</div>
                    <div className="text-sm text-muted-foreground">Wins</div>
                  </div>
                  <div className="text-center p-4 bg-secondary rounded-lg">
                    <div className="text-3xl font-bold text-primary">1</div>
                    <div className="text-sm text-muted-foreground">Losses</div>
                  </div>
                  <div className="text-center p-4 bg-secondary rounded-lg">
                    <div className="text-3xl font-bold text-primary">0</div>
                    <div className="text-sm text-muted-foreground">Pending</div>
                  </div>
                </div>
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
                  {[1, 2, 3].map((stage) => (
                    <div key={stage} className="p-4 bg-secondary rounded-lg">
                      <h3 className="font-semibold mb-3">Stage {stage}</h3>
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
                              Jan {20 + stage}, 2024
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
