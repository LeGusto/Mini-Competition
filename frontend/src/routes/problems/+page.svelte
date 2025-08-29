<script lang="ts">
  import { onMount } from 'svelte';
  import { authService } from '$lib/services/auth';
  import { goto } from '$app/navigation';

  interface Problem {
    id: string;
    time_limit?: string;
    memory_limit?: string;
    tests?: string;
  }

  let problems: Problem[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    await loadProblems();
  });

  async function loadProblems() {
    try {
      loading = true;
      error = null;
      
      const response = await authService.authenticatedRequest('http://localhost:5000/general/problems');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      // The /general/problems endpoint already includes metadata (time_limit, memory_limit, tests)
      problems = data.problems || [];
      
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load problems';
    } finally {
      loading = false;
    }
  }

  function viewProblem(problemId: string) {
    goto(`/problem/${problemId}`);
  }
</script>

<svelte:head>
  <title>Problems - Mini-Competition</title>
</svelte:head>

<div class="problems-container">
  <div class="header">
    <h1>Problems</h1>
    <p>Select a problem to view details and submit solutions</p>
  </div>

  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading problems...</p>
    </div>
  {:else if error}
    <div class="error">
      <p>{error}</p>
      <button on:click={loadProblems}>Try Again</button>
    </div>
  {:else if problems.length === 0}
    <div class="empty-state">
      <p>No problems available at the moment.</p>
    </div>
  {:else}
    <div class="table-container">
      <table class="problems-table">
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
            <tr class="problem-row">
              <td class="problem-id">
                <span class="id-badge">#{problem.id}</span>
              </td>
              <td class="time-limit">
                {problem.time_limit || 'N/A'}s
              </td>
              <td class="memory-limit">
                {problem.memory_limit || 'N/A'}MB
              </td>
              <td class="actions">
                <button 
                  class="view-btn"
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
    margin: 0 auto;
    padding: 2rem;
  }

  .header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .header h1 {
    font-size: 2.5rem;
    font-weight: 500;
    color: #f5f5f5;
    margin-bottom: 0.5rem;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  }

  .header p {
    color: #cccccc;
    font-size: 1.125rem;
  }

  .loading, .error, .empty-state {
    text-align: center;
    padding: 4rem 2rem;
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

  .error {
    color: #ff6b6b;
  }

  .error button {
    margin-top: 1rem;
    background: #666;
    color: #f5f5f5;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  }

  .error button:hover {
    background: #777;
  }

  .table-container {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 12px;
    overflow: hidden;
  }

  .problems-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  }

  .problems-table th {
    background: #4a4a4a;
    color: #f5f5f5;
    font-weight: 600;
    text-align: left;
    padding: 1rem 1.5rem;
    border-bottom: 2px solid #666;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .problems-table td {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #555;
    vertical-align: middle;
    color: #cccccc;
  }

  .problem-row:hover {
    background: #454545;
  }

  .problem-id {
    font-weight: 600;
  }

  .id-badge {
    background: #666;
    color: #f5f5f5;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .time-limit, .memory-limit, .test-cases {
    color: #aaa;
    font-weight: 500;
  }

  .actions {
    text-align: center;
  }

  .view-btn {
    background: #666;
    color: #f5f5f5;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.15s ease;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
    font-weight: 500;
  }

  .view-btn:hover {
    background: #777;
    transform: translateY(-1px);
  }

  .view-btn:active {
    transform: translateY(0);
  }

  @media (max-width: 768px) {
    .problems-container {
      padding: 1rem;
    }

    .header h1 {
      font-size: 2rem;
    }

    .table-container {
      overflow-x: auto;
    }

    .problems-table th,
    .problems-table td {
      padding: 0.75rem 1rem;
      font-size: 0.875rem;
    }

    .view-btn {
      padding: 0.5rem 0.75rem;
      font-size: 0.75rem;
    }
  }
</style>
