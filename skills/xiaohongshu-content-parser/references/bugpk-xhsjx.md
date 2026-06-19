# BugPk XHSJX API Reference

## Endpoint

`GET https://api.bugpk.com/api/xhsjx?url=<full_xiaohongshu_share_url>`

## Expected response fields

- `code`
- `msg`
- `data.type`
- `data.title`
- `data.desc`
- `data.author.name`
- `data.author.id`
- `data.author.avatar`
- `data.cover`
- `data.url`
- `data.images`
- `data.live_photo`
- `data.video_backup`
- `cache_status`
- `bktip.website`
- `bktip.tip`

## Practical notes

- `desc` is the正文.
- Some responses return `video_backup` as a string.
- A direct `520` usually means transport or edge blocking, not a schema problem.
- Prefer browser-like headers and retry once.
