<script lang="ts">
  export let problem: any;
  export let timeUnit: string = 's'; // 's' for seconds, 'ms' for milliseconds
</script>

{#if problem}
  <div class="problem-meta">
    <div class="meta-item">
      <span class="meta-label">Time Limit:</span>
      <span class="meta-value">{problem.time_limit || 'N/A'}{timeUnit}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Memory Limit:</span>
      <span class="meta-value">{problem.memory_limit || 'N/A'}MB</span>
    </div>
  </div>
{/if}

<style>
  .problem-meta {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: #2d2d2d;
    border-radius: 4px;
  }

  .meta-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .meta-label {
    color: #888;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    text-align: left;
  }

  .meta-value {
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    font-weight: 600;
    text-align: center;
  }
</style>
