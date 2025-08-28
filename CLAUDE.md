# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a **VCT (Valorant Champions Tour) Survivor** game - a tournament prediction platform where players are randomly assigned to matches and must predict winners to survive elimination.

The repository contains two Next.js applications:

### Root Level (`/`)
- **Framework**: Next.js 15.2.4 with React 18 and TypeScript
- **Main App**: Simple landing page/basic version
- **Scripts**: 
  - `npm run dev` - Development server
  - `npm run build` - Production build
  - `npm run export` - Static export
  - `npm run start` - Production server
  - `npm run lint` - ESLint

### Main Application (`/vct-survivor-web/`)
- **Framework**: Next.js 15.5.2 with React 19 and TypeScript
- **Styling**: Tailwind CSS 4 with custom gaming theme
- **UI Components**: Shadcn/UI with Radix UI primitives
- **Scripts**:
  - `npm run dev` - Development server with Turbopack
  - `npm run build` - Production build with Turbopack
  - `npm run start` - Production server
  - `npm run lint` - ESLint

## Architecture

### Data Management (`src/lib/data.ts`)
- **Local Storage Based**: All data persists in browser localStorage
- **Core Entities**: Users, Matches, UserPicks
- **Key Functions**:
  - `getUser(email)` - Get/create user
  - `assignMatchToUser(userId)` - Random match assignment
  - `submitPick(userId, matchId, selectedTeam)` - Lock predictions
  - `completeMatch(matchId, winner)` - Process results and eliminate users
  - `getLeaderboard()` - Ranked user list

### Game Logic
- **Final Man Standing**: One wrong pick eliminates player
- **Random Assignment**: Each user gets assigned to random matches
- **Progressive Elimination**: Winners advance, losers are eliminated
- **Persistent State**: Picks are locked and cannot be changed

### UI Components
- **Layout**: Single-page app with tabbed interface (Home, Leaderboard, Stats, Schedule)  
- **Authentication**: Email-based user creation/login
- **State Management**: React hooks with localStorage persistence
- **Responsive**: Mobile-first design with dark gaming theme

## Development Commands

```bash
# Work in main application directory
cd vct-survivor-web

# Start development server
npm run dev

# Build for production  
npm run build

# Run linting
npm run lint
```

## Key Configuration Files

- **Root**: `package.json`, `next.config.ts`, `vercel.json`
- **Main App**: `vct-survivor-web/package.json`, `vct-survivor-web/next.config.ts`
- **Tailwind**: Configured in main app with custom gaming theme
- **TypeScript**: `vct-survivor-web/tsconfig.json`

## Data Schema

Users have wins/losses/rank, matches have teams/stage/status, picks link users to match selections with correctness tracking.

## Deployment

Uses Vercel with GitHub Pages deployment scripts (`deploy-gh-pages.sh`, `deploy.sh`).