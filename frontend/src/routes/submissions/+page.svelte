<script lang="ts">
    import { onMount } from 'svelte';
    import { authService } from '$lib/services/auth';
    import { authStore } from '$lib/stores/auth';
    interface Submission {
        id: number;
        problem_id: string;
        language: string;
        submission_time: string;
        status: string;
        judge_response: any;
        execution_time?: number;
        memory_used?: number;
        judge_submission_id?: string;
    }

    let submissions: Submission[] = [];
    let loading = true;
    let error: string | null = null;
    let userTimezone: string | null = null;

    onMount(async () => {
        authStore.init();
        
        const unsubscribe = authStore.subscribe(state => {
            console.log("--------------------------------")
            console.log(state.user?.timezone);
            console.log(state.user);
            console.log("--------------------------------")
        if (state.user?.timezone) {
            userTimezone = state.user.timezone;
        }
    });
    
    // Clean up subscription
    unsubscribe();
        await fetchSubmissions();
    });

    async function fetchSubmissions() {
        try {
            loading = true;
            error = null;
            
            const response = await authService.authenticatedRequest('http://localhost:5000/submission/all');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received submissions data:', data);
            
            // Log execution time values for debugging
            if (data && data.length > 0) {
                data.forEach((submission: Submission) => {
                    console.log(`Submission ${submission.id}: execution_time=${submission.execution_time} (type: ${typeof submission.execution_time})`);
                });
            }
            
            submissions = data || [];
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to fetch submissions';
        } finally {
            loading = false;
        }
    }

    function formatDate(dateString: string): string {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleString('en-US', {
            timeZone: userTimezone || undefined,
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    function getStatusColor(submission: Submission): string {
        // If we have judge response with results, use the actual verdicts for coloring
        if (submission.judge_response && submission.judge_response.results) {
            const results = submission.judge_response.results;
            if (results.length === 0) return 'submissions-status-pending';
            
            // Check if all tests passed
            const allAccepted = results.every((r: any) => r.verdict === 'Accepted');
            if (allAccepted) return 'submissions-status-accepted';
            
            // Find the first failed test and color based on its verdict
            const firstFailed = results.find((r: any) => r.verdict !== 'Accepted');
            if (firstFailed) {
                const verdict = firstFailed.verdict.toLowerCase();
                if (verdict.includes('time limit') || verdict.includes('tle')) {
                    return 'submissions-status-tle';
                } else if (verdict.includes('memory limit') || verdict.includes('mle')) {
                    return 'submissions-status-error';
                } else if (verdict.includes('runtime') || verdict.includes('re')) {
                    return 'submissions-status-error';
                } else if (verdict.includes('compilation') || verdict.includes('ce')) {
                    return 'submissions-status-compilation';
                } else {
                    return 'submissions-status-wrong';
                }
            }
        }
        
        // Fallback to status-based coloring
        const status = submission.status.toLowerCase();
        if (status === 'accepted' || status === 'ac') {
            return 'submissions-status-accepted';
        } else if (status === 'pending') {
            return 'submissions-status-pending';
        } else {
            return 'submissions-status-error';
        }
    }

    function getStatusDisplay(submission: Submission): string {
        if (!submission.status) return 'Pending';
        
        // If we have judge response with results, use the actual verdicts
        if (submission.judge_response && submission.judge_response.results) {
            const results = submission.judge_response.results;
            if (results.length === 0) return 'Pending';
            
            // Check if all tests passed
            const allAccepted = results.every((r: any) => r.verdict === 'Accepted');
            if (allAccepted) return 'Accepted';
            
            // Find the first failed test and show its verdict
            const firstFailed = results.find((r: any) => r.verdict !== 'Accepted');
            if (firstFailed) return firstFailed.verdict;
        }
        
        // Fallback to status if no detailed results
        return submission.status.charAt(0).toUpperCase() + submission.status.slice(1).toLowerCase();
    }
</script>

<svelte:head>
    <title>Submissions - Mini Competition</title>
</svelte:head>

<div class="submissions-container">
    <div class="submissions-header">
        <h1>My Submissions</h1>
        <button 
            class="submissions-refresh-btn" 
            on:click={fetchSubmissions}
            disabled={loading}
        >
            {loading ? 'Loading...' : 'Refresh'}
        </button>
    </div>

    {#if error}
        <div class="submissions-error-message">
            {error}
        </div>
    {/if}

    {#if loading}
        <div class="submissions-loading">
            <div class="submissions-spinner"></div>
            <p>Loading submissions...</p>
        </div>
    {:else if submissions.length === 0}
        <div class="submissions-empty-state">
            <p>No submissions found.</p>
            <p>Start solving problems to see your submissions here!</p>
        </div>
    {:else}
        <div class="submissions-table-container">
            <table class="submissions-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <!-- <th>Judge ID</th> -->
                        <th>Problem</th>
                        <th>Language</th>
                        <th>Status</th>
                        <th>Time</th>
                        <th>Memory</th>
                        <th>Submitted</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {#each submissions as submission}
                        <tr>
                            <td>{submission.id}</td>
                            <!-- <td>{submission.judge_submission_id || 'N/A'}</td> -->
                            <td>
                                <a href="/problem/{submission.problem_id}" class="submissions-problem-link">
                                    Problem {submission.problem_id}
                                </a>
                            </td>
                            <td class="submissions-language">{submission.language}</td>
                            <td>
                                <span class="submissions-status {getStatusColor(submission)}">
                                    {getStatusDisplay(submission)}
                                </span>
                            </td>
                            <td class="submissions-time">
                                {submission.execution_time ? `${submission.execution_time}s` : 'N/A'}
                            </td>
                            <td class="submissions-memory">
                                {submission.memory_used ? `${submission.memory_used}MB` : 'N/A'}
                            </td>
                            <td class="submissions-date">{formatDate(submission.submission_time)}</td>
                            <td>
                                {#if submission.judge_response}
                                    <details class="submissions-details">
                                        <summary>View Details</summary>
                                        <pre class="submissions-judge-response">{JSON.stringify(submission.judge_response, null, 2)}</pre>
                                    </details>
                                {:else}
                                    <span class="submissions-no-details">No details available</span>
                                {/if}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>

<style>
    .submissions-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
        width: 100%;
    }

    .submissions-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
    }

    .submissions-header h1 {
        margin: 0;
        color: #333;
        font-size: 2rem;
    }

    .submissions-refresh-btn {
        background: #007bff;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1rem;
    }

    .submissions-refresh-btn:hover:not(:disabled) {
        background: #0056b3;
    }

    .submissions-refresh-btn:disabled {
        background: #ccc;
        cursor: not-allowed;
    }

    .submissions-error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        border: 1px solid #f5c6cb;
    }

    .submissions-loading {
        text-align: center;
        padding: 40px;
    }

    .submissions-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #007bff;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: submissions-spin 1s linear infinite;
        margin: 0 auto 20px;
    }

    @keyframes submissions-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .submissions-empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #666;
    }

    .submissions-empty-state p {
        margin: 10px 0;
        font-size: 1.1rem;
    }

    .submissions-table-container {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }

    .submissions-table {
        width: 100%;
        border-collapse: collapse;
    }

    .submissions-table th, 
    .submissions-table td {
        padding: 15px;
        text-align: left;
        border-bottom: 1px solid #eee;
    }

    .submissions-table th {
        background: #f8f9fa;
        font-weight: 600;
        color: #495057;
    }

    .submissions-table tr:hover {
        background: #f8f9fa;
    }

    .submissions-problem-link {
        color: #007bff;
        text-decoration: none;
        font-weight: 500;
    }

    .submissions-problem-link:hover {
        text-decoration: underline;
    }

    .submissions-language {
        font-family: 'Courier New', monospace;
        background: #f8f9fa;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.9rem;
    }

    .submissions-status {
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.9rem;
        display: inline-block;
        min-height: 24px;
        line-height: 1.2;
        white-space: normal;
        word-wrap: break-word;
        text-align: center;
        vertical-align: middle;
    }

    .submissions-status-accepted {
        color: #059669;
        background: #d1fae5;
        padding: 6px 10px;
    }

    .submissions-status-wrong {
        color: #dc2626;
        background: #fee2e2;
        border: 1px solid #fecaca;
        padding: 6px 10px;
    }

    .submissions-status-tle {
        color: #d97706;
        background: #fef3c7;
        border: 1px solid #fed7aa;
        padding: 6px 10px;
    }

    .submissions-status-error {
        color: #dc2626;
        background: #fee2e2;
        border: 1px solid #fecaca;
        font-weight: 700;
        padding: 6px 10px;
    }

    .submissions-status-compilation {
        color: #ea580c;
        background: #fed7aa;
        border: 1px solid #fdba74;
        padding: 6px 10px;
    }

    .submissions-status-pending {
        color: #6b7280;
        background: #f3f4f6;
        padding: 6px 10px;
    }

    .submissions-time, .submissions-memory {
        font-family: 'Courier New', monospace;
        background: #f8f9fa;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.9rem;
        text-align: center;
    }

    .submissions-date {
        color: #666;
        font-size: 0.9rem;
    }

    .submissions-details summary {
        cursor: pointer;
        color: #007bff;
        font-size: 0.9rem;
    }

    .submissions-details summary:hover {
        text-decoration: underline;
    }

    .submissions-judge-response {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        max-height: 200px;
        overflow-y: auto;
        margin-top: 10px;
        white-space: pre-wrap;
    }

    .submissions-no-details {
        color: #999;
        font-style: italic;
        font-size: 0.9rem;
    }

    @media (max-width: 768px) {
        .submissions-container {
            padding: 10px;
        }

        .submissions-header {
            flex-direction: column;
            gap: 15px;
            align-items: flex-start;
        }

        .submissions-table-container {
            overflow-x: auto;
        }

        .submissions-table th, 
        .submissions-table td {
            padding: 10px;
            font-size: 0.9rem;
        }
    }
</style>
