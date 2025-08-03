<script lang="ts">
  import { authService } from '$lib/services/auth';
  import { goto } from '$app/navigation';
  
  let username = '';
  let password = '';
  let loading = false;
  let error = '';

  async function handleLogin() {
    loading = true;
    error = '';
    
    const result = await authService.login({ username, password });
    
    if (result.success) {
      await goto('/');
    } else {
      error = result.error || 'Login failed';
    }
    
    loading = false;
  }

  async function handleRegister() {
    loading = true;
    error = '';
    
    const result = await authService.register({ username, password});
    
    if (result.success) {
      await goto('/');
    } else {
      error = result.error || 'Registration failed';
    }
    
    loading = false;
  }
</script>

<main>
    <h1>Login</h1>
    <form on:submit|preventDefault={handleLogin}>
        <input type="text" bind:value={username} placeholder="Username" required />
        <input type="password" bind:value={password} placeholder="Password" required />
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
    </form>
    {#if error}
      <p class="error">{error}</p>
    {/if}

    <h1>Register</h1>
    <form on:submit|preventDefault={handleRegister}>
        <input type="text" bind:value={username} placeholder="Username" required />
        <input type="password" bind:value={password} placeholder="Password" required />
        <button type="submit" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
    </form>
    {#if error}
      <p class="error">{error}</p>
    {/if}
</main>