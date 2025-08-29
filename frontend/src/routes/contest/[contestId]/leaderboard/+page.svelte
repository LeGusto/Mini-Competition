<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { authService } from '$lib/services/auth';

  let contestId = $page.params.contestId;
  let leaderboardData: any = null;
  let userSubmissions: any[] = [];
  let loading = true;
  let error = '';
  let refreshInterval: any = null;

  onMount(async () => {
    await loadLeaderboard();
    await loadUserSubmissions();
    
    // Auto-refresh every 30 seconds for live updates
    refreshInterval = setInterval(async () => {
      await loadLeaderboard();
    }, 30000);
  });

  // Cleanup function for the interval
  onMount(() => {
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  });

  async function loadLeaderboard() {
    try {
      const response = await authService.authenticatedRequest(
        `http://localhost:5000/contest/${contestId}/leaderboard`
      );
      
      if (response.ok) {
        leaderboardData = await response.json();
      } else {
        error = 'Failed to load leaderboard';
      }
    } catch (err) {
      error = 'Failed to load leaderboard';
      console.error('Error loading leaderboard:', err);
    } finally {
      loading = false;
    }
  }

  async function loadUserSubmissions() {
    try {
      const response = await authService.authenticatedRequest(
        `http://localhost:5000/contest/${contestId}/submissions`
      );
      
      if (response.ok) {
        userSubmissions = await response.json();
      }
    } catch (err) {
      console.error('Error loading user submissions:', err);
    }
  }

  function formatDateTime(timeData: any) {
    if (!timeData) return 'N/A';
    
    if (typeof timeData === 'object' && timeData.formatted) {
      return `${timeData.formatted} ${timeData.timezone}`;
    }
    
    const date = new Date(timeData);
    return date.toLocaleString();
  }

  function getContestStatus() {
    if (!leaderboardData?.contest) return 'unknown';
    
    const now = new Date();
    const start = new Date(leaderboardData.contest.start_time.utc_iso || leaderboardData.contest.start_time);
    const end = new Date(leaderboardData.contest.end_time.utc_iso || leaderboardData.contest.end_time);

    if (now < start) return 'upcoming';
    if (now > end) return 'ended';
    return 'active';
  }

  function getStatusClass(status: string) {
    switch (status) {
      case 'upcoming': return 'status-upcoming';
      case 'active': return 'status-active';
      case 'ended': return 'status-ended';
      default: return '';
    }
  }

  function getStatusText(status: string) {
    switch (status) {
      case 'upcoming': return 'Upcoming';
      case 'active': return 'Active';
      case 'ended': return 'Ended';
      default: return 'Unknown';
    }
  }

  function formatPenalty(penaltyMinutes: number) {
    if (penaltyMinutes === 0) return '0m';
    return `${penaltyMinutes}m`;
  }

  function getRankClass(rank: number) {
    if (rank === 1) return 'rank-gold';
    if (rank === 2) return 'rank-silver';
    if (rank === 3) return 'rank-bronze';
    return '';
  }
</script>

<div class="leaderboard-container">
  {#if loading}
    <div class="loading">Loading leaderboard...</div>
  {:else if error}
    <div class="error-message">{error}</div>
  {:else if leaderboardData}
    <div class="contest-header">
      <h1>{leaderboardData.contest.name} - Leaderboard</h1>
      <div class="contest-info">
        <div class="contest-status">
          <span class="status-badge {getStatusClass(getContestStatus())}">
            {getStatusText(getContestStatus())}
          </span>
        </div>
        <div class="contest-times">
          <div>Start: {formatDateTime(leaderboardData.contest.start_time)}</div>
          <div>End: {formatDateTime(leaderboardData.contest.end_time)}</div>
        </div>
        <div class="contest-problems">
          {leaderboardData.contest.problems ? leaderboardData.contest.problems.length : 0} problems
        </div>
      </div>
    </div>

    <div class="leaderboard-content">
      <div class="leaderboard-table">
        <h2>Rankings</h2>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>User</th>
              <th>Solved</th>
              <th>Score</th>
              <th>Penalty</th>
              <th>First Solve</th>
            </tr>
          </thead>
          <tbody>
            {#each leaderboardData.leaderboard as entry}
              <tr class="{getRankClass(entry.rank)}">
                <td class="rank">{entry.rank}</td>
                <td class="username">{entry.username}</td>
                <td class="solved">{entry.problems_solved}</td>
                <td class="score">{entry.total_score}</td>
                <td class="penalty">{formatPenalty(entry.total_penalty)}</td>
                <td class="first-solve">
                  {entry.first_solve_time ? formatDateTime(entry.first_solve_time) : 'N/A'}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <div class="user-submissions">
        <h2>Your Submissions</h2>
        {#if userSubmissions.length === 0}
          <p class="no-submissions">No submissions yet for this contest.</p>
        {:else}
          <div class="submissions-list">
            {#each userSubmissions as submission}
              <div class="submission-item {submission.is_accepted ? 'accepted' : 'rejected'}">
                <div class="submission-header">
                  <span class="problem-id">Problem {submission.problem_id}</span>
                  <span class="submission-status">
                    {submission.is_accepted ? '✅ Accepted' : '❌ Rejected'}
                  </span>
                  <span class="submission-time">
                    {formatDateTime(submission.submission_time)}
                  </span>
                </div>
                <div class="submission-details">
                  <span class="language">{submission.language}</span>
                  {#if submission.score > 0}
                    <span class="score">Score: {submission.score}</span>
                  {/if}
                  {#if submission.penalty_time > 0}
                    <span class="penalty">Penalty: {formatPenalty(submission.penalty_time)}</span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <div class="refresh-info">
      <small>Leaderboard auto-refreshes every 30 seconds</small>
      <button class="btn btn-secondary" on:click={loadLeaderboard}>Refresh Now</button>
    </div>
  {/if}
</div>

<style>
  .leaderboard-container {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1rem;
  }

  .contest-header {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 2rem;
    margin-bottom: 2rem;
  }

  h1 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 1rem 0;
    font-size: 2rem;
    font-weight: 500;
  }

  .contest-info {
    display: grid;
    grid-template-columns: auto auto auto;
    gap: 2rem;
    align-items: center;
  }

  .contest-status {
    text-align: center;
  }

  .contest-times {
    font-family: 'Courier New', monospace;
    color: #cccccc;
  }

  .contest-times div {
    margin-bottom: 0.5rem;
  }

  .contest-problems {
    text-align: center;
    font-family: 'Courier New', monospace;
    color: #aaa;
    font-size: 1.1rem;
  }

  .status-badge {
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .status-upcoming {
    background: #666;
    color: #f5f5f5;
  }

  .status-active {
    background: #777;
    color: #f5f5f5;
  }

  .status-ended {
    background: #555;
    color: #f5f5f5;
  }

  .leaderboard-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 2rem;
    margin-bottom: 2rem;
  }

  .leaderboard-table, .user-submissions {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 1.5rem;
  }

  h2 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 1rem 0;
    font-size: 1.5rem;
    font-weight: 500;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Courier New', monospace;
  }

  th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #555;
  }

  th {
    background: #4a4a4a;
    color: #f5f5f5;
    font-weight: 600;
  }

  td {
    color: #cccccc;
  }

  .rank-gold {
    background: linear-gradient(135deg, #ffd700, #ffed4e);
    color: #000;
  }

  .rank-silver {
    background: linear-gradient(135deg, #c0c0c0, #e5e5e5);
    color: #000;
  }

  .rank-bronze {
    background: linear-gradient(135deg, #cd7f32, #daa520);
    color: #000;
  }

  .rank {
    font-weight: 600;
    text-align: center;
  }

  .username {
    font-weight: 600;
    color: #f5f5f5;
  }

  .solved, .score {
    text-align: center;
    font-weight: 600;
  }

  .penalty {
    text-align: center;
    color: #ff6b6b;
  }

  .first-solve {
    font-size: 0.9rem;
    color: #888;
  }

  .submissions-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .submission-item {
    background: #4a4a4a;
    border: 1px solid #666;
    border-radius: 4px;
    padding: 1rem;
  }

  .submission-item.accepted {
    border-left: 4px solid #4caf50;
  }

  .submission-item.rejected {
    border-left: 4px solid #f44336;
  }

  .submission-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .problem-id {
    font-weight: 600;
    color: #f5f5f5;
  }

  .submission-status {
    font-weight: 600;
  }

  .submission-status:global(.accepted) {
    color: #4caf50;
  }

  .submission-status:global(.rejected) {
    color: #ff6b6b;
  }

  .submission-time {
    font-size: 0.9rem;
    color: #aaa;
  }

  .submission-details {
    display: flex;
    gap: 1rem;
    font-size: 0.9rem;
    color: #cccccc;
  }

  .language {
    color: #f5f5f5;
  }

  .score {
    color: #4caf50;
  }

  .penalty {
    color: #ff6b6b;
  }

  .no-submissions {
    text-align: center;
    color: #aaa;
    font-style: italic;
    padding: 2rem;
  }

  .refresh-info {
    text-align: center;
    padding: 1rem;
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .refresh-info small {
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-secondary {
    background: #666;
    color: #f5f5f5;
  }

  .btn-secondary:hover {
    background: #777;
  }

  .loading {
    text-align: center;
    padding: 3rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
    font-size: 1.2rem;
  }

  .error-message {
    background: #4a4a4a;
    color: #ff6b6b;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    font-family: 'Courier New', monospace;
    border: 1px solid #666;
  }

  @media (max-width: 768px) {
    .leaderboard-content {
      grid-template-columns: 1fr;
    }

    .contest-info {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .submission-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .refresh-info {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>
