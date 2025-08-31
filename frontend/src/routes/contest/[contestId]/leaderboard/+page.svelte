<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { authService } from '$lib/services/auth';

  let contestId = $page.params.contestId;
  let leaderboardData: any = null;
  let loading = true;
  let error = '';
  let refreshInterval: any = null;

  onMount(async () => {
    await loadLeaderboard();
    
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



  function formatDateTime(timeData: any) {
    if (!timeData) return 'N/A';
    
    // Handle new timezone-aware format
    if (typeof timeData === 'object' && timeData.utc_iso) {
      // Convert UTC time to user's local timezone
      const date = new Date(timeData.utc_iso);
      return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      });
    }
    
    // Fallback for old format (simple ISO string)
    if (typeof timeData === 'string') {
      const date = new Date(timeData);
      return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      });
    }
    
    return 'Invalid date';
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
    if (penaltyMinutes === 0) return '';
    return `${penaltyMinutes}m`;
  }

  function getRankClass(rank: number) {
    if (rank === 1) return 'rank-gold';
    if (rank === 2) return 'rank-silver';
    if (rank === 3) return 'rank-bronze';
    return '';
  }

  function getProblemLabel(index: number) {
    return String.fromCharCode(65 + index); // A, B, C, D, etc.
  }

  function getProblemStatus(userId: number, problemId: string) {
    // Get status from leaderboard data
    const userEntry = leaderboardData?.leaderboard?.find((entry: any) => entry.user_id === userId);
    if (!userEntry || !userEntry.problem_statuses) return 'untried';
    
    const problemStatus = userEntry.problem_statuses[problemId];
    return problemStatus ? problemStatus.status : 'untried';
  }

  function getProblemAttempts(userId: number, problemId: string) {
    // Get attempts from leaderboard data
    const userEntry = leaderboardData?.leaderboard?.find((entry: any) => entry.user_id === userId);
    if (!userEntry || !userEntry.problem_statuses) return 0;
    
    const problemStatus = userEntry.problem_statuses[problemId];
    return problemStatus ? problemStatus.attempts : 0;
  }

  function getProblemPenaltyAttempts(userId: number, problemId: string) {
    // Get penalty attempts (wrong attempts before acceptance) from leaderboard data
    const userEntry = leaderboardData?.leaderboard?.find((entry: any) => entry.user_id === userId);
    if (!userEntry || !userEntry.problem_statuses) return 0;
    
    const problemStatus = userEntry.problem_statuses[problemId];
    return problemStatus ? (problemStatus.penalty_attempts || 0) : 0;
  }

  function getProblemTime(userId: number, problemId: string) {
    // Get solve time from leaderboard data
    const userEntry = leaderboardData?.leaderboard?.find((entry: any) => entry.user_id === userId);
    if (!userEntry || !userEntry.problem_statuses) return null;
    
    const problemStatus = userEntry.problem_statuses[problemId];
    return problemStatus ? problemStatus.solve_time : null;
  }

  function getGridColumns() {
    if (!leaderboardData?.contest?.problems) return '60px 200px 80px';
    const problemCount = leaderboardData.contest.problems.length;
    const problemColumns = Array(problemCount).fill('80px').join(' ');
    return `60px 200px 80px ${problemColumns}`;
  }

  function getGridColumnsTablet() {
    if (!leaderboardData?.contest?.problems) return '50px 150px 70px';
    const problemCount = leaderboardData.contest.problems.length;
    const problemColumns = Array(problemCount).fill('70px').join(' ');
    return `50px 150px 70px ${problemColumns}`;
  }

  function getGridColumnsMobile() {
    if (!leaderboardData?.contest?.problems) return '40px 120px 60px';
    const problemCount = leaderboardData.contest.problems.length;
    const problemColumns = Array(problemCount).fill('60px').join(' ');
    return `40px 120px 60px ${problemColumns}`;
  }

  function formatAttempts(count: number) {
    if (count === 1) return '1 try';
    return `${count} tries`;
  }

  function isFirstBlood(userId: number, problemId: string) {
    // Check if this user got first blood on this problem
    const userEntry = leaderboardData?.leaderboard?.find((entry: any) => entry.user_id === userId);
    if (!userEntry || !userEntry.problem_statuses) return false;
    
    const problemStatus = userEntry.problem_statuses[problemId];
    return problemStatus ? (problemStatus.is_first_blood || false) : false;
  }
</script>

<div class="leaderboard-container">
  {#if loading}
    <div class="loading">Loading leaderboard...</div>
  {:else if error}
    <div class="error-message">{error}</div>
  {:else if leaderboardData}
    <div class="contest-header">
      <h1>{leaderboardData.contest.name}</h1>
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
      </div>
    </div>

    <div class="leaderboard-wrapper">
      <div class="leaderboard-grid" style="grid-template-columns: {getGridColumns()}; --grid-columns-tablet: {getGridColumnsTablet()}; --grid-columns-mobile: {getGridColumnsMobile()}">
        <!-- Header Row -->
        <div class="grid-header">
          <div class="rank-header">RANK</div>
          <div class="team-header">TEAM</div>
          <div class="score-header">SCORE</div>
          {#each leaderboardData.contest.problems || [] as problemId, index}
            <div class="problem-header">
              {getProblemLabel(index)}
            </div>
          {/each}
        </div>

        <!-- Leaderboard Rows -->
        {#if leaderboardData.leaderboard && leaderboardData.leaderboard.length > 0}
          {#each leaderboardData.leaderboard as entry, rowIndex}
            <div class="grid-row">
              <div class="rank-cell {getRankClass(entry.rank)}">{entry.rank}</div>
              <div class="team-cell">
                <div class="team-name">{entry.username}</div>
                <div class="team-meta">
                  {entry.problems_solved} solved
                  {#if entry.total_penalty > 0}
                    · {formatPenalty(entry.total_penalty)} penalty
                  {/if}
                </div>
              </div>
              <div class="score-cell">
                <div class="score-main">{entry.total_score}</div>
              </div>
              {#each leaderboardData.contest.problems || [] as problemId, problemIndex}
                {@const status = getProblemStatus(entry.user_id, problemId)}
                {@const attempts = getProblemAttempts(entry.user_id, problemId)}
                {@const penaltyAttempts = getProblemPenaltyAttempts(entry.user_id, problemId)}
                {@const solveTime = getProblemTime(entry.user_id, problemId)}
                {@const firstBlood = isFirstBlood(entry.user_id, problemId)}
                <div class="problem-cell problem-{status} {firstBlood ? 'first-blood' : ''}">
                  {#if status === 'solved'}
                    <div class="solve-time">{solveTime}</div>
                    {#if penaltyAttempts > 0}
                      <div class="attempts">{formatAttempts(penaltyAttempts)}</div>
                    {/if}
                  {:else if status === 'attempted'}
                    <div class="attempts">{formatAttempts(attempts)}</div>
                  {:else if status === 'pending'}
                    <div class="attempts">Pending...</div>
                  {:else}
                    <!-- Empty for untried -->
                  {/if}
                </div>
              {/each}
            </div>
          {/each}
        {/if}
        
        <!-- Show empty message below the grid if no submissions -->
        {#if !leaderboardData.leaderboard || leaderboardData.leaderboard.length === 0}
          <div class="empty-leaderboard">
            <p>No submissions yet for this contest.</p>
            <p>The leaderboard will update as participants submit solutions.</p>
          </div>
        {/if}
      </div>
    </div>

    <div class="legend">
      <h3>Legend</h3>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-color problem-solved"></div>
          <span>Solved</span>
        </div>
        <div class="legend-item">
          <div class="legend-color problem-attempted"></div>
          <span>Attempted</span>
        </div>
        <div class="legend-item">
          <div class="legend-color problem-pending"></div>
          <span>Pending</span>
        </div>
        <div class="legend-item">
          <div class="legend-color problem-untried"></div>
          <span>Not attempted</span>
        </div>
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
    max-width: 1400px;
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
    text-align: center;
  }

  .contest-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 2rem;
  }

  .contest-status {
    text-align: center;
  }

  .contest-times {
    font-family: 'Courier New', monospace;
    color: #cccccc;
    text-align: center;
  }

  .contest-times div {
    margin-bottom: 0.5rem;
  }

  .status-badge {
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    font-family: 'Courier New', monospace;
  }

  .status-upcoming {
    background: #666;
    color: #f5f5f5;
  }

  .status-active {
    background: #4caf50;
    color: #f5f5f5;
  }

  .status-ended {
    background: #555;
    color: #f5f5f5;
  }

  .leaderboard-wrapper {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 2rem;
    overflow-x: auto;
  }

  .leaderboard-grid {
    display: grid;
    gap: 1px;
    min-width: 600px;
    font-family: 'Courier New', monospace;
  }

  .grid-header {
    display: contents;
  }

  .grid-header > div {
    background: #4a4a4a;
    color: #f5f5f5;
    font-weight: 600;
    padding: 0.75rem 0.5rem;
    text-align: center;
    font-size: 0.9rem;
    border: 1px solid #555;
  }

  .grid-row {
    display: contents;
  }

  .grid-row > div {
    background: #3a3a3a;
    border: 1px solid #555;
    padding: 0.75rem 0.5rem;
    color: #cccccc;
  }

  .rank-cell {
    text-align: center;
    font-weight: 600;
    font-size: 1.1rem;
  }

  .team-cell {
    padding: 0.5rem !important;
  }

  .team-name {
    font-weight: 600;
    color: #f5f5f5;
    margin-bottom: 0.25rem;
    font-size: 0.95rem;
  }

  .team-meta {
    font-size: 0.8rem;
    color: #aaa;
  }

  .score-cell {
    text-align: center;
    font-weight: 600;
    font-size: 1.1rem;
    color: #f5f5f5;
  }

  .problem-cell {
    text-align: center;
    font-size: 0.8rem;
    line-height: 1.2;
  }

  .problem-solved {
    background: #4caf50 !important;
    color: #fff !important;
  }

  .problem-solved.first-blood {
    background: #2e7d32 !important;
    color: #fff !important;
    border: 2px solid #1b5e20 !important;
    font-weight: 600 !important;
  }

  .problem-attempted {
    background: #f44336 !important;
    color: #fff !important;
  }

  .problem-pending {
    background: #ff9800 !important;
    color: #fff !important;
  }

  .problem-untried {
    background: #3a3a3a !important;
    color: #888 !important;
  }

  .solve-time {
    font-weight: 600;
    margin-bottom: 0.2rem;
  }

  .attempts {
    font-size: 0.7rem;
    opacity: 0.8;
  }

  .rank-cell.rank-gold {
    background: linear-gradient(135deg, #ffd700, #ffed4e) !important;
    color: #000 !important;
    font-weight: 700;
  }

  .rank-cell.rank-silver {
    background: linear-gradient(135deg, #c0c0c0, #e5e5e5) !important;
    color: #000 !important;
    font-weight: 700;
  }

  .rank-cell.rank-bronze {
    background: linear-gradient(135deg, #cd7f32, #daa520) !important;
    color: #000 !important;
    font-weight: 700;
  }

  .legend {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .legend h3 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 1rem 0;
    font-size: 1.2rem;
    font-weight: 500;
  }

  .legend-items {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Courier New', monospace;
    color: #cccccc;
  }

  .legend-color {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #555;
  }

  .empty-leaderboard {
    grid-column: 1 / -1;
    text-align: center;
    padding: 3rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  .empty-leaderboard p {
    margin: 0.5rem 0;
    font-size: 1.1rem;
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
    white-space: nowrap;
    max-width: fit-content;
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

  @media (max-width: 1200px) {
    .leaderboard-grid[style*="grid-template-columns"] {
      grid-template-columns: var(--grid-columns-tablet) !important;
    }
    
    .team-name {
      font-size: 0.85rem;
    }
    
    .team-meta {
      font-size: 0.75rem;
    }
  }

  @media (max-width: 768px) {
    .leaderboard-grid[style*="grid-template-columns"] {
      grid-template-columns: var(--grid-columns-mobile) !important;
      gap: 0;
    }
    
    .contest-info {
      flex-direction: column;
      gap: 1rem;
    }

    .legend-items {
      justify-content: center;
    }

    .refresh-info {
      flex-direction: column;
      gap: 1rem;
    }

    .grid-header > div,
    .grid-row > div {
      padding: 0.5rem 0.25rem;
      font-size: 0.8rem;
    }
  }
</style>