<script lang="ts">
  import { API_BASE_URL } from '$lib/config';
  import { authService } from '$lib/services/auth';

  export let problemId: string;
  export let disabled = false;
  export let onSubmissionStart: (() => void) | undefined = undefined;
  export let onSubmissionComplete: ((result: any) => void) | undefined = undefined;
  export let onSubmissionError: ((error: string) => void) | undefined = undefined;

  let selectedFile: File | null = null;
  let selectedLanguage = 'cpp';
  let submitting = false;
  let submissionError = '';
  let fileInput: HTMLInputElement;

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      selectedFile = target.files[0];
      submissionError = '';
    }
  }

  async function submitSolution() {
    if (!selectedFile) {
      submissionError = 'Please select a file';
      onSubmissionError?.(submissionError);
      return;
    }

    try {
      submitting = true;
      submissionError = '';
      onSubmissionStart?.();

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('problem_id', problemId);
      formData.append('language', selectedLanguage);

      const response = await authService.authenticatedRequest(
        `${API_BASE_URL}/submission/submit`,
        {
          method: 'POST',
          body: formData
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Clear the file input after successful submission
        selectedFile = null;
        if (fileInput) {
          fileInput.value = '';
        }
        
        onSubmissionComplete?.(data);
      } else {
        const errorData = await response.json();
        submissionError = errorData.message || 'Failed to submit solution';
        onSubmissionError?.(submissionError);
      }
    } catch (err) {
      submissionError = 'Failed to submit solution';
      onSubmissionError?.(submissionError);
      console.error('Error submitting solution:', err);
    } finally {
      submitting = false;
    }
  }

  // Reset form
  export function reset() {
    selectedFile = null;
    selectedLanguage = 'cpp';
    submissionError = '';
    submitting = false;
    
    // Clear the file input element
    if (fileInput) {
      fileInput.value = '';
    }
  }
</script>

<div class="submission-form">
  <form on:submit|preventDefault={submitSolution} class="form">
    <div class="form-group">
      <label for="language">Language:</label>
      <select
        id="language"
        bind:value={selectedLanguage}
        required
        disabled={disabled || submitting}
      >
        <option value="cpp">C++</option>
        <option value="python">Python</option>
        <option value="java">Java</option>
      </select>
    </div>

    <div class="form-group">
      <label for="file">Solution File:</label>
      <input
        bind:this={fileInput}
        id="file"
        type="file"
        accept=".cpp,.py,.java,.c,.cc,.cxx"
        on:change={handleFileSelect}
        required
        disabled={disabled || submitting}
      />
      {#if selectedFile}
        <span class="file-info">Selected: {selectedFile.name}</span>
      {/if}
    </div>

    <button
      type="submit"
      class="btn btn-primary submit-btn"
      disabled={submitting || !selectedFile || disabled}
    >
      {submitting ? 'Submitting...' : 'Submit Solution'}
    </button>
  </form>

  {#if submissionError}
    <div class="error-message">{submissionError}</div>
  {/if}
</div>

<style>
  .submission-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .form {
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
    border-color: #888;
    box-shadow: 0 0 0 2px rgba(136, 136, 136, 0.3);
  }

  .form-group select:disabled, .form-group input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .file-info {
    color: #888;
    font-size: 0.85rem;
    font-family: 'Courier New', monospace;
  }

  .submit-btn {
    margin-top: 0.5rem;
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
</style>
