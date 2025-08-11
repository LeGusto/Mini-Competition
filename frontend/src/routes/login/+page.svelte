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
      await goto('/main');
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
      await goto('/main');
    } else {
      error = result.error || 'Registration failed';
    }
    
    loading = false;
  }
</script>

<main>
  <div class="container">
    <div class="card">
    <h1>Login</h1>
    <form on:submit|preventDefault={handleLogin} class="login-form">
        <input type="text" bind:value={loginUsername} placeholder="Username" required />
        <input type="password" bind:value={loginPassword} placeholder="Password" required />
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
    </form>
    {#if error}
      <p class="error">{error}</p>
    {/if}
    </div>
    <div class="divider"></div>
    <div class="card">
    <h1>Register</h1>
    <form on:submit|preventDefault={handleRegister} class="register-form">
        <input type="text" bind:value={registerUsername} placeholder="Username" required />
        <input type="password" bind:value={registerPassword} placeholder="Password" required />
        <button type="submit" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
    </form>
    </div>
    {#if error}
      <p class="error">{error}</p>
    {/if}
  </div>
</main>