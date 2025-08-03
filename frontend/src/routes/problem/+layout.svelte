<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';

  onMount(() => {
    // Initialize auth state
    authStore.init();
    
    // Check authentication
    const unsubscribe = authStore.subscribe(state => {
      if (!state.loading && !state.isAuthenticated) {
        goto('/login');
      }
    });

    return unsubscribe;
  });
</script>

<slot /> 