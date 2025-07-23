<script lang="ts">
  import { onMount } from 'svelte';
  let selectedFile: File | null = null;
  let problemId = "";
  let language = "cpp";
  let responseMessage = "";
  let problems: string[] = [];
  let submissionId = "";
  let verdicts: { testcase: number, verdict: string }[] = [];
  let judgeStatus = "";

  onMount(async () => {
    try {
      const res = await fetch("http://localhost:5000/general/problems");
      const data = await res.json();
      problems = data.problems || [];
      if (problems.length > 0) problemId = problems[0];
    } catch (err) {
      responseMessage = "Failed to fetch problems: " + err;
    }
  });

  function handleFileChange(event: Event) {
    selectedFile = (event.target as HTMLInputElement).files?.[0] ?? null;
  }

  async function submitSolution() {
    if (!selectedFile) {
      responseMessage = "Please select a file.";
      return;
    }
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("problem_id", problemId);
    formData.append("language", language);

    try {
      const res = await fetch("http://localhost:5000/submission/submit", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      responseMessage = data.message || JSON.stringify(data);
      if (data.submissionId) {
        submissionId = data.submissionId;
        pollJudgeStatus();
      }
    } catch (err) {
      responseMessage = "Failed to submit: " + err;
    }
  }

  async function pollJudgeStatus() {
    if (!submissionId) return;
    judgeStatus = "Checking...";
    try {
      // The judge server is on port 3000
      const res = await fetch(`http://localhost:5000/submission/status/${submissionId}`);
      const data = await res.json();
      if (data.results && Array.isArray(data.results)) {
        verdicts = data.results;
        judgeStatus = "";
      } else {
        judgeStatus = data.status || JSON.stringify(data, null, 2);
      }
      if (data.status === "queued" || data.status === "processing") {
        setTimeout(pollJudgeStatus, 2000);
      }
    } catch (err) {
      judgeStatus = "Failed to get status: " + err;
    }
  }
</script>

<main>
  <h1>Welcome to Mini-Competition!</h1>
  <p>
    This is a competitive programming platform for small competitions.<br>
    Please log in or register to get started.
  </p>

  <h2>Upload a file</h2>
  <input type="file" on:change={handleFileChange} />

  <div>
    <label>
      Problem:
      <select bind:value={problemId}>
        {#each problems as pid}
          <option value={pid}>{pid}</option>
        {/each}
      </select>
    </label>
    <label>
      Language:
      <select bind:value={language}>
        <option value="cpp">C++</option>
        <option value="python">Python</option>
      </select>
    </label>
  </div>

  {#if selectedFile}
    <p>Selected file: {selectedFile.name}</p>
  {/if}

  <button on:click={submitSolution}>Submit Solution</button>
  {#if submissionId}
    <p>Submission ID: {submissionId}</p>
    {#if verdicts.length > 0}
      <h3>Test Results</h3>
      <ul>
        {#each verdicts as result}
          <li>Testcase {result.testcase}: {result.verdict}</li>
        {/each}
      </ul>
    {:else if judgeStatus}
      <pre>{judgeStatus}</pre>
    {/if}
  {/if}
</main>

<style>
  main {
    max-width: 600px;
    margin: 2rem auto;
    padding: 2rem;
    text-align: center;
    border-radius: 12px;
    background: #f9f9f9;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }
  h1 {
    color: #2d6cdf;
  }
</style>