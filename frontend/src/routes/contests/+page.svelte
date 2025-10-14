<script lang="ts">
  import { API_BASE_URL } from '$lib/config';
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { contestService } from '$lib/services/contest';
  import { authStore } from '$lib/stores/auth';
  import { onMount } from 'svelte';

  let contests: any[] = [];
  let loading = true;
  let error = '';
  let registeringContestId: string | null = null;

  // Check if current user is admin
  $: isAdmin = $authStore.user?.role === 'admin';

  onMount(async () => {
    await loadContests();
  });

  async function loadContests() {
    try {
      loading = true;
      const userTimezone = $authStore.user?.timezone || 'UTC';
      const response = await authService.authenticatedRequest(`${API_BASE_URL}/contests?timezone=${encodeURIComponent(userTimezone)}`);

      if (response.ok) {
        contests = await response.json();

        // Check registration status for each contest
        for (let contest of contests) {
          try {
            const regStatus = await contestService.checkRegistrationStatus(contest.id.toString());
            contest.isRegistered = regStatus.is_registered;
            contest.registrationData = regStatus.registration_data;
          } catch (err) {
            console.error(`Error checking registration for contest ${contest.id}:`, err);
            contest.isRegistered = false;
            contest.registrationData = null;
          }
        }
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

  async function registerAndViewContest(contestId: number) {
    try {
      registeringContestId = contestId.toString();
      const result = await contestService.registerForContest(contestId.toString());

      if (result.success) {
        // Reload contests to update registration status
        await loadContests();
        // Navigate to the contest
        goto(`/contest/${contestId}`);
      } else {
        console.error('Registration failed:', result.message);
        // Could show an error message here if needed
      }
    } catch (err) {
      console.error('Error registering for contest:', err);
    } finally {
      registeringContestId = null;
    }
  }

  function createContest() {
    goto('/contests/create');
  }
</script>

<div class="contests-container">
  {#if !loading}
    <div class="header">
      <h1>Contests</h1>
      {#if isAdmin}
        <button class="btn btn-primary" on:click={createContest}>
          Create Contest
        </button>
      {/if}
    </div>
  {/if}

  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading contests...</p>
    </div>
  {:else if error}
    <div class="error-message">{error}</div>
  {:else if contests.length === 0}
    <div class="empty-state">
      <p>No contests available.</p>
      {#if isAdmin}
        <button class="btn btn-primary" on:click={createContest}>
          Create Your First Contest
        </button>
      {:else}
        <p>Check back later for new contests!</p>
      {/if}
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
                {#if status === 'ended' || (contest.isRegistered && status === 'active')}
                  <button
                    class="btn btn-small btn-secondary"
                    on:click={() => viewContest(contest.id)}
                  >
                    View
                  </button>
                {:else if contest.isRegistered && status === 'upcoming'}
                  <button
                    class="btn btn-small btn-secondary"
                    on:click={() => viewContest(contest.id)}
                    disabled
                  >
                    Registered
                  </button>
                {:else}
                  <button
                    class="btn btn-small btn-primary"
                    on:click={() => registerAndViewContest(contest.id)}
                    disabled={registeringContestId === contest.id.toString()}
                  >
                    {registeringContestId === contest.id.toString() ? 'Registering...' : 'Register'}
                  </button>
                {/if}
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
    color: #f5f5f5;
    margin: 0;
    font-size: 2rem;
    font-weight: 500;
  }

  .loading {
    text-align: center;
    padding: 4rem 2rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #666;
    border-top: 4px solid #888;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
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

  .empty-state {
    text-align: center;
    padding: 3rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  .empty-state p {
    margin-bottom: 1rem;
    font-size: 1.1rem;
  }

  .contests-table {
    background: #3a3a3a;
    border: 1px solid #555;
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

  .contest-name {
    font-weight: 600;
    color: #f5f5f5;
  }

  .solved-count {
    text-align: center;
    font-weight: 600;
    color: #4caf50;
  }

  .problems-count {
    color: #aaa;
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
    white-space: nowrap;
    max-width: fit-content;
    text-align: center;
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

  .btn-secondary:disabled {
    background: #4a4a4a;
    color: #888;
    cursor: not-allowed;
    opacity: 0.7;
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