<script lang="ts">
  import { API_BASE_URL } from '$lib/config';
  import { goto } from '$app/navigation';
  import { authService } from '$lib/services/auth';
  import { authStore } from '$lib/stores/auth';
  import { onMount } from 'svelte';

  let name = '';
  let description = '';
  let startDate = '';
  let startTime = '';
  let endDate = '';
  let endTime = '';
  let problemIds = '';
  let loading = false;
  let error = '';
  let availableProblems: any[] = [];
  let validationErrors: string[] = [];
  let fieldErrors: { [key: string]: boolean } = {};

  onMount(async () => {
    // Check if user is admin, redirect if not
    if ($authStore.user?.role !== 'admin') {
      goto('/contests');
      return;
    }

    // Load available problems
    try {
      const response = await authService.authenticatedRequest(`${API_BASE_URL}/general/problems`);
      const data = await response.json();
      availableProblems = data.problems || [];
    } catch (err) {
      console.error('Failed to load problems:', err);
    }
  });

  function validateContest(): boolean {
    validationErrors = [];
    fieldErrors = {};
    console.log('Validating contest...', { name, startDate, startTime, endDate, endTime, problemIds });
    
    // Check required fields
    if (!name || !startDate || !startTime || !endDate || !endTime) {
      validationErrors.push('Please fill in all required fields');
      if (!name) fieldErrors.name = true;
      if (!startDate) fieldErrors.startDate = true;
      if (!startTime) fieldErrors.startTime = true;
      if (!endDate) fieldErrors.endDate = true;
      if (!endTime) fieldErrors.endTime = true;
      console.log('Missing required fields');
      return false;
    }

    // Validate start time is after current time
    const now = new Date();
    const startDateTime = new Date(`${startDate}T${startTime}`);
    console.log('Start time validation:', { now: now.toISOString(), startDateTime: startDateTime.toISOString() });
    
    if (startDateTime <= now) {
      validationErrors.push('Start time must be after the current time');
      fieldErrors.startDate = true;
      fieldErrors.startTime = true;
      console.log('Start time is in the past');
    }

    // Validate end time is after start time
    const endDateTime = new Date(`${endDate}T${endTime}`);
    console.log('End time validation:', { startDateTime: startDateTime.toISOString(), endDateTime: endDateTime.toISOString() });
    
    if (endDateTime <= startDateTime) {
      validationErrors.push('End time must be after start time');
      fieldErrors.endDate = true;
      fieldErrors.endTime = true;
      console.log('End time is before start time');
    }

    // Validate problem IDs exist
    if (problemIds.trim()) {
      const inputProblemIds = problemIds.split(',').map(id => id.trim()).filter(id => id);
      
      // Remove duplicates
      const uniqueProblemIds = [...new Set(inputProblemIds)];
      
      if (uniqueProblemIds.length !== inputProblemIds.length) {
        problemIds = uniqueProblemIds.join(', ');
      }
      
      const availableProblemIds = availableProblems.map(p => p.id.toString());
      console.log('Problem ID validation:', { inputProblemIds, uniqueProblemIds, availableProblemIds });
      
      for (const problemId of uniqueProblemIds) {
        if (!availableProblemIds.includes(problemId)) {
          validationErrors.push(`Problem ID "${problemId}" does not exist`);
          fieldErrors.problemIds = true;
          console.log(`Problem ID ${problemId} does not exist`);
        }
      }
    }

    console.log('Validation result:', { isValid: validationErrors.length === 0, errors: validationErrors, fieldErrors });
    return validationErrors.length === 0;
  }

  async function createContest() {
    // Clear previous errors
    error = '';
    validationErrors = [];
    hasBeenSubmitted = true;

    // Validate the form
    if (!validateContest()) {
      return;
    }

    loading = true;

    try {
      // Combine date and time into ISO format
      const startDateTime = new Date(`${startDate}T${startTime}`).toISOString();
      const endDateTime = new Date(`${endDate}T${endTime}`).toISOString();

      // Parse problem IDs (comma-separated) and remove duplicates
      const problems = [...new Set(problemIds.split(',').map(id => id.trim()).filter(id => id))];

      const response = await authService.authenticatedRequest(`${API_BASE_URL}/contest`, {
        method: 'POST',
        body: JSON.stringify({
          name,
          description,
          start_time: startDateTime,
          end_time: endDateTime,
          problems
        })
      });

      if (response.ok) {
        goto('/contests');
      } else {
        const errorData = await response.json();
        error = errorData.message || 'Failed to create contest';
      }
    } catch (err) {
      error = 'Failed to create contest';
      console.error('Error creating contest:', err);
    } finally {
      loading = false;
    }
  }

  function handleCancel() {
    goto('/contests');
  }

  // Clear validation errors when user starts typing (but only after first submission attempt)
  let hasBeenSubmitted = false;
  
  function clearValidationErrors() {
    if (hasBeenSubmitted && validationErrors.length > 0) {
      validationErrors = [];
      fieldErrors = {};
    }
  }

</script>

<div class="create-contest-container">
  <div class="form-card">
    <h1>Create New Contest</h1>
    
    <form on:submit|preventDefault={createContest}>
      <div class="form-group">
        <label for="name">Contest Name *</label>
        <input
          id="name"
          type="text"
          bind:value={name}
          placeholder="Weekly Contest #1"
          on:input={clearValidationErrors}
          class:error={fieldErrors.name}
          required
        />
      </div>

      <div class="form-group">
        <label for="description">Description</label>
        <textarea
          id="description"
          bind:value={description}
          placeholder="Contest description..."
          rows="3"
        ></textarea>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="start-date">Start Date *</label>
          <input
            id="start-date"
            type="date"
            bind:value={startDate}
            on:input={clearValidationErrors}
            class:error={fieldErrors.startDate}
            required
          />
        </div>
        <div class="form-group">
          <label for="start-time">Start Time *</label>
          <input
            id="start-time"
            type="time"
            bind:value={startTime}
            on:input={clearValidationErrors}
            class:error={fieldErrors.startTime}
            required
          />
        </div>
      </div>
              <div class="timezone-info">
          <small>All times are in your local timezone: <strong>{$authStore.user?.timezone}</strong></small>
        </div>

      <div class="form-row">
        <div class="form-group">
          <label for="end-date">End Date *</label>
          <input
            id="end-date"
            type="date"
            bind:value={endDate}
            on:input={clearValidationErrors}
            class:error={fieldErrors.endDate}
            required
          />
        </div>
        <div class="form-group">
          <label for="end-time">End Time *</label>
          <input
            id="end-time"
            type="time"
            bind:value={endTime}
            on:input={clearValidationErrors}
            class:error={fieldErrors.endTime}
            required
          />
        </div>
      </div>

      <div class="form-group">
        <label for="problems">Problem IDs</label>
        <input
          id="problems"
          type="text"
          bind:value={problemIds}
          placeholder="1, 2, 3"
          on:input={clearValidationErrors}
          class:error={fieldErrors.problemIds}
        />
        <small class="form-help">
          Enter problem IDs separated by commas (e.g., 1, 2, 3)
        </small>
        {#if availableProblems.length > 0}
          <div class="available-problems">
            <strong>Available Problems:</strong>
            {availableProblems.map(p => p.id).join(', ')}
          </div>
        {/if}
      </div>

      <div class="form-actions">
        <button type="button" class="btn btn-secondary" on:click={handleCancel}>
          Cancel
        </button>
        <button type="submit" class="btn btn-primary" disabled={loading}>
          {loading ? 'Creating...' : 'Create Contest'}
        </button>
      </div>
    </form>

    {#if error}
      <div class="error-message">{error}</div>
    {/if}

    {#if validationErrors.length > 0}
      <div class="validation-errors">
        <strong>Please fix the following errors:</strong>
        <ul>
          {#each validationErrors as validationError}
            <li>{validationError}</li>
          {/each}
        </ul>
      </div>
    {/if}
  </div>
</div>

<style>
  .create-contest-container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 0 1rem;
  }

  .form-card {
    background: #3a3a3a;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 2rem;
  }

  h1 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin-bottom: 1.5rem;
    font-size: 1.8rem;
  }

  .error-message {
    background: #4a4a4a;
    color: #ff6b6b;
    padding: 0.75rem;
    border-radius: 4px;
    margin-top: 1rem;
    font-family: 'Courier New', monospace;
    border: 1px solid #666;
  }

  .validation-errors {
    background: #4a4a4a;
    color: #ff6b6b;
    padding: 0.75rem;
    border-radius: 4px;
    margin-top: 1rem;
    font-family: 'Courier New', monospace;
    border: 1px solid #666;
  }

  .validation-errors strong {
    display: block;
    margin-bottom: 0.5rem;
    color: #ff6b6b;
  }

  .validation-errors ul {
    margin: 0;
    padding-left: 1.5rem;
  }

  .validation-errors li {
    margin-bottom: 0.25rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .timezone-info {
    text-align: center;
    margin: 0.5rem 0 1rem 0;
    padding: 0.5rem;
    background: #4a4a4a;
    border-radius: 4px;
    border: 1px solid #666;
  }

  .timezone-info small {
    color: #aaa;
    font-family: 'Courier New', monospace;
  }

  .timezone-info strong {
    color: #f5f5f5;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    color: #cccccc;
    font-weight: 500;
    font-family: 'Courier New', monospace;
  }

  input, textarea {
    width: 100%;
    padding: 0.75rem;
    background: #4a4a4a;
    border: 1px solid #666;
    border-radius: 4px;
    color: #f5f5f5;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
  }

  input:focus, textarea:focus {
    outline: none;
    border-color: #888;
    box-shadow: 0 0 0 2px rgba(136, 136, 136, 0.3);
  }

  input.error, textarea.error {
    border-color: #ff6b6b !important;
    box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.3) !important;
  }

  input.error:focus, textarea.error:focus {
    border-color: #ff6b6b !important;
    box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.5) !important;
  }

  .form-help {
    display: block;
    margin-top: 0.25rem;
    color: #aaa;
    font-size: 0.8rem;
    font-family: 'Courier New', monospace;
  }

  .available-problems {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: #4a4a4a;
    border-radius: 4px;
    font-size: 0.85rem;
    color: #cccccc;
    font-family: 'Courier New', monospace;
    border: 1px solid #666;
  }

  .form-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 2rem;
  }

  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
  }

  .btn:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .btn-secondary {
    background: #666;
    color: #f5f5f5;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #777;
  }

  .btn-primary {
    background: #888;
    color: #f5f5f5;
  }

  .btn-primary:hover:not(:disabled) {
    background: #999;
  }

  @media (max-width: 768px) {
    .form-row {
      grid-template-columns: 1fr;
    }
    
    .form-actions {
      flex-direction: column;
    }
  }
</style>