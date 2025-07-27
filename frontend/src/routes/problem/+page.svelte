<script lang="ts">
  import { onMount } from 'svelte';
  import type { PageData } from './$types';
  
  export let data: PageData;
  
  let problems: string[] = [];
  let selectedProblem = data.problemId;
  let pdfUrl = '';
  let loading = false;
  let error = '';

  onMount(async () => {
    await loadProblems();
    if (selectedProblem) {
      loadProblemStatement();
    }
  });

  async function loadProblems() {
    try {
      const res = await fetch("http://localhost:5000/general/problems");
      const data = await res.json();
      problems = data.problems || [];
      if (problems.length > 0 && !selectedProblem) {
        selectedProblem = problems[0];
      }
    } catch (err) {
      error = "Failed to fetch problems: " + err;
    }
  }

  async function loadProblemStatement() {
    if (!selectedProblem) return;
    
    loading = true;
    error = '';
    
    try {
      // First check if the PDF exists by making a HEAD request with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(`http://localhost:5000/general/problem/${selectedProblem}/statement`, {
        method: 'HEAD',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // If the PDF exists, set the URL for the iframe
      pdfUrl = `http://localhost:5000/general/problem/${selectedProblem}/statement`;
      loading = false;
    } catch (err) {
      loading = false;
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      
      if (err instanceof Error && err.name === 'AbortError') {
        error = 'Request timed out. The server might be slow or unavailable.';
      } else {
        error = `Failed to load PDF: ${errorMessage}. Please check if the problem statement exists.`;
      }
    }
  }

  function downloadPDF() {
    if (!selectedProblem) return;
    
    const link = document.createElement('a');
    link.href = `http://localhost:5000/general/problem/${selectedProblem}/statement`;
    link.download = `problem_${selectedProblem}_statement.pdf`;
    link.click();
  }

  function openInNewTab() {
    if (!selectedProblem) return;
    
    window.open(`http://localhost:5000/general/problem/${selectedProblem}/statement`, '_blank');
  }
</script>

<svelte:head>
  <title>Problem Statement Viewer - Mini-Competition</title>
</svelte:head>

<main>
  <div class="header">
    <h1>📄 Problem Statement Viewer</h1>
    <div class="controls">
      <button class="btn btn-secondary" on:click={downloadPDF} disabled={!selectedProblem}>
        📥 Download PDF
      </button>
      <button class="btn btn-primary" on:click={openInNewTab} disabled={!selectedProblem}>
        🔗 Open in New Tab
      </button>
    </div>
  </div>

  <div class="problem-selector">
    <label for="problemSelect">Select Problem:</label>
    <select 
      id="problemSelect" 
      bind:value={selectedProblem} 
      on:change={loadProblemStatement}
    >
      {#each problems as problem}
        <option value={problem}>Problem {problem}</option>
      {/each}
    </select>
  </div>

  {#if error}
    <div class="error">
      {error}
    </div>
  {/if}

  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading problem statement...</p>
    </div>
  {/if}

  {#if selectedProblem && !loading}
    <div class="pdf-container">
      <iframe 
        src={pdfUrl} 
        title="Problem Statement PDF"
        class="pdf-viewer"
      ></iframe>
    </div>
  {:else if !loading && !error}
    <div class="no-problem">
      <p>Please select a problem to view its statement.</p>
    </div>
  {/if}
</main>

<style>
  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }

  .header {
    background: #2c3e50;
    color: white;
    padding: 2rem;
    border-radius: 8px 8px 0 0;
    margin: -2rem -2rem 2rem -2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .header h1 {
    margin: 0;
    font-size: 2rem;
  }

  .controls {
    display: flex;
    gap: 1rem;
  }

  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
    transition: all 0.2s;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: #3498db;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #2980b9;
  }

  .btn-secondary {
    background: #95a5a6;
    color: white;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #7f8c8d;
  }

  .problem-selector {
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
  }

  .problem-selector label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: #495057;
  }

  .problem-selector select {
    padding: 0.75rem;
    border: 1px solid #ced4da;
    border-radius: 6px;
    font-size: 1rem;
    min-width: 200px;
    background: white;
  }

  .pdf-container {
    height: 70vh;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    overflow: hidden;
  }

  .pdf-viewer {
    width: 100%;
    height: 100%;
    border: none;
  }

  .loading {
    text-align: center;
    padding: 3rem;
    color: #6c757d;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error {
    background: #f8d7da;
    color: #721c24;
    padding: 1rem;
    border-radius: 6px;
    border: 1px solid #f5c6cb;
    margin-bottom: 1rem;
  }

  .no-problem {
    text-align: center;
    padding: 3rem;
    color: #6c757d;
    font-size: 1.1rem;
  }

  @media (max-width: 768px) {
    .header {
      flex-direction: column;
      text-align: center;
    }

    .controls {
      justify-content: center;
    }

    .pdf-container {
      height: 50vh;
    }
  }
</style> 