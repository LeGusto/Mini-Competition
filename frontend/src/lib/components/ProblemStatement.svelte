<script lang="ts">
  export let pdfUrl: string | null = null;
  export let problemId: string;
  export let height: number = 700;

  function downloadPDF() {
    if (pdfUrl) {
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = `problem_${problemId}.pdf`;
      link.click();
    }
  }

  function openPDFInNewTab() {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank');
    }
  }
</script>

<div class="statement-card">
  <div class="statement-header">
    <h2>Problem Statement</h2>
    <div class="statement-actions">
      {#if pdfUrl}
        <button class="btn btn-small btn-secondary" on:click={downloadPDF}>
          Download PDF
        </button>
        <button class="btn btn-small btn-secondary" on:click={openPDFInNewTab}>
          Open in New Tab
        </button>
      {/if}
    </div>
  </div>

  {#if pdfUrl}
    <div class="pdf-container">
      <iframe
        src={pdfUrl}
        title="Problem Statement"
        width="100%"
        height="{height}"
      ></iframe>
    </div>
  {:else}
    <div class="no-statement">
      Problem statement not available
    </div>
  {/if}
</div>

<style>
  .statement-card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 1rem;
  }

  .statement-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .statement-header h2 {
    font-family: 'Courier New', monospace;
    color: #f5f5f5;
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
  }

  .statement-actions {
    display: flex;
    gap: 0.5rem;
  }

  .pdf-container {
    border: 1px solid #333;
    border-radius: 4px;
    overflow: hidden;
  }

  .no-statement {
    text-align: center;
    padding: 2rem;
    color: #888;
    font-family: 'Courier New', monospace;
  }

  .btn {
    padding: 0.375rem 0.75rem;
    border: none;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: inline-block;
    text-align: center;
  }

  .btn-secondary {
    background: #444;
    color: #e0e0e0;
  }

  .btn-secondary:hover {
    background: #555;
  }
</style>
