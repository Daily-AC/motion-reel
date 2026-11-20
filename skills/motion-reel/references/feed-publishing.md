# Publishing to short-video feeds

Douyin, TikTok, Instagram Reels and YouTube Shorts play full-screen 9:16 video in an autoplaying feed, under the platform's own interface. These rules come from films delivered to such a feed; check the current app before relying on exact pixel positions, which change with app versions and devices.

## Author the vertical cut

Render 1080×1920 from a project whose layouts were composed for it. Never letterbox the landscape film into a portrait frame: the picture shrinks to a third of the screen. Canvas2D shots need their own portrait layouts (type size, line breaks, subject position). three.js shots can keep their storyboard and extend height (see [three-d.md](three-d.md)). Review the portrait cut's own decoded frames; a landscape review says nothing about it.

## Hook and opening

- Frame 0 is the cover the feed shows before playback and the first thing a scrolling viewer sees, so it must already be a finished picture. Do not grow it from black or type it on at the very start; start from a complete state and move from there (for example, pull back from a close-up).
- Put a short hook title on screen within the first second and clear it before the drums come in, so it does not compete with the first impact.
- Have sound at frame 0, not after a silent lead-in.

## Safe zones on a 1080×1920 frame

- Top: the status bar and the app's tabs cover the top edge. A HUD or label belongs in a band around y ≈ 250, below them; the engine's HUD moves there on a portrait canvas.
- Bottom: about the lowest 25% holds the account name, caption and music line. Keep titles, faces, logos and numbers out of it.
- Right: a column of buttons (like, comment, share, avatar) runs down the right edge. Keep key content left of it.
- Low subjects should sit mid-frame; in 3D, lower the look target for portrait.

Check the actual frame by overlaying these regions on decoded stills; the platform's preview inside the upload screen is the final authority.

## Covers

- The vertical cover defaults to frame 0. Design frame 0 as a poster: subject, title and brand legible at thumbnail size.
- For a landscape upload, pick a frame with a horizontal composition, often the end card, rather than an arbitrary mid-action frame.
- Some platforms offer AI-recommended covers that add their own text or crop. Inspect the cover preview before publishing and replace it if it added words or cut the subject.

## Before publishing

Publishing is a separate step from rendering: do it only with the user's authorization. Report the cover frame used, the aspect ratio actually uploaded and anything the platform changed.
