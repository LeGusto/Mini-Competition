<script lang="ts">
  import { authService } from '$lib/services/auth';
  import { goto } from '$app/navigation';
  
  // Login form variables
  let loginUsername = '';
  let loginPassword = '';
  let loginLoading = false;
  
  // Register form variables
  let registerUsername = '';
  let registerPassword = '';
  let registerLoading = false;
  
  // Shared error state
  let error = '';

  async function handleLogin() {
    loginLoading = true;
    error = '';
    
    const result = await authService.login({ username: loginUsername, password: loginPassword });
    
    if (result.success) {
      await goto('/main');
    } else {
      error = result.error || 'Login failed';
    }
    
    loginLoading = false;
  }

  async function handleRegister() {
    registerLoading = true;
    error = '';
    
    const result = await authService.register({ username: registerUsername, password: registerPassword });
    
    if (result.success) {
      await goto('/main');
    } else {
      error = result.error || 'Registration failed';
    }
    
    registerLoading = false;
  }
</script>

<main>
  <div class="login-wrapper">
    <div class="container">
      <div class="card">
      <h1>Login</h1>
      <form on:submit|preventDefault={handleLogin} class="login-form">
          <input type="text" bind:value={loginUsername} placeholder="Username" required />
          <input type="password" bind:value={loginPassword} placeholder="Password" required />
          <button type="submit" disabled={loginLoading}>
            {loginLoading ? 'Logging in...' : 'Login'}
          </button>
      </form>
      </div>
      <div class="divider"></div>
      <div class="card">
      <h1>Register</h1>
      <form on:submit|preventDefault={handleRegister} class="register-form">
          <input type="text" bind:value={registerUsername} placeholder="Username" required />
          <input type="password" bind:value={registerPassword} placeholder="Password" required />
          <button type="submit" disabled={registerLoading}>
            {registerLoading ? 'Registering...' : 'Register'}
          </button>
      </form>
      </div>
    </div>

    <!-- Error message below cards -->
    <div class="error" class:visible={error}>
      {error || ' '}
    </div>
  </div>
</main>

<style>
  .login-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2rem;
  }

  .container {
    display: flex;
    align-items: center;
    gap: 2rem;
    max-width: 900px;
    width: 100%;
  }

  .error {
    background: #4a4a4a;
    color: #ff6b6b;
    padding: 0.875rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    text-align: center;
    border: 1px solid #666;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
    width: 100%;
    visibility: hidden;
  }

  .error.visible {
    visibility: visible;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .container {
      flex-direction: column;
      gap: 1.5rem;
    }

    .divider {
      display: none;
    }
  }
</style>