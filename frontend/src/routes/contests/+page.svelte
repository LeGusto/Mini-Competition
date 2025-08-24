<script lang="ts">
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { onMount } from 'svelte';

  let contests: any[] = [];
  let loading = true;
  let error = '';

  onMount(async () => {
    await loadContests();
  });

  async function loadContests() {
    try {
      loading = true;
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const response = await authService.authenticatedRequest(`http://localhost:5000/contests?timezone=${encodeURIComponent(userTimezone)}`);
      
      if (response.ok) {
        contests = await response.json();
      } else {
        error = 'Failed to load contests';
      }
    } catch (err) {
      error = 'Failed to load contests';
      console.error('Error loading contests:', err);
    } finally {
      loading = false;
    }
  }

  function formatDateTime(timeData: any) {
    if (!timeData) return 'N/A';
    
    // Handle new timezone-aware format
    if (typeof timeData === 'object' && timeData.formatted) {
      return `${timeData.formatted} ${timeData.timezone}`;
    }
    
    // Fallback for old format
    const date = new Date(timeData);
    return date.toLocaleString();
  }

  function getContestStatus(startTime: any, endTime: any) {
    const now = new Date();
    
    // Use UTC times for status calculation to avoid timezone issues
    let start, end;
    
    if (typeof startTime === 'object' && startTime.utc_iso) {
      // New timezone-aware format
      start = new Date(startTime.utc_iso);
      end = new Date(endTime.utc_iso);
    } else {
      // Fallback for old format
      start = new Date(startTime);
      end = new Date(endTime);
    }

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

  function viewContest(contestId: number) {
    goto(`/contest/${contestId}`);
  }

  function createContest() {
    goto('/contests/create');
  }
</script>

<div class="contests-container">
  <div class="header">
    <h1>Contests</h1>
    <button class="btn btn-primary" on:click={createContest}>
      Create Contest
    </button>
  </div>

  {#if loading}
    <div class="loading">Loading contests...</div>
  {:else if error}
    <div class="error-message">{error}</div>
  {:else if contests.length === 0}
    <div class="empty-state">
      <p>No contests available.</p>
      <button class="btn btn-primary" on:click={createContest}>
        Create Your First Contest
      </button>
    </div>
  {:else}
    <div class="contests-table">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Solved</th>
            <th>Start Time</th>
            <th>End Time</th>
            <th>Problems</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each contests as contest}
            {@const status = getContestStatus(contest.start_time, contest.end_time)}
            <tr>
              <td>{contest.id}</td>
              <td class="contest-name">{contest.name}</td>
              <td class="solved-count">
                {contest.solved_problems || 0} / {contest.problems ? contest.problems.length : 0}
              </td>
              <td>{formatDateTime(contest.start_time)}</td>
              <td>{formatDateTime(contest.end_time)}</td>
              <td class="problems-count">
                {contest.problems ? contest.problems.length : 0} problems
              </td>
              <td>
                <span class="status-badge {getStatusClass(status)}">
                  {getStatusText(status)}
                </span>
              </td>
              <td>
                <button 
                  class="btn btn-small btn-secondary" 
                  on:click={() => viewContest(contest.id)}
                >
                  View
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .contests-container {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1rem;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  h1 {
    font-family: 'Courier New', monospace;
    color: #64b5f6;
    margin: 0;
    font-size: 2rem;
  }

  .loading {
    text-align: center;
    padding: 2rem;
    color: #888;
    font-family: 'Courier New', monospace;
  }

  .error-message {
    background: #f44336;
    color: white;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    font-family: 'Courier New', monospace;
  }

  .empty-state {
    text-align: center;
    padding: 3rem;
    color: #888;
    font-family: 'Courier New', monospace;
  }

  .empty-state p {
    margin-bottom: 1rem;
    font-size: 1.1rem;
  }

  .contests-table {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    overflow: hidden;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Courier New', monospace;
  }

  th, td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid #333;
  }

  th {
    background: #2d2d2d;
    color: #64b5f6;
    font-weight: 600;
  }

  td {
    color: #e0e0e0;
  }

  .contest-name {
    font-weight: 600;
    color: #fff;
  }

  .solved-count {
    text-align: center;
    font-weight: 600;
    color: #4caf50;
  }

  .problems-count {
    color: #888;
    font-size: 0.9rem;
  }

  .status-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .status-upcoming {
    background: #2196f3;
    color: white;
  }

  .status-active {
    background: #4caf50;
    color: white;
  }

  .status-ended {
    background: #757575;
    color: white;
  }

  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: inline-block;
  }

  .btn-small {
    padding: 0.375rem 0.75rem;
    font-size: 0.85rem;
  }

  .btn-primary {
    background: #64b5f6;
    color: #000;
  }

  .btn-primary:hover {
    background: #42a5f5;
  }

  .btn-secondary {
    background: #444;
    color: #e0e0e0;
  }

  .btn-secondary:hover {
    background: #555;
  }

  @media (max-width: 768px) {
    .header {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }

    .contests-table {
      overflow-x: auto;
    }

    table {
      min-width: 800px;
    }
  }
</style>