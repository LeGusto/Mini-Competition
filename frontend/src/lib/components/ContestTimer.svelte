<script lang="ts">
  export let timerText: string = '';
  export let className: string = '';
</script>

{#if timerText}
  <span class="contest-timer {className}">{timerText}</span>
{/if}

<style>
  .contest-timer {
    color: #ef5350;
    font-family: 'Courier New', monospace;
    font-size: 0.95rem;
    font-weight: 600;
    background: #3a1a1a;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #f44336;
    display: inline-block;
    white-space: nowrap;
  }

  @media (max-width: 768px) {
    .contest-timer {
      font-size: 0.85rem;
      padding: 0.4rem 0.8rem;
    }
  }
</style>
