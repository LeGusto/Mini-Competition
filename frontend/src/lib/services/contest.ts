import { authService } from './auth';
import { API_BASE_URL } from '../config';

const API_BASE = API_BASE_URL;

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

  // Register for a contest
  async registerForContest(contestId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/register`,
        {
          method: 'POST'
        }
      );

      const data = await response.json();

      if (response.ok) {
        return { success: true, message: data.message };
      } else {
        return { success: false, message: data.message || 'Registration failed' };
      }
    } catch (error) {
      console.error('Error registering for contest:', error);
      return { success: false, message: 'Failed to register for contest' };
    }
  }

  // Check registration status for a contest
  async checkRegistrationStatus(contestId: string): Promise<{
    is_registered: boolean;
    registration_data?: any;
  }> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/registration-status`
      );

      if (response.ok) {
        const data = await response.json();
        return {
          is_registered: data.is_registered,
          registration_data: data.registration_data
        };
      } else {
        return { is_registered: false };
      }
    } catch (error) {
      console.error('Error checking registration status:', error);
      return { is_registered: false };
    }
  }

  // Get contest access status
  async getContestAccessStatus(contestId: string): Promise<{
    can_access: boolean;
    reason: string;
    can_register: boolean;
    contest_status: string;
    is_registered: boolean;
  }> {
    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE}/contest/${contestId}/access`
      );

      if (response.ok) {
        return await response.json();
      } else {
        throw new Error('Failed to get access status');
      }
    } catch (error) {
      console.error('Error getting contest access status:', error);
      throw error;
    }
  }
}

export const contestService = new ContestService();
