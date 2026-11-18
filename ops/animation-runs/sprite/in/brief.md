# Morning Loaf: the baker's sprite sheets

Morning Loaf is making a small 2D game. Its hero is the bread mascot in ~/work/input/mascot.png (also as mascot.svg). Make the mascot's sprite sheets, in a pixel-art style.

1. Walk: 8 frames of the mascot walking to the right, a full walk cycle.
2. Idle: 4 frames of the mascot standing and breathing.

Each frame 128 x 128 pixels, frames side by side in one row, transparent background. The mascot must look the same in every frame (same size, colours, hat and face) and stand on the same ground line.

Deliver ~/work/output/walk.png (1024 x 128) and ~/work/output/idle.png (512 x 128).

preview.mp4: 1024 x 512 on a light grey background, 4 seconds: the walk cycle playing at 12 frames per second, scaled up 4x without smoothing.

An image model is available if your tool wants one: an OpenAI-compatible endpoint is set in OPENAI_BASE_URL and OPENAI_API_KEY (gpt-image-2), and Gemini's API answers at its usual address.
