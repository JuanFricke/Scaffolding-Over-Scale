<?php

use App\Models\Post;
use App\Models\User;

use function Pest\Laravel\actingAs;

it('creates a post', function () {
    $user = User::factory()->create();

    actingAs($user)
        ->postJson('/api/posts', [
            'title' => 'Hello',
            'body' => 'World',
        ])
        ->assertCreated()
        ->assertJsonPath('data.title', 'Hello');

    expect(Post::where('title', 'Hello')->exists())->toBeTrue();
});
