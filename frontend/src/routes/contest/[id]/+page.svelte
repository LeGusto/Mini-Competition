<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { onMount } from 'svelte';

  let contest: any = null;
  let problems: any[] = [];
  let loading = true;
  let error = '';

  $: contestId = $page.params.id;

  onMount(async () => {
    if (contestId) {
      await loadContest();
    }
  });

  async function loadContest() {
    try {
      loading = true;
      const response = await authService.authenticatedRequest(`http://localhost:5000/contest/${contestId}`);
      
      if (response.ok) {
        const data = await response.json();
        problems = data.problems || [];
        
        // Also get contest details
        const contestsResponse = await authService.authenticatedRequest('http://localhost:5000/contests');
        if (contestsResponse.ok) {
          const contests = await contestsResponse.json();
          contest = contests.find((c: any) => c.id.toString() === contestId);
        }
      } else {
        error = 'Failed to load contest';
      }
    } catch (err) {
      error = 'Failed to load contest';
      console.error('Error loading contest:', err);
    } finally {
      loading = false;
    }
  }

  function formatDateTime(isoString: string) {
    const date = new Date(isoString);
    return date.toLocaleString();
  }

  function getContestStatus(startTime: string, endTime: string) {
    const now = new Date();
    const start = new Date(startTime);
    const end = new Date(endTime);

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

  function viewProblem(problemId: string) {
    goto(`/contest/${contestId}/problem/${problemId}`);
  }

  function goBack() {
    goto('/contests');
  }
</script>

<div class="contest-container">
  {#if loading}
    <div class="loading">Loading contest...</div>
  {:else if error}
    <div class="error-message">{error}</div>
    <button class="btn btn-secondary" on:click={goBack}>
      Back to Contests
    </button>
  {:else if contest}
    {@const status = getContestStatus(contest.start_time, contest.end_time)}
    
    <div class="contest-header">
      <div class="contest-header-top">
        <button class="btn btn-secondary back-btn" on:click={goBack}>
          ← Back to Contests
        </button>

        <div class="contest-actions">
          <a href="/contest/{contestId}/leaderboard" class="btn btn-primary">
            📊 Leaderboard
          </a>
        </div>
      </div>

      <div class="contest-info">
        <h1>{contest.name}</h1>
        <div class="contest-meta">
          <span class="status-badge {getStatusClass(status)}">
            {getStatusText(status)}
          </span>
          <span class="contest-id">Contest #{contest.id}</span>
        </div>
      </div>
    </div>

    <div class="contest-details">
      <div class="detail-card">
        <h2>Contest Information</h2>
        <div class="detail-grid">
          <div class="detail-item">
            <div class="detail-label">Description:</div>
            <span>{contest.description || 'No description provided'}</span>
          </div>
          <div class="detail-item">
            <div class="detail-label">Start Time:</div>
            <span>{formatDateTime(contest.start_time)}</span>
          </div>
          <div class="detail-item">
            <div class="detail-label">End Time:</div>
            <span>{formatDateTime(contest.end_time)}</span>
          </div>
          <div class="detail-item">
            <div class="detail-label">Problems:</div>
            <span>{contest.problems ? contest.problems.length : 0} problems</span>
          </div>
        </div>
      </div>

      {#if problems.length > 0}
        <div class="problems-card">
          <h2>Problems</h2>
          <div class="problems-table">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Time Limit</th>
                  <th>Memory Limit</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {#each problems as problem}
                  <tr>
                    <td class="problem-id">{problem.id}</td>
                    <td>{problem.time_limit}ms</td>
                    <td>{problem.memory_limit}MB</td>
                    <td>
                      <button 
                        class="btn btn-small btn-primary" 
                        on:click={() => viewProblem(problem.id)}
                      >
                        View Problem
                      </button>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {:else}
        <div class="empty-problems">
          <p>No problems assigned to this contest yet.</p>
        </div>
      {/if}
    </div>
  {:else}
    <div class="error-message">Contest not found</div>
    <button class="btn btn-secondary" on:click={goBack}>
      Back to Contests
    </button>
  {/if}
</div>

<style>
  .contest-container {
    max-width: 1000px;
    margin: 2rem auto;
    padding: 0 1rem;
  }

  .loading {
    text-align: center;
    padding: 2rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
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

  .contest-header {
    margin-bottom: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .contest-header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }

  .contest-actions {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .back-btn {
    flex-shrink: 0;
  }

  .contest-info h1 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 0.5rem 0;
    font-size: 2.2rem;
    font-weight: 500;
  }

  .contest-meta {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .contest-id {
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  .status-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    font-family: 'Courier New', monospace;
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

  .contest-details {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .detail-card, .problems-card {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .detail-card h2, .problems-card h2 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 1rem 0;
    font-size: 1.4rem;
    font-weight: 500;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
  }

  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .detail-label {
    color: #aaa;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    font-weight: 600;
  }

  .detail-item span {
    color: #cccccc;
    font-family: 'Courier New', monospace;
  }

  .problems-table {
    overflow-x: auto;
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
    color: #cccccc;
  }

  th {
    background: #4a4a4a;
    color: #f5f5f5;
    font-weight: 600;
  }

  .problem-id {
    font-weight: 600;
    color: #f5f5f5;
  }

  .empty-problems {
    text-align: center;
    padding: 2rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
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
    background: #888;
    color: #f5f5f5;
  }

  .btn-primary:hover {
    background: #999;
  }

  .btn-secondary {
    background: #666;
    color: #f5f5f5;
  }

  .btn-secondary:hover {
    background: #777;
  }

  @media (max-width: 768px) {
    .detail-grid {
      grid-template-columns: 1fr;
    }

    .contest-meta {
      flex-direction: column;
      align-items: flex-start;
    }

    .contest-header-top {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }

    .contest-info h1 {
      font-size: 1.8rem;
    }
  }
</style>