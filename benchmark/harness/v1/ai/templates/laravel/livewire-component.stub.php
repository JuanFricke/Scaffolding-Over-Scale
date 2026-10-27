<?php

namespace App\Livewire;

use App\Models\Post;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Validation\ValidationException;
use Livewire\Attributes\Computed;
use Livewire\Attributes\Locked;
use Livewire\Attributes\Validate;
use Livewire\Component;
use Livewire\WithFileUploads;

/**
 * Secure-by-default Livewire component skeleton.
 *
 * Follow ai/skills/livewire/livewire-policy.md. Reminders:
 *  - Public properties are client-writable hidden fields -> validate them.
 *  - #[Locked] for server-only context (never assign untrusted data into it).
 *  - Every public method is a public endpoint -> authorize inside it.
 *  - Never trust action parameters -> resolve + authorize every time.
 */
class ExampleComponent extends Component
{
    use WithFileUploads;

    #[Locked]
    public int $postId;

    #[Validate('required|string|min:3|max:255')]
    public string $title = '';

    // 1MB image; validate the real file, let store() name it.
    #[Validate('nullable|image|max:1024')]
    public $photo = null;

    public function mount(Post $post): void
    {
        $this->authorize('update', $post);
        $this->postId = $post->id;
        $this->title = $post->title;
    }

    public function save(): void
    {
        $post = Post::findOrFail($this->postId);
        $this->authorize('update', $post);
        $this->validate();

        if ($this->photo) {
            $post->cover_path = $this->photo->store(path: 'covers');
        }

        $post->update(['title' => $this->title]);
    }

    public function delete(int $id): void
    {
        // Do NOT trust $id: resolve then authorize.
        $post = Post::findOrFail($id);
        $this->authorize('delete', $post);
        $post->delete();
    }

    public function sensitiveAction(): void
    {
        $key = 'sensitive:'.auth()->id();

        if (RateLimiter::tooManyAttempts($key, maxAttempts: 5)) {
            throw ValidationException::withMessages([
                'title' => 'Too many attempts. Try again in '.RateLimiter::availableIn($key).'s.',
            ]);
        }

        RateLimiter::hit($key, decaySeconds: 60);

        // ... do the work ...
    }

    // Derived from sensitive data: computed, not a public property.
    #[Computed]
    public function summary(): string
    {
        return str($this->title)->limit(50)->value();
    }

    // Internal plumbing stays protected/private so the client can't call it.
    protected function reset(): void
    {
        $this->title = '';
        $this->photo = null;
    }

    public function render()
    {
        return view('livewire.example-component');
    }
}
