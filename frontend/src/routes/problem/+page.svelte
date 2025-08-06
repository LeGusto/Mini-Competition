<script lang="ts">
  import { onMount } from 'svelte';
  import type { PageData } from './$types';
  import { authStore } from '$lib/stores/auth';
  import { authService } from '$lib/services/auth';
  export let data: PageData;
  
  let problems: string[] = [];
  let selectedProblem = data.problemId;
  let pdfUrl = '';
  let loading = false;
  let error = '';

  // Submission variables
  let selectedFile: File | null = null;
  let selectedLanguage = 'cpp';
  let submitting = false;
  let submissionResult: any = null;
  let submissionError = '';

  const languages = [
    { value: 'cpp', label: 'C++' },
    { value: 'python', label: 'Python' }
  ];

  onMount(async () => {
    await loadProblems();
    if (selectedProblem) {
      loadProblemStatement();
    }
  });

  async function loadProblems() {
    try {
      // Use authenticated request
      const response = await authService.authenticatedRequest("http://localhost:5000/general/problems");
      const data = await response.json();
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
      // Use authenticated request for problem statement
      const response = await authService.authenticatedRequest(
        `http://localhost:5000/general/problem/${selectedProblem}/statement`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Create a blob URL from the response
      const blob = await response.blob();
      pdfUrl = URL.createObjectURL(blob);
      loading = false;
    } catch (err) {
      loading = false;
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      error = `Failed to load PDF: ${errorMessage}. Please check if the problem statement exists.`;
    }
  }

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      selectedFile = target.files[0];
    }
  }

  async function submitSolution() {
    if (!selectedFile || !selectedProblem) {
      submissionError = 'Please select a file and problem.';
      return;
    }

    submitting = true;
    submissionError = '';
    submissionResult = null;

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('problem_id', selectedProblem);
      formData.append('language', selectedLanguage);

      const response = await authService.authenticatedRequest(
        'http://localhost:5000/submission/submit',
        {
          method: 'POST',
          body: formData
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }

      submissionResult = await response.json();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      submissionError = `Failed to submit solution: ${errorMessage}`;
    } finally {
      submitting = false;
    }
  }

  async function downloadPDF() {
    if (!selectedProblem) return;
    
    try {
      const response = await authService.authenticatedRequest(
        `http://localhost:5000/general/problem/${selectedProblem}/statement`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `problem_${selectedProblem}_statement.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      error = `Failed to download PDF: ${errorMessage}`;
    }
  }

  async function openInNewTab() {
    if (!selectedProblem) return;
    
    try {
      const response = await authService.authenticatedRequest(
        `http://localhost:5000/general/problem/${selectedProblem}/statement`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      // Note: We can't revoke the URL here as it's used in a new tab
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      error = `Failed to open PDF: ${errorMessage}`;
    }
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

    <!-- Submission Section -->
    <div class="submission-section">
      <h2>📤 Submit Solution</h2>
      
      <div class="submission-form">
        <div class="form-group">
          <label for="languageSelect">Language:</label>
          <select id="languageSelect" bind:value={selectedLanguage}>
            {#each languages as lang}
              <option value={lang.value}>{lang.label}</option>
            {/each}
          </select>
        </div>

        <div class="form-group">
          <label for="fileInput">Solution File:</label>
          <input 
            type="file" 
            id="fileInput" 
            accept=".cpp,.py,.c,.java"
            on:change={handleFileSelect}
          />
          {#if selectedFile}
            <span class="file-info">Selected: {selectedFile.name}</span>
          {/if}
        </div>

        <button 
          class="btn btn-success" 
          on:click={submitSolution}
          disabled={!selectedFile || submitting}
        >
          {submitting ? 'Submitting...' : 'Submit Solution'}
        </button>
      </div>

      {#if submissionError}
        <div class="error">
          {submissionError}
        </div>
      {/if}

      {#if submissionResult}
        <div class="success">
          <h3>Submission Result:</h3>
          <pre>{JSON.stringify(submissionResult, null, 2)}</pre>
        </div>
      {/if}
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

  .btn-success {
    background: #27ae60;
    color: white;
  }

  .btn-success:hover:not(:disabled) {
    background: #229954;
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
    margin-bottom: 2rem;
  }

  .pdf-viewer {
    width: 100%;
    height: 100%;
    border: none;
  }

  .submission-section {
    background: #f8f9fa;
    padding: 2rem;
    border-radius: 8px;
    border: 1px solid #e9ecef;
  }

  .submission-section h2 {
    margin: 0 0 1.5rem 0;
    color: #2c3e50;
  }

  .submission-form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-group label {
    font-weight: 600;
    color: #495057;
  }

  .form-group select,
  .form-group input[type="file"] {
    padding: 0.75rem;
    border: 1px solid #ced4da;
    border-radius: 6px;
    font-size: 1rem;
    background: white;
  }

  .file-info {
    font-size: 0.9rem;
    color: #6c757d;
    font-style: italic;
  }

  .success {
    background: #d4edda;
    color: #155724;
    padding: 1rem;
    border-radius: 6px;
    border: 1px solid #c3e6cb;
    margin-top: 1rem;
  }

  .success pre {
    background: white;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    margin: 0;
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

    .submission-form {
      gap: 1rem;
    }
  }
</style> 