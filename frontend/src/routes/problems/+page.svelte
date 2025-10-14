<script lang="ts">
  import { API_BASE_URL } from '$lib/config';
  import { onMount } from 'svelte';
  import { authService } from '$lib/services/auth';
  import { goto } from '$app/navigation';

  interface Problem {
    id: string;
    time_limit?: string;
    memory_limit?: string;
    tests?: string;
  }

  interface Submission {
    id: number;
    problem_id: string;
    status: string;
    judge_response: any;
    submission_time?: string;
  }

  let problems: Problem[] = [];
  let submissions: Submission[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    await loadProblems();
  });

  async function loadProblems() {
    try {
      loading = true;
      error = null;

      // Load problems
      const problemsResponse = await authService.authenticatedRequest(`${API_BASE_URL}/general/problems`);
      if (!problemsResponse.ok) {
        throw new Error(`HTTP ${problemsResponse.status}`);
      }

      const problemsData = await problemsResponse.json();
      problems = problemsData.problems || [];

      // Load user submissions to determine problem status
      const submissionsResponse = await authService.authenticatedRequest(`${API_BASE_URL}/submission/all`);
      if (submissionsResponse.ok) {
        const submissionsData = await submissionsResponse.json();
        submissions = submissionsData || [];
      } else {
        console.warn('Failed to load submissions for status checking');
        submissions = [];
      }

    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load problems';
    } finally {
      loading = false;
    }
  }

  function getProblemStatus(problemId: string): string {
    if (!submissions || submissions.length === 0) {
      return 'untried';
    }

    const problemSubmissions = submissions.filter((sub: Submission) => sub.problem_id === problemId);
    if (problemSubmissions.length === 0) {
      return 'untried';
    }

    // Sort by submission time (most recent first)
    problemSubmissions.sort((a, b) => new Date(b.submission_time || 0).getTime() - new Date(a.submission_time || 0).getTime());

    // Check if any submission is accepted
    const acceptedSubmission = problemSubmissions.find((sub: Submission) => sub.status === 'accepted' || sub.status === 'Accepted');
    if (acceptedSubmission) {
      return 'solved';
    }

    // Check if any submission is pending
    const pendingSubmission = problemSubmissions.find((sub: Submission) => sub.status === 'pending');
    if (pendingSubmission) {
      return 'pending';
    }

    // Check the most recent submission for judge_response
    const mostRecent = problemSubmissions[0];

    // If judge_response is null or no results, it's pending
    if (!mostRecent.judge_response || !mostRecent.judge_response.results || mostRecent.judge_response.results.length === 0) {
      return 'pending';
    }

    // If we have results but no accepted submission, it's failed
    return 'failed';
  }

  function viewProblem(problemId: string) {
    goto(`/problem/${problemId}`);
  }
</script>

<svelte:head>
  <title>Problems - Mini-Competition</title>
</svelte:head>

<div class="problems-container">
  {#if !loading}
    <div class="problems-header">
      <h1>Problems</h1>
      <p>Select a problem to view details and submit solutions</p>
    </div>
  {/if}

  {#if loading}
    <div class="problems-loading">
      <div class="problems-spinner"></div>
      <p>Loading problems...</p>
    </div>
  {:else if error}
    <div class="problems-error-message">
      {error}
      <button on:click={loadProblems}>Try Again</button>
    </div>
  {:else if problems.length === 0}
    <div class="problems-empty-state">
      <p>No problems available at the moment.</p>
      <p>Check back later for new problems to solve!</p>
    </div>
  {:else}
    <div class="problems-table-container">
      <table class="problems-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Status</th>
            <th>Time Limit</th>
            <th>Memory Limit</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each problems as problem}
            {@const status = getProblemStatus(problem.id)}
            <tr class="problems-row problems-status-{status}">
              <td class="problems-id">
                <span class="problems-id-badge">#{problem.id}</span>
              </td>
              <td>
                <span class="problems-status-badge problems-status-{status}">
                  {status === 'solved' ? 'Solved' : status === 'pending' ? 'Pending' : status === 'failed' ? 'Attempted' : 'Not Tried'}
                </span>
              </td>
              <td class="problems-time-limit">
                {problem.time_limit || 'N/A'}s
              </td>
              <td class="problems-memory-limit">
                {problem.memory_limit || 'N/A'}MB
              </td>
              <td class="problems-actions">
                <button
                  class="problems-view-btn problems-btn-{status}"
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
  {/if}
</div>

<style>
  .problems-container {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1rem;
  }

  .problems-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .problems-header h1 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0;
    font-size: 2rem;
    font-weight: 500;
  }

  .problems-header p {
    color: #cccccc;
    font-size: 1.125rem;
    margin: 0.5rem 0 0 0;
  }

  .problems-loading {
    text-align: center;
    padding: 2rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  .problems-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #666;
    border-top: 4px solid #888;
    border-radius: 50%;
    animation: problems-spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes problems-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .problems-error-message {
    background: #4a4a4a;
    color: #ff6b6b;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    font-family: 'Courier New', monospace;
    border: 1px solid #666;
    text-align: center;
  }

  .problems-error-message button {
    margin-top: 1rem;
    background: #666;
    color: #f5f5f5;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-family: 'Courier New', monospace;
  }

  .problems-error-message button:hover {
    background: #777;
  }

  .problems-empty-state {
    text-align: center;
    padding: 3rem;
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  .problems-empty-state p {
    margin-bottom: 1rem;
    font-size: 1.1rem;
  }

  .problems-table-container {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    overflow: hidden;
  }

  .problems-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Courier New', monospace;
  }

  .problems-table th,
  .problems-table td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid #555;
  }

  .problems-table th {
    background: #4a4a4a;
    color: #f5f5f5;
    font-weight: 600;
  }

  .problems-table td {
    color: #cccccc;
  }

  /* Status-based row coloring */
  .problems-row.problems-status-solved {
    background: rgba(76, 175, 80, 0.1);
  }

  .problems-row.problems-status-pending {
    background: rgba(255, 152, 0, 0.1);
  }

  .problems-row.problems-status-failed {
    background: rgba(244, 67, 54, 0.1);
  }

  .problems-row:hover {
    background: #454545 !important;
  }

  .problems-id {
    font-weight: 600;
  }

  .problems-id-badge {
    background: #666;
    color: #f5f5f5;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .problems-status-badge {
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.875rem;
    display: inline-block;
  }

  .problems-status-solved {
    color: #4caf50;
    background: #3a3a3a;
    border: 1px solid #4caf50;
  }

  .problems-status-pending {
    color: #ff9800;
    background: #3a2a1a;
    border: 1px solid #ff9800;
  }

  .problems-status-failed {
    color: #f44336;
    background: #3a1a1a;
    border: 1px solid #f44336;
  }

  .problems-status-untried {
    color: #666;
    background: #3a3a3a;
    border: 1px solid #666;
  }

  .problems-time-limit, .problems-memory-limit {
    color: #aaa;
    font-weight: 500;
  }

  .problems-actions {
    text-align: center;
  }

  .problems-view-btn {
    background: #666;
    color: #f5f5f5;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: 'Courier New', monospace;
    font-weight: 500;
  }

  .problems-view-btn:hover {
    background: #777;
  }

  /* Status-specific button colors */
  .problems-btn-solved {
    background: #4caf50;
  }

  .problems-btn-solved:hover {
    background: #45a049;
  }

  .problems-btn-pending {
    background: #ff9800;
  }

  .problems-btn-pending:hover {
    background: #f57c00;
  }

  .problems-btn-failed {
    background: #f44336;
  }

  .problems-btn-failed:hover {
    background: #d32f2f;
  }

  @media (max-width: 768px) {
    .problems-container {
      padding: 1rem;
    }

    .problems-header h1 {
      font-size: 1.8rem;
    }

    .problems-table-container {
      overflow-x: auto;
    }

    .problems-table th,
    .problems-table td {
      padding: 0.75rem;
      font-size: 0.875rem;
    }

    .problems-view-btn {
      padding: 0.5rem 0.75rem;
      font-size: 0.75rem;
    }

    .problems-status-badge {
      padding: 0.2rem 0.5rem;
      font-size: 0.8rem;
    }
  }
</style>
