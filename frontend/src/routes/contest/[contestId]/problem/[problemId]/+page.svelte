<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { contestService } from '$lib/services/contest';
  import { onMount, onDestroy } from 'svelte';
  import { SubmissionForm, ProblemStatement, SubmissionStatus, ProblemMeta, SubmissionPoller } from '$lib';

  let contest: any = null;
  let problem: any = null;
  let pdfUrl: string | null = null;
  let loading = true;
  let error = '';
  let accessStatus: any = null;
  let contestTimer: string = '';
  let timerInterval: any = null;

  // Submission state
  let submissionResult: any = null;
  let polling = false;

  $: contestId = $page.params.contestId;
  $: problemId = $page.params.problemId;

  onMount(async () => {
    if (contestId && problemId) {
      await loadContestAndProblem();
    }
  });

  onDestroy(() => {
    if (timerInterval) {
      clearInterval(timerInterval);
    }
  });

  async function loadContestAndProblem() {
    try {
      loading = true;
      error = '';

      // Check access status first
      try {
        accessStatus = await contestService.getContestAccessStatus(contestId);
      } catch (err) {
        console.error('Error checking access status:', err);
        accessStatus = { can_access: false, reason: 'Unable to check access status' };
      }

      if (!accessStatus.can_access) {
        error = accessStatus.reason;
        return;
      }

      // Load contest details based on access status
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

          // Check if problem is part of this contest
          if (!contest.problems || !contest.problems.includes(problemId)) {
            error = 'Problem not found in this contest';
            return;
          }

          // Start contest timer
          startContestTimer(contest);
        }
      } else if (accessStatus?.is_registered && accessStatus?.contest_status === 'upcoming') {
        // User is registered for upcoming contest
        contest = {
          id: parseInt(contestId),
          name: 'Contest',
          description: 'You are registered for this contest. Details will be available when the contest starts.',
          start_time: null,
          end_time: null,
          problems: []
        };
        error = 'Contest has not started yet. You are registered and will be able to view problems when it begins.';
        return;
      } else {
        // User can't access the problem
        contest = {
          id: parseInt(contestId),
          name: 'Contest',
          description: 'Access restricted',
          start_time: null,
          end_time: null,
          problems: []
        };
        error = accessStatus?.reason || 'Access denied';
        return;
      }

      // Load problem metadata
      const problemResponse = await authService.authenticatedRequest(
        `http://localhost:5000/general/problem/${problemId}/metadata`
      );
      if (problemResponse.ok) {
        problem = await problemResponse.json();
      }

      // Load problem statement (PDF)
      await loadProblemStatement();

    } catch (err) {
      error = 'Failed to load contest problem';
      console.error('Error loading contest problem:', err);
    } finally {
      loading = false;
    }
  }

  async function loadProblemStatement() {
    try {
      const response = await authService.authenticatedRequest(
        `http://localhost:5000/general/problem/${problemId}/statement`
      );
      
      if (response.ok) {
        const blob = await response.blob();
        if (pdfUrl) {
          URL.revokeObjectURL(pdfUrl);
        }
        pdfUrl = URL.createObjectURL(blob);
      } else {
        console.warn('Failed to load problem statement');
      }
    } catch (err) {
      console.error('Error loading problem statement:', err);
    }
  }

  function handleSubmissionStart() {
    submissionResult = null;
    polling = false;
  }

  function handleSubmissionComplete(result: any) {
    submissionResult = result;
    polling = true;
  }

  function handleSubmissionError(error: string) {
    console.error('Submission error:', error);
  }

  function handleStatusUpdate(data: any) {
    submissionResult = { ...submissionResult, ...data };
  }

  function handlePollingComplete() {
    polling = false;
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



  function goBackToContest() {
    goto(`/contest/${contestId}`);
  }

  function startContestTimer(contest: any) {
    if (timerInterval) {
      clearInterval(timerInterval);
    }

    const updateTimer = () => {
      if (!contest) return;

      const now = new Date();
      let targetTime: Date | null = null;
      let timerType = '';

      // Handle timezone-aware format
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

      if (now < startTime) {
        targetTime = startTime;
        timerType = 'Starts in: ';
      } else if (now >= startTime && now < endTime) {
        targetTime = endTime;
        timerType = 'Ends in: ';
      } else {
        contestTimer = 'Contest Ended';
        return;
      }

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
</script>

<div class="contest-problem-container">
  {#if loading}
    <div class="loading">Loading problem...</div>
  {:else if error}
    <div class="error-message">{error}</div>
    {#if accessStatus && !accessStatus.can_access}
      {#if accessStatus.is_registered && accessStatus.contest_status === 'upcoming'}
        <!-- User is registered for upcoming contest -->
        <div class="access-denied-card registered-card">
          <h2>Registration Confirmed</h2>
          <p>✅ You are registered for this contest!</p>
          <p>The contest details and problems will be available when the contest starts.</p>
        </div>
      {:else if !accessStatus.is_registered && accessStatus.can_register}
        <!-- User can register -->
        <div class="access-denied-card">
          <h2>Registration Required</h2>
          <p>You need to register for this contest to view problems.</p>
          <button class="btn btn-primary" on:click={goBackToContest}>
            Register for Contest
          </button>
        </div>
      {:else}
        <!-- User can't register -->
        <div class="access-denied-card restricted-card">
          <h2>Access Restricted</h2>
          <p>{accessStatus.reason}</p>
        </div>
      {/if}
    {/if}
    <div class="navigation-buttons">
      <button class="btn btn-secondary" on:click={goBackToContest}>
        Back to Contest
      </button>
    </div>
  {:else if contest && problem}
    {@const contestStatus = getContestStatus(contest.start_time, contest.end_time)}

    <div class="navigation-above">
      <button class="btn btn-secondary" on:click={goBackToContest}>
        ← Back to Contest
      </button>
    </div>

    <div class="problem-header">
      <div class="header">
        <div class="problem-info">
          <h1>Problem {problemId}</h1>
          {#if contestTimer}
            <div class="contest-timer-display">{contestTimer}</div>
          {/if}
        </div>
      </div>
    </div>

    <div class="content-layout">
      <!-- Submission Column -->
      <div class="submission-column">
        <div class="submission-card">
          <h2>Submit Solution</h2>
          
          {#if contestStatus === 'ended'}
            <div class="contest-ended-notice">
              <p>This contest has ended. Submissions are no longer accepted.</p>
            </div>
          {:else if contestStatus === 'upcoming'}
            <div class="contest-upcoming-notice">
              <p>This contest hasn't started yet. Submissions will be available when the contest begins.</p>
            </div>
          {:else}
            <!-- Active contest - show submission form -->
            <ProblemMeta {problem} timeUnit="ms" />

            <SubmissionForm
              {problemId}
              onSubmissionStart={handleSubmissionStart}
              onSubmissionComplete={handleSubmissionComplete}
              onSubmissionError={handleSubmissionError}
            />

            <SubmissionStatus {submissionResult} {polling} />
          {/if}
        </div>
      </div>

      <!-- Problem Statement Column -->
      <div class="statement-column">
        <ProblemStatement {pdfUrl} {problemId} height={700} />
      </div>
    </div>
  {/if}

  <!-- Polling component (invisible) -->
  {#if submissionResult?.submission_id}
    <SubmissionPoller
      submissionId={submissionResult.submission_id}
      bind:polling
      onStatusUpdate={handleStatusUpdate}
      onPollingComplete={handlePollingComplete}
    />
  {/if}
</div>

<style>
  .contest-problem-container {
    max-width: 2000px;
    margin: 2rem auto;
    padding: 0 1rem;
    width: 95%;
  }

  .loading {
    text-align: center;
    padding: 1rem;
    color: #888;
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

  .access-denied-card {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
    text-align: center;
  }

  .access-denied-card h2 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 1rem 0;
    font-size: 1.5rem;
    font-weight: 500;
  }

  .access-denied-card p {
    color: #cccccc;
    font-family: 'Courier New', monospace;
    font-size: 1.1rem;
    margin-bottom: 1rem;
  }

  .access-denied-card.registered-card p:first-child {
    color: #4caf50;
    font-weight: 500;
  }

  .access-denied-card.restricted-card p {
    color: #ff6b6b;
  }

  .navigation-above {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .navigation-above .btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.85rem;
    width: auto !important;
    flex-shrink: 0 !important;
    min-width: auto !important;
    max-width: fit-content !important;
    display: inline-block !important;
  }

  .problem-header {
    background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
    border: 1px solid #555;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 60px;
  }

  .problem-info {
    flex: 1;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .contest-timer-display {
    font-size: 0.9rem;
  }



  .navigation-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }

  .problem-info h1 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.2;
  }

  .contest-timer-display {
    color: #ef5350;
    font-family: 'Courier New', monospace;
    font-size: 1rem;
    font-weight: 600;
    background: #3a1a1a;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #f44336;
    text-align: center;
    height: fit-content;
  }





  .content-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 2rem;
  }

  .statement-column {
    min-width: 0;
  }

  .submission-card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 1rem;
  }

  .submission-card h2 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
  }

  .contest-ended-notice, .contest-upcoming-notice {
    background: #333;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1rem;
    color: #ccc;
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
    text-decoration: none;
    display: inline-block;
  }

  .btn:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }



  .btn-primary {
    background: #888;
    color: #f5f5f5;
  }

  .btn-primary:hover:not(:disabled) {
    background: #999;
  }

  .btn-secondary {
    background: #444;
    color: #e0e0e0;
  }

  .btn-secondary:hover {
    background: #555;
  }

  @media (max-width: 1024px) {
    .content-layout {
      grid-template-columns: 1fr;
    }

    .statement-column {
      order: -1;
    }
  }

  @media (max-width: 768px) {
    .navigation-above {
      margin-bottom: 0.5rem;
    }

    .navigation-above .btn {
      padding: 0.25rem 0.5rem;
      font-size: 0.8rem;
      width: auto !important;
      flex-shrink: 0 !important;
      min-width: auto !important;
      max-width: fit-content !important;
      display: inline-block !important;
    }

    .problem-header {
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }

    .header {
      flex-direction: column;
      gap: 0.5rem;
      align-items: center;
    }

    .problem-info {
      text-align: center;
      gap: 0.25rem;
    }

    .contest-timer-display {
      font-size: 0.8rem;
    }
  }
</style>