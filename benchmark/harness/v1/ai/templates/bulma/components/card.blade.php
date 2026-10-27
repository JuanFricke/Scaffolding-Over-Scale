{{-- Anonymous Blade component. Copy to resources/views/components/card.blade.php --}}
{{-- Usage: <x-card title="Hello">Body</x-card> --}}
@props(['title' => null])

<div {{ $attributes->merge(['class' => 'card']) }}>
    @isset($title)
        <header class="card-header">
            <p class="card-header-title">{{ $title }}</p>
        </header>
    @endisset

    <div class="card-content">
        <div class="content">
            {{ $slot }}
        </div>
    </div>

    @isset($footer)
        <footer class="card-footer">
            {{ $footer }}
        </footer>
    @endisset
</div>
