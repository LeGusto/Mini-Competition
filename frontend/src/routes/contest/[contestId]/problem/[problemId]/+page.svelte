<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { onMount } from 'svelte';

  let contest: any = null;
  let problem: any = null;
  let pdfUrl: string | null = null;
  let loading = true;
  let error = '';
  
  // Submission form state
  let selectedFile: File | null = null;
  let selectedLanguage = 'cpp';
  let submitting = false;
  let submissionResult: any = null;
  let submissionError = '';
  let submissionId: string | null = null;
  let polling = false;

  $: contestId = $page.params.contestId;
  $: problemId = $page.params.problemId;

  onMount(async () => {
    if (contestId && problemId) {
      await loadContestAndProblem();
    }
  });

  async function loadContestAndProblem() {
    try {
      loading = true;
      error = '';

      // Load contest details
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

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      selectedFile = target.files[0];
      submissionResult = null;
      submissionError = '';
    }
  }

  async function submitSolution() {
    if (!selectedFile) {
      submissionError = 'Please select a file';
      return;
    }

    try {
      submitting = true;
      submissionError = '';
      submissionResult = null;

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('problem_id', problemId);
      formData.append('language', selectedLanguage);

      const response = await authService.authenticatedRequest(
        'http://localhost:5000/submission/submit',
        {
          method: 'POST',
          body: formData
        }
      );

      if (response.ok) {
        const data = await response.json();
        submissionId = data.submission_id;
        submissionResult = data;
        
        // Start polling for submission status
        await pollSubmissionStatus();
      } else {
        const errorData = await response.json();
        submissionError = errorData.message || 'Failed to submit solution';
      }
    } catch (err) {
      submissionError = 'Failed to submit solution';
      console.error('Error submitting solution:', err);
    } finally {
      submitting = false;
    }
  }

  async function pollSubmissionStatus() {
    if (!submissionId || polling) return;
    
    polling = true;
    const maxAttempts = 30; // 30 attempts with 2 second intervals = 1 minute max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await authService.authenticatedRequest(
          `http://localhost:5000/submission/status/${submissionId}`
        );
        
        if (response.ok) {
          const data = await response.json();
          submissionResult = { ...submissionResult, ...data };
          
          // Continue polling if status is still pending or judging
          if ((data.status === 'pending' || data.status === 'judging') && attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 2000);
          } else {
            polling = false;
          }
        } else {
          polling = false;
        }
      } catch (err) {
        console.error('Error polling submission status:', err);
        polling = false;
      }
    };

    setTimeout(poll, 2000);
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

  function downloadPDF() {
    if (pdfUrl) {
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = `problem_${problemId}.pdf`;
      link.click();
    }
  }

  function openPDFInNewTab() {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank');
    }
  }

  function goBackToContest() {
    goto(`/contest/${contestId}`);
  }

  function goBackToContests() {
    goto('/contests');
  }
</script>

<div class="contest-problem-container">
  {#if loading}
    <div class="loading">Loading problem...</div>
  {:else if error}
    <div class="error-message">{error}</div>
    <div class="navigation-buttons">
      <button class="btn btn-secondary" on:click={goBackToContest}>
        Back to Contest
      </button>
      <button class="btn btn-secondary" on:click={goBackToContests}>
        Back to Contests
      </button>
    </div>
  {:else if contest && problem}
    {@const contestStatus = getContestStatus(contest.start_time, contest.end_time)}
    
    <div class="header">
      <div class="navigation">
        <button class="btn btn-secondary" on:click={goBackToContest}>
          ← Back to Contest
        </button>
        <button class="btn btn-secondary" on:click={goBackToContests}>
          All Contests
        </button>
      </div>
      
      <div class="problem-info">
        <h1>Problem {problemId}</h1>
        <div class="contest-badge">
          <span class="contest-name">{contest.name}</span>
          <span class="status-badge {getStatusClass(contestStatus)}">
            {getStatusText(contestStatus)}
          </span>
        </div>
      </div>
    </div>

    <div class="content-layout">
      <!-- Problem Statement Column -->
      <div class="statement-column">
        <div class="statement-card">
          <div class="statement-header">
            <h2>Problem Statement</h2>
            <div class="statement-actions">
              {#if pdfUrl}
                <button class="btn btn-small btn-secondary" on:click={downloadPDF}>
                  Download PDF
                </button>
                <button class="btn btn-small btn-secondary" on:click={openPDFInNewTab}>
                  Open in New Tab
                </button>
              {/if}
            </div>
          </div>
          
          {#if pdfUrl}
            <div class="pdf-container">
              <iframe 
                src={pdfUrl} 
                title="Problem Statement"
                width="100%" 
                height="600"
              ></iframe>
            </div>
          {:else}
            <div class="no-statement">
              Problem statement not available
            </div>
          {/if}
        </div>
      </div>

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
            <div class="problem-meta">
              <div class="meta-item">
                <span class="meta-label">Time Limit:</span>
                <span class="meta-value">{problem.time_limit || 'N/A'}ms</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Memory Limit:</span>
                <span class="meta-value">{problem.memory_limit || 'N/A'}MB</span>
              </div>
            </div>

            <form on:submit|preventDefault={submitSolution} class="submission-form">
              <div class="form-group">
                <label for="language">Language:</label>
                <select id="language" bind:value={selectedLanguage} required>
                  <option value="cpp">C++</option>
                  <option value="python">Python</option>
                  <option value="java">Java</option>
                </select>
              </div>

              <div class="form-group">
                <label for="file">Solution File:</label>
                <input
                  id="file"
                  type="file"
                  accept=".cpp,.py,.java,.c,.cc,.cxx"
                  on:change={handleFileSelect}
                  required
                />
                {#if selectedFile}
                  <span class="file-info">Selected: {selectedFile.name}</span>
                {/if}
              </div>

              <button type="submit" class="btn btn-primary submit-btn" disabled={submitting || !selectedFile}>
                {submitting ? 'Submitting...' : 'Submit Solution'}
              </button>
            </form>

            {#if submissionError}
              <div class="error-message">{submissionError}</div>
            {/if}

            {#if submissionResult}
              <div class="submission-status">
                <h3>Submission Status</h3>
                <div class="status-info">
                  <div class="status-item">
                    <span class="status-label">Submission ID:</span>
                    <span class="status-value">{submissionResult.submission_id}</span>
                  </div>
                  <div class="status-item">
                    <span class="status-label">Status:</span>
                    <span class="status-value status-{submissionResult.status}">
                      {submissionResult.status || 'pending'}
                      {#if polling}(updating...){/if}
                    </span>
                  </div>
                  {#if submissionResult.verdict}
                    <div class="status-item">
                      <span class="status-label">Verdict:</span>
                      <span class="status-value verdict-{submissionResult.verdict}">
                        {submissionResult.verdict}
                      </span>
                    </div>
                  {/if}
                  {#if submissionResult.score !== undefined}
                    <div class="status-item">
                      <span class="status-label">Score:</span>
                      <span class="status-value">{submissionResult.score}%</span>
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .contest-problem-container {
    max-width: 1400px;
    margin: 1rem auto;
    padding: 0 1rem;
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

  .header {
    margin-bottom: 1.5rem;
  }

  .navigation {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .navigation-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }

  .problem-info h1 {
    font-family: 'Courier New', monospace;
    color: #64b5f6;
    margin: 0 0 0.5rem 0;
    font-size: 2rem;
  }

  .contest-badge {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .contest-name {
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    font-size: 1rem;
  }

  .status-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    font-family: 'Courier New', monospace;
  }

  .status-upcoming { background: #2196f3; color: white; }
  .status-active { background: #4caf50; color: white; }
  .status-ended { background: #757575; color: white; }

  .content-layout {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 1.5rem;
  }

  .statement-column {
    min-width: 0;
  }

  .statement-card, .submission-card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .statement-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .statement-header h2, .submission-card h2 {
    font-family: 'Courier New', monospace;
    color: #64b5f6;
    margin: 0;
    font-size: 1.4rem;
  }

  .statement-actions {
    display: flex;
    gap: 0.5rem;
  }

  .pdf-container {
    border: 1px solid #333;
    border-radius: 4px;
    overflow: hidden;
  }

  .no-statement {
    text-align: center;
    padding: 2rem;
    color: #888;
    font-family: 'Courier New', monospace;
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

  .problem-meta {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: #2d2d2d;
    border-radius: 4px;
  }

  .meta-item {
    display: flex;
    justify-content: space-between;
  }

  .meta-label {
    color: #888;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
  }

  .meta-value {
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    font-weight: 600;
  }

  .submission-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-group label {
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    font-weight: 500;
  }

  .form-group select, .form-group input {
    padding: 0.75rem;
    background: #2d2d2d;
    border: 1px solid #444;
    border-radius: 4px;
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
  }

  .form-group select:focus, .form-group input:focus {
    outline: none;
    border-color: #64b5f6;
    box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.2);
  }

  .file-info {
    color: #888;
    font-size: 0.85rem;
    font-family: 'Courier New', monospace;
  }

  .submit-btn {
    margin-top: 0.5rem;
  }

  .submission-status {
    margin-top: 1rem;
    padding: 1rem;
    background: #2d2d2d;
    border-radius: 4px;
  }

  .submission-status h3 {
    font-family: 'Courier New', monospace;
    color: #64b5f6;
    margin: 0 0 0.75rem 0;
    font-size: 1.1rem;
  }

  .status-info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .status-item {
    display: flex;
    justify-content: space-between;
  }

  .status-label {
    color: #888;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
  }

  .status-value {
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    font-weight: 600;
  }

  .status-pending { color: #ffa726; }
  .status-judging { color: #42a5f5; }
  .status-complete { color: #66bb6a; }
  .status-error { color: #ef5350; }

  .verdict-AC { color: #66bb6a; }
  .verdict-WA { color: #ef5350; }
  .verdict-TLE { color: #ff9800; }
  .verdict-RTE { color: #e91e63; }
  .verdict-CE { color: #9c27b0; }

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

  .btn-small {
    padding: 0.375rem 0.75rem;
    font-size: 0.85rem;
  }

  .btn-primary {
    background: #64b5f6;
    color: #000;
  }

  .btn-primary:hover:not(:disabled) {
    background: #42a5f5;
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

    .submission-column {
      order: -1;
    }
  }

  @media (max-width: 768px) {
    .navigation {
      flex-direction: column;
    }

    .contest-badge {
      flex-direction: column;
      align-items: flex-start;
    }

    .statement-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
  }
</style>