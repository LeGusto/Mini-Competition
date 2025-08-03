<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';

  onMount(() => {
    // Initialize auth state from localStorage
    authStore.init();
    
    // Check if user is authenticated
    const unsubscribe = authStore.subscribe(state => {
      if (!state.loading) {
        if (!state.isAuthenticated) {
          // Redirect to login if not authenticated
          goto('/login');
        }
      }
    });

    // Cleanup subscription
    return unsubscribe;
  });
</script>

<main>
  <h1>Welcome to Mini-Competition</h1>
  <p>You are successfully logged in!</p>
  <a href="/problem">View Problems</a>
  <button on:click={() => authStore.logout()}>Logout</button>
</main>

