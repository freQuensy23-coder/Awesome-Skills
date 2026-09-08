# Controlling the Treblo website

These controls were observed in the live English UI in September 2026. Inspect the current DOM before acting; labels and routes can change. The workflow uses the ordinary authenticated editor. Use browser automation only with the provider's required authorization; otherwise perform these UI steps manually or use the supported public API. It does not bypass login, verification, limits, or moderation.

## Start with a real, persistent browser

Use your agent's existing authorized browser when available. Preserve its profile, accounts, and unrelated tabs. Confirm that the page is actually Treblo, not an error, stale tab, or login wall. If a proxy is part of the user's environment, verify connectivity from inside that browser; do not change identities or network locations to avoid limits.

On a fresh local Linux workstation with Google Chrome installed and a graphical session, an example dedicated browser launch is:

```bash
google-chrome --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.local/share/music-editor-browser" \
  https://treblo.com/
```

Use the installed Chrome executable on your OS. Do not launch this command against a profile that another Chrome process already owns. Keep CDP bound to localhost; it grants control of logged-in accounts. A remote machine needs an authenticated desktop/tunnel rather than a public CDP listener. A dedicated profile is for stable task state, not repeated signups.

An agent with Playwright can attach to that browser without installing a second browser:

```bash
python -m pip install playwright
```

```python
from playwright.sync_api import sync_playwright

pw = sync_playwright().start()
browser = pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
context = browser.contexts[0]
page = context.new_page()
page.goto("https://treblo.com/create")
page.bring_to_front()
print(page.url, page.title())
print(page.locator("body").inner_text())
```

The following `page` examples use this same session. In a Hermes browser tool, evaluate the equivalent JavaScript through its DOM evaluator. Do not call `browser.close()` on a shared browser. Close only your task tab if appropriate, then detach the client.

## Registration and initial upload

Complete [normal registration](accounts-and-limits.md). Open **Create → New Project** or an existing private project. Record the project ID from the resulting `/editor/…` URL. Give the project a useful name through the available title control. A name containing “private” is not a privacy setting: inspect the actual sharing state and do not publish the track.

The observed project screen has an **Upload** button with `aria-label="Upload"`. Clicking it opens **Upload to Project**, with an audio file input and the statement “I confirm that I own or have permission to use all content in the recording I'm uploading.” The supported input selector was `input[type=file]`, accepting common WAV, MP3, FLAC, OGG, MPEG/MP4, AIFF and other audio MIME types. The UI can enforce further limits; inspect its current error rather than assuming the API's size cap applies to this form.

```python
page.get_by_role("button", name="Upload", exact=True).first.click()
dialog = page.get_by_role("dialog")
dialog.locator('input[type="file"]').set_input_files("work/source.wav")
```

Only after the user has authorized the required rights attestation, check the permission box and submit the **Upload** button inside that dialog. Wait for processing to complete and for a playable track, duration, waveform, and lyric alignment. Read the resulting track ID and source audio URL from the editor's own state/network response. Preserve them privately.

With raw CDP, a file-input fallback is `DOM.setFileInputFiles` using the input's persistent `backendNodeId`. The file must exist on the browser host. Temporary `Runtime.evaluate` object IDs are session-scoped; do not reuse one across disconnected tool calls. After any upload action, verify that the filename/track actually appears before submitting or retrying.

A duplicate upload returned HTTP 422 “This upload matches existing audio and cannot be used.” Reuse the existing track. Do not alter a file merely to defeat duplicate detection.

## Open the correct replacement controls

Select the actual source track. Choose **Edit** or **Resume edit**, then **Replace** rather than Extend/Reference. Use **Advanced** and verify **v2.2**. A v2 deprecation/queue notice does not establish that v3 supports the same edit mode; recheck the live model selector and official documentation.

If an old draft is blocking the operation, inspect its track and lyrics before discarding it. Discard only the obsolete draft for this task. A stale dialog remained visually mounted after discard in one run; reloading the exact project cleared it without deleting source audio. Never discard an unrelated edit to simplify automation.

## Select seconds, not a guessed waveform position

Use the original track's aligned lyrics as an initial estimate and verify the audible phonetic boundaries. Select mode is critical: the control with `aria-label="Place an edit manually"` changes the timeline hint to **Drag to select**. If the hint still says **Click to insert, replace, or reference**, dragging can pan the waveform instead.

Prefer numeric start/end inputs if your current UI exposes them. Otherwise, zoom until two known time ticks and both requested boundaries are visible. Measure the horizontal positions of those ticks and calculate the linear mapping:

`x(t) = x1 + (t - t1) * (x2 - x1) / (t2 - t1)`.

Read the actual tick positions from the DOM. Never reuse coordinates from another viewport. The observed viewport ID was `timeline-viewport`; selection handles expose `role="slider"` and labels such as **Selection start** and **Selection end**. Read their `aria-valuenow` after every selection.

A normal Playwright mouse drag on the visible waveform is the first choice:

```python
# x_start, x_end and y must come from this page's measured timeline.
page.mouse.move(x_start, y)
page.mouse.down()
page.mouse.move(x_end, y, steps=8)
page.mouse.up()
```

Keep press/move/release in the same attached CDP session. In stateless tools, a gesture split across sessions can stall or have no effect. When the site's ordinary selection handler accepts DOM pointer events, this fallback worked; it is layout interaction, not a trusted-event/security bypass:

```javascript
async function dragVisibleSelection(xStart, xEnd, y) {
  const viewport = document.getElementById('timeline-viewport');
  if (!viewport) throw new Error('Timeline not found');
  const pause = () => new Promise(resolve => setTimeout(resolve, 60));
  const opts = x => ({bubbles: true, clientX: x, clientY: y,
    pointerId: 17, pointerType: 'mouse', isPrimary: true, buttons: 1});
  viewport.dispatchEvent(new PointerEvent('pointerdown', opts(xStart)));
  await pause();
  document.dispatchEvent(new PointerEvent('pointermove', opts(xEnd)));
  await pause();
  document.dispatchEvent(new PointerEvent('pointerup', {...opts(xEnd), buttons: 0}));
  await pause();
  return [...document.querySelectorAll('[role=slider]')].map(e => ({
    label: e.getAttribute('aria-label'), value: e.getAttribute('aria-valuenow')
  }));
}
```

Call this only after confirming Select mode and that the coordinates are within the visible waveform. Verify the resulting interval independently. Pointer movement without a changed selection is a failure, not success.

## React inputs and stale layout

A form-filling tool reported success while the custom lyric text remained unchanged. Read back both the textarea value and the settled editor state. A native setter plus bubbling input/change events updated the controlled textarea:

```javascript
function setCustomLyrics(lines) {
  const e = [...document.querySelectorAll('textarea')]
    .find(x => x.placeholder.startsWith('Write custom lyrics'));
  if (!e) throw new Error('Custom lyric field not found');
  const value = lines.join('\n');
  Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')
    .set.call(e, value);
  e.dispatchEvent(new Event('input', {bubbles: true}));
  e.dispatchEvent(new Event('change', {bubbles: true}));
  return e.value;
}
```

Wait for a render, read the value again, and verify the submit button is enabled. Preserve intended newlines. In the website, Auto style conditioning and custom lyrics worked; the developer API has different tag-validation requirements.

A hidden tab delayed entrance animations and made the audio dock appear clipped. First bring the correct target to the foreground and inspect `document.visibilityState`, its bounding boxes, and `document.elementsFromPoint(x, y)`. Reload only after preserving the draft if needed. A temporary CSS change to the existing dock's bottom position/animation was used as a last-resort display repair; it did not alter selection values, account permissions, disabled controls, or the request. Do not disable a security overlay or permission gate. Re-read all coordinates after any viewport/layout change.

## Submit once and read back the real task

Before submission, verify source track, privacy/sharing state, model, exact interval, exact lyrics, output count and budget. Click the normal **Generate** button once. Observe the site's actual response. A 403 `TURNSTILE_REQUIRED` was followed by the site's own automatic verification and a successful retry in one run. Let that flow finish; do not fabricate tokens or repeatedly resubmit while a request is pending. If a human-only challenge or login wall blocks progress, retain the page and ask for the required authorization step.

For debugging, record only a whitelist of request fields, status and returned task/track IDs. Never export a HAR, cookies, Authorization headers, Turnstile tokens or all browser storage. The observed native route was `https://p.treblo.com/generate/v2/inpaint/PROJECT_ID`, with trackId, inpaintSelection, inpaintLyrics, num_songs, model_version, selection_crop and reference_mode among its fields. This is an observed internal UI route, not a supported public API contract; submit through the normal UI rather than copying private headers to scripts.

The editor read project tracks from the same-origin route below. Obtain the ID from your actual project, not this documentation:

```javascript
async function readProjectTracks(projectId) {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(projectId)) throw new Error('Unexpected project ID');
  const r = await fetch(`/api/v1/projects/${projectId}/tracks?pageSize=30`);
  if (!r.ok) throw new Error(`Track read failed: ${r.status}`);
  return await r.json();
}
```

Observed JSON stored track metadata in `entities.tracks`, keyed by track ID, with `status`, `songPath`, `generationId`, `inpaintParams`, and `publicPost`. Use only the returned IDs for this request, persist every status batch, and poll at a bounded interval such as 20 seconds. Require the expected count, `SUCCESS` for every chosen take and a nonempty `songPath`. Do not equate TASK_SENT, queue position, or an enabled Edit button with completion. Preserve terminal errors. If the requested ID is outside the first page, follow the UI's actual pagination or observed exact-track read; do not silently drop it.

Read back `inpaintParams` to verify lyrics and mask. Verify sharing/publication separately; the tested new tracks had `publicPost: null` and were never published. Download the actual successful `songPath` promptly, then perform [local composition and QA](editing-and-qa.md). Reloading a stale project view can update status without canceling an already accepted generation.

## Sources

[Treblo Create](https://treblo.com/create), [developer docs](https://treblo.com/developers/docs), and [terms](https://treblo.com/tos). Internal selectors and endpoint schemas above are dated live observations, not promises of future UI compatibility.
