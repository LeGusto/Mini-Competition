<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { contestService } from '$lib/services/contest';
  import { onMount } from 'svelte';

  let contest: any = null;
  let problems: any[] = [];
  let loading = true;
  let error = '';
  let isRegistered = false;
  let accessStatus: any = null;
  let registering = false;
  let registrationMessage = '';
  let registrationData: any = null;

  $: contestId = $page.params.id;

  onMount(async () => {
    if (contestId) {
      await loadContest();
    }
  });

  async function loadContest() {
    try {
      loading = true;

      // Check access status first
      try {
        accessStatus = await contestService.getContestAccessStatus(contestId);
        isRegistered = accessStatus.is_registered;

        // Get registration data if user is registered
        if (isRegistered) {
          const regStatus = await contestService.checkRegistrationStatus(contestId);
          registrationData = regStatus.registration_data;
        }
      } catch (err) {
        console.error('Error checking access status:', err);
        accessStatus = { can_access: false, reason: 'Unable to check access status' };
      }

      // Determine what to load based on access status
      if (accessStatus?.can_access) {
        // User has full access - load complete contest details
        const contestsResponse = await authService.authenticatedRequest('http://localhost:5000/contests');
        if (contestsResponse.ok) {
          const contests = await contestsResponse.json();
          contest = contests.find((c: any) => c.id.toString() === contestId);

          if (!contest) {
            error = 'Contest not found';
            return;
          }
        } else {
          error = 'Failed to load contest details';
          return;
        }
      } else if (accessStatus && accessStatus.can_register) {
        // User can register - load basic contest info for registration
        const contestsResponse = await authService.authenticatedRequest('http://localhost:5000/contests');
        if (contestsResponse.ok) {
          const contests = await contestsResponse.json();
          contest = contests.find((c: any) => c.id.toString() === contestId);

          if (!contest) {
            error = 'Contest not found';
            return;
          }
        } else {
          error = 'Failed to load contest details';
          return;
        }
      } else if (accessStatus?.is_registered && accessStatus?.contest_status === 'upcoming') {
        // User is registered for upcoming contest - load basic info but don't show details
        const contestsResponse = await authService.authenticatedRequest('http://localhost:5000/contests');
        if (contestsResponse.ok) {
          const contests = await contestsResponse.json();
          const fullContest = contests.find((c: any) => c.id.toString() === contestId);

          if (!fullContest) {
            error = 'Contest not found';
            return;
          }

          // Show basic info but hide sensitive details
          contest = {
            id: fullContest.id,
            name: fullContest.name,
            description: 'You are registered for this contest. Details will be available when the contest starts.',
            start_time: fullContest.start_time,
            end_time: fullContest.end_time,
            problems: []
          };
        } else {
          error = 'Failed to load contest details';
          return;
        }
      } else {
        // User can't access and can't register
        contest = {
          id: parseInt(contestId),
          name: 'Contest',
          description: 'Access restricted',
          start_time: null,
          end_time: null,
          problems: []
        };
      }

      // Load problems only if user has access
      if (accessStatus?.can_access) {
        const response = await authService.authenticatedRequest(`http://localhost:5000/contest/${contestId}`);
        if (response.ok) {
          const data = await response.json();
          problems = data.problems || [];
        }
      }

    } catch (err) {
      error = 'Failed to load contest';
      console.error('Error loading contest:', err);
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
    
    // Handle new timezone-aware format
    let start, end;
    if (typeof startTime === 'object' && startTime.utc_iso) {
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

  function viewProblem(problemId: string) {
    goto(`/contest/${contestId}/problem/${problemId}`);
  }

  function goBack() {
    goto('/contests');
  }

  async function registerForContest() {
    try {
      registering = true;
      registrationMessage = '';

      const result = await contestService.registerForContest(contestId);

      if (result.success) {
        registrationMessage = result.message;
        // Reload contest to update access status
        await loadContest();
      } else {
        registrationMessage = result.message;
      }
    } catch (err) {
      registrationMessage = 'Registration failed';
      console.error('Error registering for contest:', err);
    } finally {
      registering = false;
    }
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
      <!-- Access Control Section -->
      {#if accessStatus && !accessStatus.can_access}
        {#if accessStatus.is_registered && accessStatus.contest_status === 'upcoming'}
          <!-- User is registered for upcoming contest -->
          <div class="access-control-card registered-card">
            <h2>Registration Confirmed</h2>
            <div class="access-message">
              <p>✅ You are registered for this contest!</p>
              <p>The contest details and problems will be available when the contest starts.</p>
              {#if registrationData}
                <p class="registration-time">Registered on: {formatDateTime(registrationData.registered_at)}</p>
              {/if}
            </div>
          </div>
        {:else if accessStatus.is_registered && accessStatus.contest_status === 'active'}
          <!-- User is registered for active contest but still can't access - this should not happen -->
          <div class="access-control-card restricted-card">
            <h2>Access Issue</h2>
            <div class="access-message">
              <p>There seems to be an issue with contest access. Please contact support.</p>
              <p>Reason: {accessStatus.reason}</p>
            </div>
          </div>
        {:else if !accessStatus.is_registered && accessStatus.can_register}
          <!-- User can register -->
          <div class="access-control-card">
            <h2>Registration Required</h2>
            <div class="access-message">
              <p>To participate in this contest, you need to register first.</p>
              <button
                class="btn btn-primary register-btn"
                on:click={registerForContest}
                disabled={registering}
              >
                {registering ? 'Registering...' : 'Register for Contest'}
              </button>
              {#if registrationMessage}
                <div class="registration-result {registrationMessage.includes('success') ? 'success' : 'error'}">
                  {registrationMessage}
                </div>
              {/if}
            </div>
          </div>
        {:else}
          <!-- User can't register (contest ended or other restriction) -->
          <div class="access-control-card restricted-card">
            <h2>Access Restricted</h2>
            <div class="access-message">
              <p>{accessStatus.reason}</p>
            </div>
          </div>
        {/if}
      {/if}

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
          {#if registrationData}
            <div class="detail-item">
              <div class="detail-label">Registered:</div>
              <span>{formatDateTime(registrationData.registered_at)}</span>
            </div>
          {/if}
        </div>
      </div>

      {#if accessStatus?.can_access && problems.length > 0}
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
      {:else if accessStatus?.can_access}
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

  .registration-status {
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-weight: 500;
  }

  .registration-status.registered {
    color: #4caf50;
    background: #3a3a3a;
    border: 1px solid #4caf50;
  }

  .registration-status.not-registered {
    color: #ff6b6b;
    background: #3a3a3a;
    border: 1px solid #ff6b6b;
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

  .detail-card, .problems-card, .access-control-card {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .detail-card h2, .problems-card h2, .access-control-card h2 {
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

  .access-message {
    text-align: center;
    padding: 1rem 0;
  }

  .access-message p {
    color: #cccccc;
    font-family: 'Courier New', monospace;
    font-size: 1.1rem;
    margin-bottom: 1rem;
  }

  .registration-time {
    color: #aaa !important;
    font-size: 0.9rem !important;
    margin-top: 0.5rem !important;
    font-style: italic;
  }

  .registered-card .access-message p:first-child {
    color: #4caf50;
    font-weight: 500;
  }

  .restricted-card .access-message p {
    color: #ff6b6b;
  }

  .register-btn {
    margin-top: 0.5rem;
  }

  .registration-result {
    margin-top: 1rem;
    padding: 0.75rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    text-align: center;
  }

  .registration-result.success {
    background: #3a3a3a;
    color: #4caf50;
    border: 1px solid #4caf50;
  }

  .registration-result.error {
    background: #3a3a3a;
    color: #ff6b6b;
    border: 1px solid #ff6b6b;
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