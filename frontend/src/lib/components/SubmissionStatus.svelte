<script lang="ts">
  export let submissionResult: any = null;
  export let polling = false;

  // Function to get status color class
  function getStatusClass(status: string) {
    switch (status) {
      case 'pending': return 'status-pending';
      case 'queued': return 'status-queued';
      case 'processing': return 'status-processing';
      case 'completed': return 'status-completed';
      case 'accepted': return 'status-accepted';
      case 'wrong_answer': return 'status-wrong-answer';
      case 'error': return 'status-error';
      default: return '';
    }
  }

  // Function to get verdict color class
  function getVerdictClass(verdict: string) {
    switch (verdict) {
      case 'AC': return 'verdict-AC';
      case 'WA': return 'verdict-WA';
      case 'TLE': return 'verdict-TLE';
      case 'RTE': return 'verdict-RTE';
      case 'CE': return 'verdict-CE';
      default: return '';
    }
  }
</script>

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
        <span class="status-value {getStatusClass(submissionResult.status)}">
          {submissionResult.status || 'queued'}
        </span>
      </div>
      {#if submissionResult.verdict}
        <div class="status-item">
          <span class="status-label">Verdict:</span>
          <span class="status-value {getVerdictClass(submissionResult.verdict)}">
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

<style>
  .submission-status {
    margin-top: 0.75rem;
    padding: 0.75rem;
    background: #2d2d2d;
    border-radius: 4px;
  }

  .submission-status h3 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0 0 0.75rem 0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .status-info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .status-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .status-label {
    color: #888;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    text-align: left;
  }

  .status-value {
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    font-weight: 600;
    text-align: center;
  }

  .status-pending { color: #ffa726; }
  .status-queued { color: #ffa726; }
  .status-processing { color: #ffb74d; }
  .status-completed { color: #66bb6a; }
  .status-accepted { color: #66bb6a; }
  .status-wrong-answer { color: #ef5350; }
  .status-error { color: #ef5350; }

  .verdict-AC { color: #66bb6a; }
  .verdict-WA { color: #ef5350; }
  .verdict-TLE { color: #ff9800; }
  .verdict-RTE { color: #e91e63; }
  .verdict-CE { color: #9c27b0; }
</style>
