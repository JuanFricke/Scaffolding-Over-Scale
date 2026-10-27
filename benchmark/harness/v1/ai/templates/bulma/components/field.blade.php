{{-- Anonymous Blade component. Copy to resources/views/components/field.blade.php --}}
{{-- Usage: <x-field name="email" label="Email" type="email" required /> --}}
@props([
    'name',
    'label',
    'type' => 'text',
    'value' => null,
    'required' => false,
    'help' => null,
])

@php($id = $attributes->get('id', $name))

<div class="field">
    <label class="label" for="{{ $id }}">{{ $label }}</label>
    <div class="control">
        <input
            id="{{ $id }}"
            name="{{ $name }}"
            type="{{ $type }}"
            @if($required) required @endif
            value="{{ old($name, $value) }}"
            {{ $attributes->merge(['class' => 'input' . ($errors->has($name) ? ' is-danger' : '')]) }}
        >
    </div>

    @if($help)
        <p class="help">{{ $help }}</p>
    @endif

    @error($name)
        <p class="help is-danger">{{ $message }}</p>
    @enderror
</div>
