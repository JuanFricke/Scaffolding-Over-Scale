{{-- Anonymous Blade component. Copy to resources/views/components/modal.blade.php --}}
{{-- Usage: <x-modal id="confirm" title="Are you sure?">Body</x-modal>          --}}
{{-- Open with a trigger that toggles is-active, e.g.                            --}}
{{--   <button data-modal-open="confirm" class="button">Open</button>           --}}
@props(['id', 'title' => null])

<div id="{{ $id }}" class="modal" role="dialog" aria-modal="true"
     @isset($title) aria-label="{{ $title }}" @endisset>
    <div class="modal-background" data-modal-close="{{ $id }}"></div>
    <div class="modal-card">
        <header class="modal-card-head">
            <p class="modal-card-title">{{ $title }}</p>
            <button class="delete" aria-label="close" data-modal-close="{{ $id }}"></button>
        </header>
        <section class="modal-card-body">
            {{ $slot }}
        </section>
        @isset($footer)
            <footer class="modal-card-foot">{{ $footer }}</footer>
        @endisset
    </div>
</div>

{{-- Minimal, framework-free toggle (include once per page, e.g. in the layout) --}}
<script>
document.addEventListener('click', (e) => {
    const open = e.target.closest('[data-modal-open]');
    if (open) document.getElementById(open.dataset.modalOpen)?.classList.add('is-active');
    const close = e.target.closest('[data-modal-close]');
    if (close) document.getElementById(close.dataset.modalClose)?.classList.remove('is-active');
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') document.querySelectorAll('.modal.is-active').forEach(m => m.classList.remove('is-active'));
});
</script>
