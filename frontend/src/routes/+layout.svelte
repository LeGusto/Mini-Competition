<script lang="ts">
    import { page } from '$app/stores';
    import { authStore } from '$lib/stores/auth';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte'; 

    // Check if we're on the login page
    $: isLoginPage = $page.url.pathname === '/login';

    if (!isLoginPage) {
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
    }
  </script>
  
  {#if !isLoginPage}
    <nav class="navbar">
      <div class="nav-container">
        <div class="nav-links">
          <a href="/problems">Problems</a>
          <a href="/submissions">Submissions</a>
          <a href="/contests">Contests</a>
        </div>
        <div class="nav-user">
          <span class="username">{$authStore.user?.username}</span>
          <button on:click={() => {authStore.logout(); goto('/login')}}>Logout</button>
        </div>
      </div>
    </nav>
  {/if}

  
  
  <main>
    
    <slot />
  </main>