<main>
    <h1>Login</h1>
    <form on:submit|preventDefault={handleLogin}>
        <input type="text" name="username" placeholder="Username" />
        <input type="password" name="password" placeholder="Password" />
        <button type="submit">Login</button>
    </form>
</main>