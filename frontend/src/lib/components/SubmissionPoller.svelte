<script lang="ts">
  import { authService } from '$lib/services/auth';
  import { onMount } from 'svelte';

  export let submissionId: string | null = null;
  export let polling: boolean = false;
  export let onStatusUpdate: ((data: any) => void) | undefined = undefined;
  export let onPollingComplete: (() => void) | undefined = undefined;

  let maxAttempts = 30; // 30 attempts with 2 second intervals = 1 minute max
  let attempts = 0;

  // Start polling when submissionId changes
  $: if (submissionId && !polling) {
    startPolling();
  }

  function startPolling() {
    if (!submissionId || polling) return;

    polling = true;
    attempts = 0;
    setTimeout(poll, 2000);
  }

  async function poll() {
    try {
      const response = await authService.authenticatedRequest(
        `http://localhost:5000/submission/status/${submissionId}`
      );

      if (response.ok) {
        const data = await response.json();
        onStatusUpdate?.(data);

        // Continue polling if status is still pending or judging
        if ((data.status === 'pending' || data.status === 'judging') && attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        } else {
          polling = false;
          onPollingComplete?.();
        }
      } else {
        polling = false;
        onPollingComplete?.();
      }
    } catch (err) {
      console.error('Error polling submission status:', err);
      polling = false;
      onPollingComplete?.();
    }
  }

  // Stop polling
  export function stopPolling() {
    polling = false;
  }

  // Reset polling state
  export function reset() {
    polling = false;
    attempts = 0;
  }
</script>

<!-- This component is purely functional, no UI -->
