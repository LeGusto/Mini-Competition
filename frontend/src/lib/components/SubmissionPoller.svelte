<script lang="ts">
  import { API_BASE_URL } from '$lib/config';
  import { authService } from '$lib/services/auth';
  import { onMount } from 'svelte';

  export let submissionId: string | null = null;
  export let polling: boolean = false;
  export let onStatusUpdate: ((data: any) => void) | undefined = undefined;
  export let onPollingComplete: (() => void) | undefined = undefined;

  let maxAttempts = 10; 
  let attempts = 0;
  let pollInterval = 2000; 
  let isPolling = false; 

  // Start polling when submissionId changes and polling is enabled
  $: if (submissionId && polling && !isPolling) {
    startPolling();
  }

  function startPolling() {
    if (!submissionId || isPolling) return;

    isPolling = true;
    attempts = 0;
    setTimeout(poll, pollInterval);
  }

  async function poll() {
    attempts++;

    try {
      const response = await authService.authenticatedRequest(
        `${API_BASE_URL}/submission/status/${submissionId}`
      );

      if (response.ok) {
        const data = await response.json();
        onStatusUpdate?.(data);

        // Continue polling if status is still in progress
        const inProgressStatuses = ['pending', 'queued', 'processing'];
        if (inProgressStatuses.includes(data.status) && attempts < maxAttempts) {
          setTimeout(poll, pollInterval);
        } else {
          // Stop polling - either got final result or timed out
          isPolling = false;
          polling = false;
          onPollingComplete?.();
        }
      } else {
        // API error - stop polling
        isPolling = false;
        polling = false;
        onPollingComplete?.();
      }
    } catch (err) {
      console.error('Error polling submission status:', err);
      isPolling = false;
      polling = false;
      onPollingComplete?.();
    }
  }

  // Stop polling
  export function stopPolling() {
    isPolling = false;
    polling = false;
  }

  // Reset polling state
  export function reset() {
    isPolling = false;
    polling = false;
    attempts = 0;
  }
</script>

<!-- This component is purely functional, no UI -->
