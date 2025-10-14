<script lang="ts">
  import { API_BASE_URL } from '$lib/config';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { contestService } from '$lib/services/contest';
  import { onMount, onDestroy } from 'svelte';

  let contest: any = null;
  let problems: any[] = [];
  let loading = true;
  let error = '';
  let isRegistered = false;
  let accessStatus: any = null;
  let registering = false;
  let registrationMessage = '';
  let registrationData: any = null;
  let userSubmissions: any[] = [];
  let pendingSubmissions: any[] = [];
  let contestTimer: string = '';
  let timerInterval: any = null;
  let previousContestStatus: 'not_started' | 'in_progress' | 'ended' = 'not_started';

  $: contestId = $page.params.id;

  onMount(async () => {
    if (contestId) {
      await loadContest();
    }
  });

  onDestroy(() => {
    if (timerInterval) {
      clearInterval(timerInterval);
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
        const contestsResponse = await authService.authenticatedRequest(`${API_BASE_URL}/contests`);
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
        const contestsResponse = await authService.authenticatedRequest(`${API_BASE_URL}/contests`);
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
        const contestsResponse = await authService.authenticatedRequest(`${API_BASE_URL}/contests`);
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
        const response = await authService.authenticatedRequest(`${API_BASE_URL}/contest/${contestId}`);
        if (response.ok) {
          const data = await response.json();
          problems = data.problems || [];
          // Load user submissions for this contest
          await loadUserSubmissions();
          // Start contest timer
          startContestTimer(contest);
        }
      } else {
        // Start contest timer even if user doesn't have access (for upcoming contests)
        startContestTimer(contest);
      }

    } catch (err) {
      error = 'Failed to load contest';
      console.error('Error loading contest:', err);
    } finally {
      loading = false;
    }
  }

  async function loadUserSubmissions() {
    try {
      // Load contest submissions
      const contestResponse = await authService.authenticatedRequest(`${API_BASE_URL}/contest/${contestId}/submissions`);
      if (contestResponse.ok) {
        userSubmissions = await contestResponse.json();
      } else {
        console.error('Failed to load contest submissions');
        userSubmissions = [];
      }

      // Also load regular submissions to check for pending status
      const submissionsResponse = await authService.authenticatedRequest(`${API_BASE_URL}/submission/all`);
      if (submissionsResponse.ok) {
        const allSubmissions = await submissionsResponse.json();
        // Store pending submissions separately for status checking
        pendingSubmissions = allSubmissions.filter((sub: any) => sub.status === 'pending');
      } else {
        console.error('Failed to load regular submissions');
        pendingSubmissions = [];
      }

      console.log('User submissions:', userSubmissions);
      console.log('Pending submissions:', pendingSubmissions);
    } catch (err) {
      console.error('Error loading user submissions:', err);
      userSubmissions = [];
      pendingSubmissions = [];
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

  function startContestTimer(contest: any) {
    if (timerInterval) {
      clearInterval(timerInterval);
    }

    // Track if this is the first update
    let isFirstUpdate = true;

    const updateTimer = () => {
      if (!contest) return;

      const now = new Date();
      let targetTime: Date | null = null;
      let timerType = '';

      // Handle new timezone-aware format
      let startTime: Date | null = null;
      let endTime: Date | null = null;

      if (contest.start_time && typeof contest.start_time === 'object' && contest.start_time.utc_iso) {
        startTime = new Date(contest.start_time.utc_iso);
        endTime = new Date(contest.end_time.utc_iso);
      } else if (contest.start_time && contest.end_time) {
        startTime = new Date(contest.start_time);
        endTime = new Date(contest.end_time);
      }

      if (!startTime || !endTime) {
        contestTimer = '';
        return;
      }

      // Determine current contest status
      let currentStatus: 'not_started' | 'in_progress' | 'ended';
      if (now < startTime) {
        currentStatus = 'not_started';
        targetTime = startTime;
        timerType = 'Starts in: ';
      } else if (now >= startTime && now < endTime) {
        currentStatus = 'in_progress';
        targetTime = endTime;
        timerType = 'Ends in: ';
      } else {
        currentStatus = 'ended';
        contestTimer = 'Contest Ended';
        return;
      }

 

      if (!isFirstUpdate && previousContestStatus === 'not_started' && currentStatus === 'in_progress') {
        console.log('Contest has started! Refreshing page...');
        window.location.reload();
        return;
      }


      previousContestStatus = currentStatus;
      isFirstUpdate = false;

      const timeDiff = targetTime.getTime() - now.getTime();

      if (timeDiff <= 0) {
        contestTimer = timerType === 'Starts in: ' ? 'Contest Starting...' : 'Contest Ended';
        return;
      }

      const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

      if (days > 0) {
        contestTimer = `${timerType}${days}d ${hours}h ${minutes}m`;
      } else if (hours > 0) {
        contestTimer = `${timerType}${hours}h ${minutes}m ${seconds}s`;
      } else {
        contestTimer = `${timerType}${minutes}m ${seconds}s`;
      }
    };

    updateTimer();
    timerInterval = setInterval(updateTimer, 1000);
  }

  async function viewProblem(problemId: string) {
    // Refresh user submissions when viewing a problem to catch any recent submissions
    await loadUserSubmissions();
    goto(`/contest/${contestId}/problem/${problemId}`);
  }



  function goBack() {
    goto('/contests');
  }

    function getProblemStatus(problemId: number): string {
    // Check if there are any contest submissions for this problem
    const problemSubmissions = userSubmissions.filter((sub: any) => sub.problem_id === problemId);

    if (!userSubmissions || userSubmissions.length === 0 || problemSubmissions.length === 0) {
      // No contest submissions yet - check main submissions table for pending
      const pendingForProblem = pendingSubmissions.filter((sub: any) => sub.problem_id === problemId);
      if (pendingForProblem.length > 0) {
        return 'pending'; // orange
      }
      return 'untried'; // gray
    }

    // Sort by submission time (most recent first)
    problemSubmissions.sort((a, b) => new Date(b.submission_time).getTime() - new Date(a.submission_time).getTime());

    // Check if any submission is accepted
    const acceptedSubmission = problemSubmissions.find((sub: any) => sub.is_accepted);
    if (acceptedSubmission) {
      return 'solved'; // green
    }

    // No accepted submission - check if there are pending submissions in main table
    const pendingForProblem = pendingSubmissions.filter((sub: any) => sub.problem_id === problemId);
    if (pendingForProblem.length > 0) {
      return 'pending'; // orange
    }

    // Check the most recent submission for judge_response
    const mostRecent = problemSubmissions[0];

    // If judge_response is null or no results, it's pending
    if (!mostRecent.judge_response || !mostRecent.judge_response.results || mostRecent.judge_response.results.length === 0) {
      return 'pending'; // orange
    }

    // If we have results but no accepted submission, it's failed
    return 'failed'; // red
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
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading contest...</p>
    </div>
  {:else if error}
    <div class="error-message">{error}</div>
  {:else if contest}
    {@const status = getContestStatus(contest.start_time, contest.end_time)}
    
    <div class="contest-header">
      <div class="contest-info">
        <h1>{contest.name}</h1>
        <div class="contest-meta">
          <span class="status-badge {getStatusClass(status)}">
            {getStatusText(status)}
          </span>
          <span class="contest-id">Contest #{contest.id}</span>
          {#if contestTimer}
            <span class="contest-timer">{contestTimer}</span>
          {/if}
          <div class="contest-actions">
            <a href="/contest/{contestId}/leaderboard" class="btn btn-leaderboard">
              Leaderboard
            </a>
          </div>
        </div>
      </div>


    </div>

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

    <!-- Problems Section - FULL WIDTH TOP -->
    {#if accessStatus?.can_access && problems.length > 0}
      <div class="problems-card">
        <h2>Contest Problems</h2>
        <div class="problems-grid">
          {#each problems as problem, index}
            <div class="contest-problem-item status-{getProblemStatus(problem.id)}">
              <div class="problem-header">
                <div class="problem-letter">{String.fromCharCode(65 + index)}</div>
                <div class="problem-info">
                  <div class="problem-id">Problem {problem.id}</div>
                  <div class="problem-limits">
                    <span class="limit">Time: {problem.time_limit}ms</span>
                    <span class="limit">Memory: {problem.memory_limit}MB</span>
                  </div>
                </div>
              </div>
              <button
                class="btn btn-problem"
                on:click={() => viewProblem(problem.id)}
              >
                Solve Problem
              </button>
            </div>
          {/each}
        </div>
      </div>
    {:else if accessStatus?.can_access}
      <div class="empty-problems">
        <h3>No Problems Yet</h3>
        <p>Problems will be added to this contest soon.</p>
      </div>
    {/if}

    <!-- Contest Details Section - BOTTOM -->
    <div class="bottom-details">
      <div class="detail-card">
        <h2>Contest Details</h2>
        <div class="detail-grid-bottom">
          <div class="detail-item">
            <div class="detail-label">Start Time:</div>
            <span class="detail-value">{formatDateTime(contest.start_time)}</span>
          </div>
          <div class="detail-item">
            <div class="detail-label">End Time:</div>
            <span class="detail-value">{formatDateTime(contest.end_time)}</span>
          </div>
          <div class="detail-item">
            <div class="detail-label">Problems:</div>
            <span class="detail-value">{contest.problems ? contest.problems.length : 0} problems</span>
          </div>
          {#if registrationData}
            <div class="detail-item">
              <div class="detail-label">Registered:</div>
              <span class="detail-value">{formatDateTime(registrationData.registered_at)}</span>
            </div>
          {/if}
        </div>
      </div>

      <!-- Description Section -->
      {#if contest.description && contest.description !== 'No description provided'}
        <details class="description-card">
          <summary>Contest Description</summary>
          <div class="description-content">
            <p>{contest.description}</p>
          </div>
        </details>
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
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
  }

  .loading {
    text-align: center;
    padding: 4rem 2rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
    font-size: 1.2rem;
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

  .contest-header {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto 2rem auto;
    padding: 2.5rem 2rem;
    background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
    border: 1px solid #555;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
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

  .btn.back-btn {
    flex-shrink: 0;
    padding: 0.5rem 1rem !important;
    font-size: 0.9rem !important;
    width: auto !important;
    max-width: max-content !important;
    min-width: auto !important;
  }

  .contest-info h1 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 1rem 0;
    font-size: 2.5rem;
    font-weight: 600;
    line-height: 1.1;
    letter-spacing: -0.025em;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .contest-meta {
    display: flex;
    gap: 1.5rem;
    align-items: center;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .contest-meta .contest-actions {
    margin-left: auto;
  }

  .contest-id {
    color: #cccccc;
    font-family: 'Courier New', monospace;
    font-size: 0.95rem;
    font-weight: 500;
    background: #4a4a4a;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #666;
  }

  .contest-timer {
    color: #ef5350;
    font-family: 'Courier New', monospace;
    font-size: 0.95rem;
    font-weight: 600;
    background: #3a1a1a;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #f44336;
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
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    font-family: 'Courier New', monospace;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
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

  .bottom-details {
    margin-top: 2rem;
  }

  .detail-grid-bottom {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }

  .detail-card, .problems-card, .access-control-card, .description-card {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .detail-card h2, .problems-card h2, .access-control-card h2, .description-card summary {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 1rem 0;
    font-size: 1.4rem;
    font-weight: 500;
  }

  .detail-list {
    display: flex;
    flex-direction: column;
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

  /* New leaderboard button styles */
  .btn-leaderboard {
    background: linear-gradient(135deg, #ff6b35, #f7931e);
    color: white;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3);
    width: auto !important;
    max-width: max-content !important;
    min-width: auto !important;
  }

  .btn-leaderboard:hover {
    background: linear-gradient(135deg, #ff5722, #f57c00);
  }



  /* Problems grid layout */
  .problems-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
  }

  /* NEW CLEAN PROBLEM ITEM STYLES */
  .contest-problem-item {
    background: #3a3a3a;
    border: 2px solid #666;
    border-radius: 8px;
    padding: 1.5rem;
    transition: border-color 0.2s ease;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .contest-problem-item:hover {
    border-color: #888;
  }

  /* STATUS COLORS - CLEAN APPROACH */
  .contest-problem-item.status-untried {
    background: #2a2a2a;
    border-color: #666;
  }

  .contest-problem-item.status-untried:hover {
    border-color: #888;
  }

  .contest-problem-item.status-solved {
    background: #1a3a1a;
    border-color: #4caf50;
  }

  .contest-problem-item.status-solved:hover {
    border-color: #66bb6a;
  }

  .contest-problem-item.status-failed {
    background: #3a1a1a;
    border-color: #f44336;
  }

  .contest-problem-item.status-failed:hover {
    border-color: #ef5350;
  }

  .contest-problem-item.status-pending {
    background: #3a2a1a;
    border-color: #ff9800;
  }

  .contest-problem-item.status-pending:hover {
    border-color: #ffa726;
  }

  .problem-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .problem-letter {
    background: #666;
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 1.2rem;
    font-family: 'Courier New', monospace;
  }

  /* Letter badge colors based on status */
  .contest-problem-item.status-untried .problem-letter {
    background: #666;
  }

  .contest-problem-item.status-solved .problem-letter {
    background: #4caf50;
  }

  .contest-problem-item.status-failed .problem-letter {
    background: #f44336;
  }

  .contest-problem-item.status-pending .problem-letter {
    background: #ff9800;
  }

  .problem-info {
    flex: 1;
  }

  .problem-id {
    color: #f5f5f5;
    font-weight: 600;
    font-family: 'Courier New', monospace;
    margin-bottom: 0.25rem;
  }

  .problem-limits {
    display: flex;
    gap: 1rem;
    font-size: 0.85rem;
  }

  .limit {
    color: #aaa;
    font-family: 'Courier New', monospace;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .btn-problem {
    background: #666;
    color: white;
    width: 100%;
    font-weight: 600;
    padding: 0.75rem;
    font-size: 0.95rem;
  }

  .btn-problem:hover {
    background: #777;
  }

  /* Button colors based on status */
  .contest-problem-item.status-untried .btn-problem {
    background: #666;
  }

  .contest-problem-item.status-untried .btn-problem:hover {
    background: #777;
  }

  .contest-problem-item.status-solved .btn-problem {
    background: #4caf50;
  }

  .contest-problem-item.status-solved .btn-problem:hover {
    background: #45a049;
  }

  .contest-problem-item.status-failed .btn-problem {
    background: #f44336;
  }

  .contest-problem-item.status-failed .btn-problem:hover {
    background: #d32f2f;
  }

  .contest-problem-item.status-pending .btn-problem {
    background: #ff9800;
  }

  .contest-problem-item.status-pending .btn-problem:hover {
    background: #f57c00;
  }

  /* Empty problems styling */
  .empty-problems {
    text-align: center;
    padding: 2rem;
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
  }

  .empty-problems h3 {
    color: #f5f5f5;
    font-family: 'Courier New', monospace;
    margin-bottom: 0.5rem;
    font-size: 1.4rem;
  }

  .empty-problems p {
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  /* Improved detail styles */
  .detail-value {
    color: #f5f5f5 !important;
    font-weight: 500;
  }

  /* Description collapsible */
  .description-card {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    overflow: hidden;
  }

  .description-card summary {
    padding: 1rem 1.5rem;
    cursor: pointer;
    background: #4a4a4a;
    color: #f5f5f5;
    font-family: 'Courier New', monospace;
    font-weight: 600;
    user-select: none;
    transition: background 0.2s ease;
  }

  .description-card summary:hover {
    background: #555;
  }

  .description-content {
    padding: 1.5rem;
  }

  .description-content p {
    color: #cccccc;
    font-family: 'Courier New', monospace;
    line-height: 1.6;
    margin: 0;
  }

  /* FORCED OVERRIDES FOR GLOBAL CSS ISSUES */
  .contest-header .btn {
    width: auto !important;
  }
  
  .contest-actions .btn {
    width: auto !important;
  }



  @media (max-width: 768px) {
    .contest-container {
      padding: 1rem;
    }

    .contest-header {
      padding: 2rem 1rem;
      margin-bottom: 2rem;
    }

    .contest-meta {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .contest-meta .contest-actions {
      margin-left: 0;
      margin-top: 0.5rem;
    }

    .contest-header-top {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }

    .contest-info h1 {
      font-size: 2rem;
    }

    .problems-grid {
      grid-template-columns: 1fr;
    }

    .detail-grid-bottom {
      grid-template-columns: 1fr;
    }

    .problem-limits {
      flex-direction: column;
      gap: 0.5rem;
    }

    .btn-leaderboard {
      justify-content: center;
      width: auto !important;
    }

    .btn.back-btn {
      width: auto !important;
    }
  }
</style>