<script>
    import { onMount } from "svelte";

    onMount(async () => {
        const response = await fetch("http://localhost:5000/contest/1");
        const data = await response.json();
        console.log(data);
    });
</script>

<div>Contests</div>