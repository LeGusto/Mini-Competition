<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { onMount } from 'svelte';
  import { SubmissionForm, ProblemStatement, SubmissionStatus, ProblemMeta, SubmissionPoller } from '$lib';

  let problem: any = null;
  let pdfUrl: string | null = null;
  let loading = true;
  let error = '';

  // Submission state
  let submissionResult: any = null;
  let polling = false;

  $: problemId = $page.params.id;

  onMount(async () => {
    if (problemId) {
      await loadProblem();
    }
  });

  async function loadProblem() {
    try {
      loading = true;
      error = '';

      // Load problem metadata
      const problemResponse = await authService.authenticatedRequest(
        `http://localhost:5000/general/problem/${problemId}/metadata`
      );
      if (problemResponse.ok) {
        problem = await problemResponse.json();
      } else {
        error = 'Problem not found';
        return;
      }

      // Load problem statement (PDF)
      await loadProblemStatement();

    } catch (err) {
      error = 'Failed to load problem';
      console.error('Error loading problem:', err);
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

  function goBackToProblems() {
    goto('/problems');
  }
</script>

<div class="problem-container">
  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading problem...</p>
    </div>
  {:else if error}
    <div class="error-message">{error}</div>
    <div class="navigation-buttons">
      <button class="btn btn-secondary" on:click={goBackToProblems}>
        Back to Problems
      </button>
    </div>
  {:else if problem}
    <div class="navigation-above">
      <button class="btn btn-secondary" on:click={goBackToProblems}>
        ← Back to Problems
      </button>
    </div>

    <div class="problem-header">
      <div class="header">
        <div class="problem-info">
          <h1>Problem {problemId}</h1>
        </div>
      </div>
    </div>

    <div class="content-layout">
      <!-- Submission Column -->
      <div class="submission-column">
        <div class="submission-card">
          <h2>Submit Solution</h2>

          <ProblemMeta {problem} />

          <SubmissionForm
            {problemId}
            onSubmissionStart={handleSubmissionStart}
            onSubmissionComplete={handleSubmissionComplete}
            onSubmissionError={handleSubmissionError}
          />

          <SubmissionStatus {submissionResult} {polling} />
        </div>
      </div>

      <!-- Problem Statement Column -->
      <div class="statement-column">
        <ProblemStatement {pdfUrl} {problemId} />
      </div>
    </div>

    <!-- Polling component (invisible) -->
    {#if submissionResult?.submission_id}
      <SubmissionPoller
        submissionId={submissionResult.submission_id}
        bind:polling
        onStatusUpdate={handleStatusUpdate}
        onPollingComplete={handlePollingComplete}
      />
    {/if}
  {/if}
</div>

<style>
  .problem-container {
    max-width: 2000px;
    margin: 2rem auto;
    padding: 0 1rem;
    width: 95%;
  }

  .loading {
    text-align: center;
    padding: 4rem 2rem;
    color: #888;
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

  .navigation-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }

  .navigation-above {
    display: flex;
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

  .problem-info h1 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.2;
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
    .problem-header {
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }

    .header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }



    .problem-info {
      text-align: left;
      margin: 0;
    }

    .navigation-above .btn {
      padding: 0.25rem 0.5rem;
      font-size: 0.8rem;
    }
  }
</style>