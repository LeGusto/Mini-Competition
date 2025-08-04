<script lang="ts">
  import { authService } from '$lib/services/auth';
  import { goto } from '$app/navigation';
  
  // Login form variables
  let loginUsername = '';
  let loginPassword = '';
  
  // Register form variables
  let registerUsername = '';
  let registerPassword = '';
  
  let loading = false;
  let error = '';

  async function handleLogin() {
    loading = true;
    error = '';
    
    const result = await authService.login({ username: loginUsername, password: loginPassword });
    
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
    
    const result = await authService.register({ username: registerUsername, password: registerPassword });
    
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
        <input type="text" bind:value={loginUsername} placeholder="Username" required />
        <input type="password" bind:value={loginPassword} placeholder="Password" required />
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
    </form>
    {#if error}
      <p class="error">{error}</p>
    {/if}

    <h1>Register</h1>
    <form on:submit|preventDefault={handleRegister}>
        <input type="text" bind:value={registerUsername} placeholder="Username" required />
        <input type="password" bind:value={registerPassword} placeholder="Password" required />
        <button type="submit" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
    </form>
    {#if error}
      <p class="error">{error}</p>
    {/if}
</main>