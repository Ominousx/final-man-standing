"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/contexts/AuthContext";

interface Match {
  stage_id: string;
  stage_name: string;
  match_id: string;
  team_a: string;
  team_b: string;
  match_time_iso: string;
  winner_team: string;
}

interface Pick {
  user: string;
  userEmail: string;
  stage_id: string;
  match_id: string;
  pick_team: string;
  pick_time_iso: string;
}

interface Assignment {
  user: string;
  stage_id: string;
  match_id: string;
  assigned_time_iso: string;
}

// Team logo mapping
const teamLogos: { [key: string]: string } = {
  "Sentinels": "/logos/Sentinels.png",
  "G2": "/logos/G2.png",
  "BBL": "/logos/BBL.png",
  "Team Liquid": "/logos/Team Liquid.png",
  "NRG": "/logos/NRG.png",
  "Cloud9": "/logos/Cloud9.png",
  "TALON": "/logos/TALON.png",
  "RRQ": "/logos/RRQ.png",
  "Paper Rex": "/logos/Paper Rex.png",
  "GiantX": "/logos/GiantX.png",
  "NAVI": "/logos/NAVI.png"
};

export default function Home() {
  const { user, logout, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [matches, setMatches] = useState<Match[]>([]);
  const [picks, setPicks] = useState<Pick[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [userPick, setUserPick] = useState<string>("");
  const [pickSubmitted, setPickSubmitted] = useState(false);
  const [currentRandomMatch, setCurrentRandomMatch] = useState<Match | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    // Simulate loading data - in real app, this would be API calls
    const loadData = async () => {
      try {
        // For demo purposes, using the CSV data structure
        const mockMatches: Match[] = [
          {
            stage_id: "1",
            stage_name: "Upper Finals",
            match_id: "UF-1-A",
            team_a: "Sentinels",
            team_b: "G2",
            match_time_iso: "2025-08-29T00:00:00Z",
            winner_team: ""
          },
          {
            stage_id: "1",
            stage_name: "Upper Finals",
            match_id: "UF-1-E",
            team_a: "BBL",
            team_b: "Team Liquid",
            match_time_iso: "2025-08-29T18:00:00Z",
            winner_team: ""
          },
          {
            stage_id: "1",
            stage_name: "Lower Decider",
            match_id: "LD-1-A",
            team_a: "NRG",
            team_b: "Cloud9",
            match_time_iso: "2025-08-30T03:00:00Z",
            winner_team: ""
          },
          {
            stage_id: "1",
            stage_name: "Lower Finals",
            match_id: "LF-1-P",
            team_a: "TALON",
            team_b: "RRQ",
            match_time_iso: "2025-08-30T12:00:00Z",
            winner_team: ""
          },
          {
            stage_id: "1",
            stage_name: "Grand Final",
            match_id: "GF-P",
            team_a: "Paper Rex",
            team_b: "TBD",
            match_time_iso: "2025-08-31T15:00:00Z",
            winner_team: ""
          }
        ];

        const mockPicks: Pick[] = [
          { user: "jhasushant1999", userEmail: "jhasushant1999@example.com", stage_id: "1", match_id: "UF-1-A", pick_team: "G2", pick_time_iso: "2025-08-26T10:00:04.385594+00:00" },
          { user: "jhasushat1999", userEmail: "jhasushat1999@example.com", stage_id: "1", match_id: "UF-1-E", pick_team: "Team Liquid", pick_time_iso: "2025-08-26T09:56:19.651438+00:00" },
          { user: "kunalsoni96", userEmail: "kunalsoni96@example.com", stage_id: "1", match_id: "UF-1-E", pick_team: "BBL", pick_time_iso: "2025-08-26T10:00:25.217574+00:00" },
          { user: "anshul6762", userEmail: "anshul6762@example.com", stage_id: "1", match_id: "UF-1-E", pick_team: "BBL", pick_time_iso: "2025-08-26T10:00:49.548245+00:00" }
        ];

        const mockAssignments: Assignment[] = [
          { user: "jhasushant1999", stage_id: "1", match_id: "UF-1-A", assigned_time_iso: "2025-08-26T09:49:51.814558+00:00" },
          { user: "jhasushat1999", stage_id: "1", match_id: "UF-1-E", assigned_time_iso: "2025-08-26T09:53:44.361263+00:00" },
          { user: "kunalsoni96", stage_id: "1", match_id: "UF-1-E", assigned_time_iso: "2025-08-26T10:00:21.351930+00:00" },
          { user: "anshul6762", stage_id: "1", match_id: "UF-1-E", assigned_time_iso: "2025-08-26T10:00:44.384328+00:00" }
        ];

        setMatches(mockMatches);
        setPicks(mockPicks);
        setAssignments(mockAssignments);
      } catch (error) {
        console.error("Error loading data:", error);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      loadData();
    }
  }, [user]);

  // Generate random match when user logs in or when requested

  // Load user's existing picks from localStorage
  useEffect(() => {
    if (user) {
      const storedPicks = localStorage.getItem(`userPicks_${user.email}`);
      if (storedPicks) {
        try {
          const parsedPicks = JSON.parse(storedPicks);
          setPicks(prev => [...prev, ...parsedPicks]);
        } catch (error) {
          console.error("Error parsing stored picks:", error);
        }
      }
    }
  }, [user]);

  // Generate random match when user first loads or when requested
  useEffect(() => {
    if (user && matches.length > 0 && !currentRandomMatch) {
      // Logic for generating random match would go here
      const randomMatch = matches[Math.floor(Math.random() * matches.length)];
      setCurrentRandomMatch(randomMatch);
    }
  }, [user, matches, currentRandomMatch]);

  const handlePickSubmission = (pickedTeam: string) => {
    if (!user || !currentRandomMatch) return;

    const newPick: Pick = {
      user: user.name || "Unknown User",
      userEmail: user.email,
      stage_id: currentRandomMatch.stage_id,
      match_id: currentRandomMatch.match_id,
      pick_team: pickedTeam,
      pick_time_iso: new Date().toISOString()
    };

    // Add to local state
    setPicks(prev => [...prev, newPick]);
    
    // Store in localStorage
    const storedPicks = localStorage.getItem(`userPicks_${user.email}`) || "[]";
    const parsedPicks = JSON.parse(storedPicks);
    parsedPicks.push(newPick);
    localStorage.setItem(`userPicks_${user.email}`, JSON.stringify(parsedPicks));

    setUserPick(pickedTeam);
    setPickSubmitted(true);
  };

  const handleNewRandomMatch = () => {
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getMatchStatus = (match: Match) => {
    if (match.winner_team) return "Completed";
    const matchTime = new Date(match.match_time_iso);
    const now = new Date();
    if (matchTime < now) return "Live";
    return "Upcoming";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Completed": return "bg-green-600";
      case "Live": return "bg-red-600";
      case "Upcoming": return "bg-blue-600";
      default: return "bg-gray-600";
    }
  };

  const getTeamLogo = (teamName: string) => {
    return teamLogos[teamName] || null;
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-2xl font-bold text-white">Loading...</div>
      </div>
    );
  }

  // Don't render main content if not authenticated
  if (!user) {
    return null;
  }

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <div className="space-y-6">
            {/* Random Match Picker */}
            <Card className="bg-black border border-gray-800 shadow-2xl">
              <CardHeader className="border-b border-gray-800">
                <CardTitle className="text-xl text-white">🎯 Your Random Match</CardTitle>
                <p className="text-gray-400">Pick the winner for this randomly selected match!</p>
              </CardHeader>
              <CardContent className="p-6">
                {currentRandomMatch ? (
                  <div className="space-y-6">
                    {/* Match Info */}
                    <div className="text-center">
                      <Badge className={`${getStatusColor(getMatchStatus(currentRandomMatch))} text-white border-0 mb-4`}>
                        {getMatchStatus(currentRandomMatch)}
                      </Badge>
                      <h3 className="text-lg font-semibold text-white mb-2">
                        {currentRandomMatch.stage_name} - {currentRandomMatch.match_id}
                      </h3>
                      <p className="text-gray-400 mb-4">
                        {formatDate(currentRandomMatch.match_time_iso)}
                      </p>
                    </div>

                    {/* Teams */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {/* Team A */}
                      <div className="text-center">
                        <div className="flex flex-col items-center space-y-3">
                          {getTeamLogo(currentRandomMatch.team_a) ? (
                            <div className="w-20 h-20 relative">
                              <Image
                                src={getTeamLogo(currentRandomMatch.team_a)!}
                                alt={`${currentRandomMatch.team_a} logo`}
                                fill
                                className="object-contain"
                              />
                            </div>
                          ) : (
                            <div className="w-20 h-20 bg-gray-900 rounded-xl flex items-center justify-center border border-gray-800">
                              <span className="text-2xl text-gray-400">?</span>
                            </div>
                          )}
                          <div className="text-2xl font-bold text-white">{currentRandomMatch.team_a}</div>
                          <div className="text-sm text-gray-400">Team A</div>
                        </div>
                      </div>
                      
                      {/* VS */}
                      <div className="flex items-center justify-center">
                        <div className="text-4xl font-bold text-gray-500">VS</div>
                      </div>
                      
                      {/* Team B */}
                      <div className="text-center">
                        <div className="flex flex-col items-center space-y-3">
                          {getTeamLogo(currentRandomMatch.team_b) ? (
                            <div className="w-20 h-20 relative">
                              <Image
                                src={getTeamLogo(currentRandomMatch.team_b)!}
                                alt={`${currentRandomMatch.team_b} logo`}
                                fill
                                className="object-contain"
                              />
                            </div>
                          ) : (
                            <div className="w-20 h-20 bg-gray-900 rounded-xl flex items-center justify-center border border-gray-800">
                              <span className="text-2xl text-gray-400">?</span>
                            </div>
                          )}
                          <div className="text-2xl font-bold text-white">{currentRandomMatch.team_b}</div>
                          <div className="text-sm text-gray-400">Team B</div>
                        </div>
                      </div>
                    </div>

                    {/* Pick Buttons */}
                    {!pickSubmitted ? (
                      <div className="flex justify-center space-x-4">
                        <Button
                          onClick={() => handlePickSubmission(currentRandomMatch.team_a)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl transition-all duration-300"
                        >
                          Pick {currentRandomMatch.team_a}
                        </Button>
                        <Button
                          onClick={() => handlePickSubmission(currentRandomMatch.team_b)}
                          className="bg-red-600 hover:bg-red-700 text-white px-8 py-3 rounded-xl transition-all duration-300"
                        >
                          Pick {currentRandomMatch.team_b}
                        </Button>
                      </div>
                    ) : (
                      <div className="text-center space-y-4">
                        <div className="text-green-400 text-lg font-semibold">
                          ✅ You picked: <span className="text-white">{userPick}</span>
                        </div>
                        <Button
                          onClick={handleNewRandomMatch}
                          className="bg-white text-black hover:bg-gray-200 px-6 py-2 rounded-xl transition-all duration-300"
                        >
                          Get Another Random Match
                        </Button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-400 text-lg">Loading random match...</div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* User's Pick History */}
            <Card className="bg-black border border-gray-800 shadow-2xl">
              <CardHeader className="border-b border-gray-800">
                <CardTitle className="text-xl text-white">📊 Your Pick History</CardTitle>
                <p className="text-gray-400">Track all your previous picks</p>
              </CardHeader>
              <CardContent className="p-6">
                {picks.filter(p => p.userEmail === user.email).length > 0 ? (
                  <div className="space-y-4">
                    {picks
                      .filter(p => p.userEmail === user.email)
                      .map((pick, index) => (
                        <div key={index} className="flex items-center justify-between p-4 bg-gray-900 rounded-xl border border-gray-800">
                          <div className="flex items-center space-x-4">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                              <span className="text-sm font-medium text-white">{index + 1}</span>
                            </div>
                            <div>
                              <div className="text-white font-medium">{pick.match_id}</div>
                              <div className="text-gray-400 text-sm">{formatDate(pick.pick_time_iso)}</div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {getTeamLogo(pick.pick_team) && (
                              <div className="w-6 h-6 relative">
                                <Image
                                  src={getTeamLogo(pick.pick_team)!}
                                  alt={`${pick.pick_team} logo`}
                                  fill
                                  className="object-contain"
                                />
                              </div>
                            )}
                            <Badge variant="secondary" className="bg-gray-800 text-white border border-gray-700">
                              {pick.pick_team}
                            </Badge>
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-400 text-lg">No picks yet. Make your first pick above!</div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        );

      case "matches":
        return (
          <div className="grid gap-6">
            {matches.map((match) => {
              const status = getMatchStatus(match);
              const userPicks = picks.filter(p => p.match_id === match.match_id);
              const userAssignments = assignments.filter(a => a.match_id === match.match_id);
              
              return (
                <Card key={match.match_id} className="bg-black border border-gray-800 shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-[1.02]">
                  <CardHeader className="border-b border-gray-800">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl text-white">
                        {match.stage_name} - {match.match_id}
                      </CardTitle>
                      <div className="flex items-center space-x-2">
                        <Badge className={`${getStatusColor(status)} text-white border-0`}>
                          {status}
                        </Badge>
                        <span className="text-sm text-gray-400">
                          {formatDate(match.match_time_iso)}
                        </span>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {/* Team A */}
                      <div className="text-center">
                        <div className="flex flex-col items-center space-y-3">
                          {getTeamLogo(match.team_a) ? (
                            <div className="w-20 h-20 relative">
                              <Image
                                src={getTeamLogo(match.team_a)!}
                                alt={`${match.team_a} logo`}
                                fill
                                className="object-contain"
                              />
                            </div>
                          ) : (
                            <div className="w-20 h-20 bg-gray-900 rounded-xl flex items-center justify-center border border-gray-800">
                              <span className="text-2xl text-gray-400">?</span>
                            </div>
                          )}
                          <div className="text-2xl font-bold text-white">{match.team_a}</div>
                          <div className="text-sm text-gray-400">Team A</div>
                        </div>
                      </div>
                      
                      {/* VS */}
                      <div className="flex items-center justify-center">
                        <div className="text-4xl font-bold text-gray-500">VS</div>
                      </div>
                      
                      {/* Team B */}
                      <div className="text-center">
                        <div className="flex flex-col items-center space-y-3">
                          {getTeamLogo(match.team_b) ? (
                            <div className="w-20 h-20 relative">
                              <Image
                                src={getTeamLogo(match.team_b)!}
                                alt={`${match.team_b} logo`}
                                fill
                                className="object-contain"
                              />
                            </div>
                          ) : (
                            <div className="w-20 h-20 bg-gray-900 rounded-xl flex items-center justify-center border border-gray-800">
                              <span className="text-2xl text-gray-400">?</span>
                            </div>
                          )}
                          <div className="text-2xl font-bold text-white">{match.team_b}</div>
                          <div className="text-sm text-gray-400">Team B</div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Match Info */}
                    <div className="mt-6 pt-6 border-t border-gray-800">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Users Assigned: </span>
                          <span className="text-white font-semibold">{userAssignments.length}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Picks Made: </span>
                          <span className="text-white font-semibold">{userPicks.length}</span>
                        </div>
                      </div>
                      
                      {userPicks.length > 0 && (
                        <div className="mt-4">
                          <span className="text-gray-400 text-sm">User Picks: </span>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {userPicks.map((pick, index) => (
                              <Badge key={index} variant="secondary" className="bg-gray-900 text-white border border-gray-800">
                                {pick.user}: {pick.pick_team}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        );

      case "picks":
        return (
          <Card className="bg-black border border-gray-800 shadow-2xl">
            <CardHeader className="border-b border-gray-800">
              <CardTitle className="text-xl text-white">User Picks</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-gray-900">
                    <TableHead className="text-gray-300 font-semibold">User</TableHead>
                    <TableHead className="text-gray-300 font-semibold">Email</TableHead>
                    <TableHead className="text-gray-300 font-semibold">Match</TableHead>
                    <TableHead className="text-gray-300 font-semibold">Pick</TableHead>
                    <TableHead className="text-gray-300 font-semibold">Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {picks.map((pick, index) => (
                    <TableRow key={index} className="border-gray-800 hover:bg-gray-900">
                      <TableCell className="text-white font-medium">{pick.user}</TableCell>
                      <TableCell className="text-gray-300">{pick.userEmail}</TableCell>
                      <TableCell className="text-gray-300">{pick.match_id}</TableCell>
                      <TableCell className="text-gray-300">
                        <div className="flex items-center space-x-2">
                          {getTeamLogo(pick.pick_team) && (
                            <div className="w-6 h-6 relative">
                              <Image
                                src={getTeamLogo(pick.pick_team)!}
                                alt={`${pick.pick_team} logo`}
                                fill
                                className="object-contain"
                              />
                            </div>
                          )}
                          <Badge variant="secondary" className="bg-gray-900 text-white border border-gray-800">
                            {pick.pick_team}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-gray-300">{formatDate(pick.pick_time_iso)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        );

      case "assignments":
        return (
          <Card className="bg-black border border-gray-800 shadow-2xl">
            <CardHeader className="border-b border-gray-800">
              <CardTitle className="text-xl text-white">Match Assignments</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-gray-900">
                    <TableHead className="text-gray-300 font-semibold">User</TableHead>
                    <TableHead className="text-gray-300 font-semibold">Match</TableHead>
                    <TableHead className="text-gray-300 font-semibold">Assigned Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {assignments.map((assignment, index) => (
                    <TableRow key={index} className="border-gray-800 hover:bg-gray-900">
                      <TableCell className="text-white font-medium">{assignment.user}</TableCell>
                      <TableCell className="text-gray-300">{assignment.match_id}</TableCell>
                      <TableCell className="text-gray-300">{formatDate(assignment.assigned_time_iso)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        );

      case "leaderboard":
        return (
          <Card className="bg-black border border-gray-800 shadow-2xl">
            <CardHeader className="border-b border-gray-800">
              <CardTitle className="text-xl text-white">Tournament Leaderboard</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="text-center py-8">
                <div className="text-gray-300 text-lg">Leaderboard coming soon...</div>
                <p className="text-gray-400 mt-2">Track user performance and rankings</p>
              </div>
            </CardContent>
          </Card>
        );

      case "settings":
        return (
          <Card className="bg-black border border-gray-800 shadow-2xl">
            <CardHeader className="border-b border-gray-800">
              <CardTitle className="text-xl text-white">Settings</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="text-center py-8">
                <div className="text-gray-300 text-lg">Settings panel coming soon...</div>
                <p className="text-gray-400 mt-2">Configure tournament preferences</p>
              </div>
            </CardContent>
          </Card>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-2xl font-bold text-white">Loading VCT Survivor...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex">
      {/* Sidebar */}
      <div className="w-64 bg-black border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 relative">
              <Image
                src="/icons/vct.png"
                alt="VCT Logo"
                fill
                className="object-contain"
              />
            </div>
            <div>
              <h1 className="text-lg font-bold text-yellow-400">VCT Survivor</h1>
              <p className="text-xs text-gray-400">Final Man Standing</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <div className="space-y-2">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 ${
                activeTab === "dashboard"
                  ? "bg-white text-black shadow-lg transform scale-105"
                  : "text-gray-300 hover:bg-gray-900 hover:text-white border border-transparent hover:border-gray-700"
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5">🎯</div>
                <span className="font-medium">Random Match Picker</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab("matches")}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 ${
                activeTab === "matches"
                  ? "bg-white text-black shadow-lg transform scale-105"
                  : "text-gray-300 hover:bg-gray-900 hover:text-white border border-transparent hover:border-gray-700"
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5">🏆</div>
                <span className="font-medium">All Matches</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab("picks")}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 ${
                activeTab === "picks"
                  ? "bg-white text-black shadow-lg transform scale-105"
                  : "text-gray-300 hover:bg-gray-900 hover:text-white border border-transparent hover:border-gray-700"
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5">📊</div>
                <span className="font-medium">All User Picks</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab("assignments")}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 ${
                activeTab === "assignments"
                  ? "bg-white text-black shadow-lg transform scale-105"
                  : "text-gray-300 hover:bg-gray-900 hover:text-white border border-transparent hover:border-gray-700"
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5">📋</div>
                <span className="font-medium">Match Assignments</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab("leaderboard")}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 ${
                activeTab === "leaderboard"
                  ? "bg-white text-black shadow-lg transform scale-105"
                  : "text-gray-300 hover:bg-gray-900 hover:text-white border border-transparent hover:border-gray-700"
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5">🏅</div>
                <span className="font-medium">Leaderboard</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab("settings")}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 ${
                activeTab === "settings"
                  ? "bg-white text-black shadow-lg transform scale-105"
                  : "text-gray-300 hover:bg-gray-900 hover:text-white border border-transparent hover:border-gray-700"
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5">⚙️</div>
                <span className="font-medium">Settings</span>
              </div>
            </button>
          </div>
        </nav>

        {/* User Info */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center space-x-3 p-3 rounded-xl bg-gray-900 border border-gray-800">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-white">{user.name ? user.name.charAt(0).toUpperCase() : 'U'}</span>
            </div>
            <div>
              <div className="text-sm font-medium text-white">{user.name || 'User'}</div>
              <div className="text-xs text-gray-300">{user.email}</div>
              <div className="text-xs text-gray-400">{user.role}</div>
            </div>
          </div>
          <Button
            onClick={handleLogout}
            variant="outline"
            className="w-full mt-3 border-gray-700 text-white hover:bg-gray-900 hover:border-gray-600 transition-all duration-300"
          >
            Logout
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-black">
        {/* Top Header */}
        <header className="bg-black border-b border-gray-800 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">
                {activeTab === "dashboard" && "Random Match Picker"}
                {activeTab === "matches" && "All Tournament Matches"}
                {activeTab === "picks" && "All User Picks"}
                {activeTab === "assignments" && "Match Assignments"}
                {activeTab === "leaderboard" && "Tournament Leaderboard"}
                {activeTab === "settings" && "Settings"}
              </h2>
              <p className="text-gray-400 text-lg">
                {activeTab === "dashboard" && "Pick winners for randomly selected matches"}
                {activeTab === "matches" && "View and manage all tournament matches"}
                {activeTab === "picks" && "Track all user picks and predictions"}
                {activeTab === "assignments" && "View match assignments and user allocations"}
                {activeTab === "leaderboard" && "Tournament standings and rankings"}
                {activeTab === "settings" && "Configure tournament preferences"}
              </p>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-8 overflow-auto bg-black">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}
