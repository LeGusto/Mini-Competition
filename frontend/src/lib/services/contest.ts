import { authService } from './auth';

// For browser access, always use localhost since the browser runs outside Docker
const API_BASE = 'http://localhost:5000';

interface ContestTeam {
  id: number;
  team_name: string;
  leader_id: number;
  leader_username: string;
  member_count: number;
  created_at: string;
}

interface TeamMember {
  id: number;
  username: string;
  role: string;
  joined_at: string;
}

class ContestService {
  // Get all teams for a contest
  async getContestTeams(contestId: string): Promise<ContestTeam[]> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/teams`
      );

      if (response.ok) {
        const data = await response.json();
        return data.teams || [];
      } else {
        throw new Error('Failed to load teams');
      }
    } catch (error) {
      console.error('Error loading contest teams:', error);
      throw error;
    }
  }

  // Create a new team for a contest
  async createContestTeam(contestId: string, teamName: string): Promise<number> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/teams`,
        {
          method: 'POST',
          body: JSON.stringify({ team_name: teamName })
        }
      );

      if (response.ok) {
        const data = await response.json();
        return data.team_id;
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to create team');
      }
    } catch (error) {
      console.error('Error creating contest team:', error);
      throw error;
    }
  }

  // Join an existing team
  async joinContestTeam(contestId: string, teamId: string): Promise<void> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/teams/${teamId}/join`,
        {
          method: 'POST'
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to join team');
      }
    } catch (error) {
      console.error('Error joining contest team:', error);
      throw error;
    }
  }

  // Leave current team
  async leaveContestTeam(contestId: string): Promise<void> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/teams/leave`,
        {
          method: 'POST'
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to leave team');
      }
    } catch (error) {
      console.error('Error leaving contest team:', error);
      throw error;
    }
  }

  // Get user's current team for a contest
  async getUserContestTeam(contestId: string): Promise<ContestTeam | null> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/my-team`
      );

      if (response.ok) {
        const data = await response.json();
        return data.team;
      } else {
        return null;
      }
    } catch (error) {
      console.error('Error getting user contest team:', error);
      return null;
    }
  }

  // Get team members
  async getContestTeamMembers(contestId: string, teamId: string): Promise<TeamMember[]> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/teams/${teamId}/members`
      );

      if (response.ok) {
        const data = await response.json();
        return data.members || [];
      } else {
        throw new Error('Failed to load team members');
      }
    } catch (error) {
      console.error('Error loading contest team members:', error);
      throw error;
    }
  }
}

export const contestService = new ContestService();
