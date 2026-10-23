# Weekly LinkedIn video pipeline

Python 3.12 with Playwright; Chromium and FFmpeg for rendering. No Make required.
Use the existing isolated checkout; no additional worktree is needed.

## Scope

Notion → script → explicit approval → storyboard/HTML preview → explicit approval →
English TTS + static slide video + supplied intro/outro → final video review.
The current renderer is a typography slideshow, not animated illustrations. The `visual`
field is a direction for review, not an implemented diagram. No automatic publishing or
upload to an external video host is implemented: that service is not yet specified.
Scripts and storyboards are saved in labeled JSON code blocks in the original task;
edit the narration/slides in the latest block before approving changes. Review factual
claims with company-approved sources. AI output is not automatically fact-verified.

## Notion setup

Data source: `3fe99be2-aa09-8098-b57d-000b14659f6e` (Task Tracker).
Existing Topic, Week, LinkedIn, and 制作状态 are preserved.
Add these three **select options** to 制作状态:

- 脚本已通过 — reviewer explicitly approves the latest script.
- 分镜已通过 — reviewer explicitly approves the latest storyboard AND HTML preview.
- 视频已通过 — final reviewer approval; retained for future delivery integration only.

Existing waiting states never trigger the next stage. Set `待制作` to request a new
script, `脚本已通过` for storyboard creation, and `分镜已通过` for rendering.
Keep VIDEO_WEEK blank until ready: it prevents creating new scripts, but still processes
approved stages. The first rollout uses an explicit Week value rather than unreliable
parsing of existing free-text date ranges. Automatic calendar selection remains future work.
If an operation fails, inspect Notion and the run output before retrying: a network failure
between writing a block and updating its status can leave a saved block with the old status.
One task per run; concurrency prevents overlap within this workflow, not across other clients.

Create a Notion internal integration with read/update/insert content permissions and grant
it access to Video Project. Store its token as GitHub Actions secret `NOTION_TOKEN`.
Store an OpenAI API key as `OPENAI_API_KEY`. Never send values through chat or commit them.
ChatGPT subscription does not supply API credit. Existing Make OAuth is not reused here.

## Local use

Current rollout skips intro/outro: the workflow sets `BODY_ONLY=true`, producing a
40-second body. Locally use `--body-only`. For an offline silent typography preview:
`python pipeline.py --demo examples/storyboard.json --output output/body-only`.
This demo does not read Notion, call AI, synthesize speech, or mark anything approved.
Unset BODY_ONLY when the supplied intro/outro assets are ready for the 60-second workflow.

```
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python pipeline.py --preview examples/storyboard.json --output output/preview
# With credentials securely injected:
python pipeline.py --week '01 · Oct 20–26, 2026'
```

The local preview command makes no network requests. Open output/preview/index.html.
For video, supply company intro/outro as assets/intro.mp4 and assets/outro.mp4 or set
INTRO_FILE/OUTRO_FILE to local paths. These are intentionally ignored by Git. On cloud
runners use a private persistent asset store and a secure download step, or add only
non-confidential approved assets to the private repository with an explicit Git ignore
exception. Assets have NOT been supplied or configured yet.

Rendering measures both clips and allocates the balance of 60 seconds to the body.
It rejects body durations outside 30–45 seconds and rejects narration that exceeds that
space. Shorter narration is padded with silence; no background music or captions are
currently generated. Landscape 1920×1080, 30 fps; preserve supplied intro/outro audio.
Review audio transitions before final approval.

## GitHub operation

Push this code to the selected repository (not done by setup). Add secrets and assets
before running Actions → Weekly video pipeline → Run workflow. Enter an exact Week to
create a script, or leave blank to advance approved tasks (unless VIDEO_WEEK is configured).
Download the `video-output-*` artifact from the run for HTML previews/video; extract the
whole ZIP before opening index.html. Artifact retention is 90 days, not permanent hosting.
Artifacts are not publicly published links and are not written into LinkedIn.

The hourly schedule is disabled unless repository variable VIDEO_AUTOMATION_ENABLED=true.
Only enable it after a successful end-to-end run. VIDEO_WEEK may hold the exact selected
week, but must be updated for each new week. A run advances only one stage of one task.
AI API usage and GitHub Actions/storage can incur charges; monitor account quotas.

## Validation status

Offline tests cover approval gates, payload reading, HTML escaping, and real FFmpeg /
Chromium rendering using synthetic test media and mocked TTS. They do not establish live
Notion access, OpenAI access, correct company facts, hosted automation, or publication.
