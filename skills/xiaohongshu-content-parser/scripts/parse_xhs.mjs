#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function parseArgs(argv) {
  const args = { downloadVideo: false, downloadImages: true, retry: 1 };
  for (let i = 2; i < argv.length; i += 1) {
    const item = argv[i];
    if (item === '--url') args.url = argv[++i];
    else if (item === '--from-file') args.fromFile = argv[++i];
    else if (item === '--out-dir') args.outDir = argv[++i];
    else if (item === '--no-download') args.noDownload = true;
    else if (item === '--download-video') args.downloadVideo = true;
    else if (item === '--no-images') args.downloadImages = false;
    else if (item === '--retry') args.retry = Number(argv[++i] ?? 1);
    else if (item === '--help' || item === '-h') args.help = true;
  }
  return args;
}

function ensureUrl(input) {
  if (!input) throw new Error('Missing --url or --from-file');
  return input;
}

function normalizeVideoBackup(value) {
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === 'string' && value) return [value];
  return [];
}

function sanitizeName(name) {
  return String(name || 'unknown').replace(/[\\/:*?"<>|\n\r]+/g, '_').slice(0, 120);
}

function getShanghaiDateStamp(date = new Date()) {
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Shanghai'
  }).format(date);
}

function extractPostId(sourceUrl) {
  try {
    const u = new URL(sourceUrl);
    const m = u.pathname.match(/\/explore\/([^/]+)/);
    return m?.[1] || '';
  } catch {
    return '';
  }
}

function buildRunFolderName(normalized) {
  const title = sanitizeName(normalized.title || 'xiaohongshu');
  const date = getShanghaiDateStamp();
  const postId = sanitizeName(extractPostId(normalized.sourceUrl) || 'unknown');
  return `${title}-${date}-${postId}`;
}

function resolveDownloadRoot(cwd) {
  return path.join(cwd, 'xiaohongshu-notes');
}

function pickText(value) {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
}

function buildNormalized(payload, sourceUrl) {
  const data = payload?.data || {};
  const author = data.author || {};
  const images = Array.isArray(data.images) ? data.images.filter(Boolean) : [];
  const livePhoto = Array.isArray(data.live_photo) ? data.live_photo.filter(Boolean) : [];
  const videoBackup = normalizeVideoBackup(data.video_backup);

  return {
    sourceUrl,
    code: payload?.code ?? null,
    msg: payload?.msg ?? '',
    cache_status: payload?.cache_status ?? null,
    bktip: payload?.bktip ?? null,
    type: data.type ?? null,
    title: data.title ?? '',
    desc: data.desc ?? '',
    author: {
      name: author.name ?? '',
      id: author.id ?? '',
      avatar: author.avatar ?? ''
    },
    cover: data.cover ?? '',
    url: data.url ?? '',
    images,
    live_photo: livePhoto,
    video_backup: videoBackup,
    counts: {
      images: images.length,
      live_photo: livePhoto.length,
      video_backup: videoBackup.length
    },
    supported_metrics: ['title', 'desc', 'author', 'cover', 'url', 'images', 'live_photo', 'video_backup', 'cache_status', 'bktip'],
    unsupported_metrics: ['likes', 'comments', 'favorites', 'shares', 'plays', 'followers']
  };
}

async function fetchJson(url) {
  const res = await fetch(url, {
    headers: {
      accept: 'application/json, text/plain, */*',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
      referer: 'https://api.bugpk.com/',
      origin: 'https://api.bugpk.com'
    }
  });
  const text = await res.text();
  if (!res.ok) {
    const err = new Error(`HTTP ${res.status}`);
    err.status = res.status;
    err.body = text;
    throw err;
  }
  return JSON.parse(text);
}

async function fetchWithRetry(apiUrl, retries) {
  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      return await fetchJson(apiUrl);
    } catch (err) {
      lastErr = err;
      if (String(err?.status) === '520' && attempt < retries) continue;
      if (attempt < retries) continue;
      throw err;
    }
  }
  throw lastErr;
}

async function readJsonFile(filePath) {
  const raw = await fs.readFile(filePath, 'utf8');
  return JSON.parse(raw);
}

function apiUrlFor(sourceUrl) {
  const u = new URL('https://api.bugpk.com/api/xhsjx');
  u.searchParams.set('url', sourceUrl);
  return u.toString();
}

async function writeFileSafe(filePath, content) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, content);
}

async function downloadToFile(url, filePath) {
  const res = await fetch(url, {
    headers: {
      accept: '*/*',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    }
  });
  if (!res.ok) throw new Error(`Download failed: ${res.status} ${url}`);
  const buf = Buffer.from(await res.arrayBuffer());
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, buf);
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    console.log('Usage: node parse_xhs.mjs --url <share-url> [--out-dir <root-dir>] [--no-download] [--download-video] [--from-file <raw.json>]');
    process.exit(0);
  }

  const cwd = process.cwd();
  const rootDir = path.resolve(args.outDir || resolveDownloadRoot(cwd));

  let payload;
  let sourceUrl = '';
  if (args.fromFile) {
    payload = await readJsonFile(args.fromFile);
    sourceUrl = payload?.sourceUrl || payload?.requestUrl || '';
  } else {
    sourceUrl = ensureUrl(args.url);
    const apiUrl = apiUrlFor(sourceUrl);
    payload = await fetchWithRetry(apiUrl, Math.max(0, args.retry));
  }

  const normalized = buildNormalized(payload, sourceUrl);
  const outDir = path.join(rootDir, buildRunFolderName(normalized));
  const mediaDir = path.join(outDir, 'media');
  await fs.mkdir(outDir, { recursive: true });
  await writeFileSafe(path.join(outDir, 'raw.json'), JSON.stringify(payload, null, 2));
  await writeFileSafe(path.join(outDir, 'normalized.json'), JSON.stringify(normalized, null, 2));

  const downloads = [];
  if (!args.noDownload) {
    const authorAvatar = normalized.author.avatar;
    const cover = normalized.cover;
    const images = normalized.images;
    const video = normalized.url;
    if (authorAvatar) {
      const file = path.join(mediaDir, `author-avatar${path.extname(new URL(authorAvatar).pathname) || '.jpg'}`);
      await downloadToFile(authorAvatar, file);
      downloads.push(file);
    }
    if (cover) {
      const file = path.join(mediaDir, `cover${path.extname(new URL(cover).pathname) || '.jpg'}`);
      await downloadToFile(cover, file);
      downloads.push(file);
    }
    if (args.downloadImages) {
      for (let i = 0; i < images.length; i += 1) {
        const img = images[i];
        const file = path.join(mediaDir, `image-${String(i + 1).padStart(2, '0')}${path.extname(new URL(img).pathname) || '.jpg'}`);
        await downloadToFile(img, file);
        downloads.push(file);
      }
    }
    if (args.downloadVideo && video) {
      const file = path.join(mediaDir, `video${path.extname(new URL(video).pathname) || '.mp4'}`);
      await downloadToFile(video, file);
      downloads.push(file);
    }
  }

  const report = [
    `# ${normalized.title || 'Xiaohongshu Post'}`,
    '',
    '## 结论',
    `- 标题：${normalized.title || '待确认'}`,
    `- 作者：${normalized.author.name || '待确认'}`,
    `- 正文：${normalized.desc || '待确认'}`,
    `- 图片数量：${normalized.images.length}`,
    `- 下载目录：${outDir}`,
    `- 目录规则：标题-日期-链接ID`,
    '',
    '## 关键信息',
    `- 类型：${normalized.type || '待确认'}`,
    `- 原始链接：${normalized.sourceUrl || '待确认'}`,
    `- cache_status：${normalized.cache_status ?? '待确认'}`,
    `- bktip：${pickText(normalized.bktip)}`,
    '',
    '## 资源',
    `- 头像：${normalized.author.avatar || '无'}`,
    `- 封面：${normalized.cover || '无'}`,
    `- 图片：${normalized.images.length ? normalized.images.join('\n  - ') : '无'}`,
    `- 视频：${normalized.url || '无'}`,
    `- 备用视频：${normalized.video_backup.length ? normalized.video_backup.join('\n  - ') : '无'}`,
    '',
    '## 过程/方法',
    '1. 调用 BugPk xhsjx 接口。',
    '2. 将返回结果规范化为 JSON。',
    '3. 下载头像、封面、图片，必要时下载视频。',
    '4. 生成 `report.md`、`normalized.json`、`raw.json`。',
    '',
    '## 易错点',
    '- 不要把官方示例里的 `key=value` 当成真实参数。',
    '- `desc` 就是正文，不要另找“正文字段”。',
    '- `video_backup` 可能是字符串也可能是数组。',
    '',
    '## 变更记录',
    `- ${new Date().toISOString().slice(0, 10)}：生成本地报告与媒体下载。`,
    '',
    '## 下一步',
    '- [ ] 如需更多字段，再扩展归一化规则。'
  ].join('\n');

  await writeFileSafe(path.join(outDir, 'report.md'), report);

  console.log(JSON.stringify({
    outDir,
    report: path.join(outDir, 'report.md'),
    normalized: path.join(outDir, 'normalized.json'),
    raw: path.join(outDir, 'raw.json'),
    mediaDir,
    title: normalized.title,
    author: normalized.author.name,
    desc: normalized.desc,
    images: normalized.images.length,
    downloads: downloads.length
  }, null, 2));
}

main().catch(err => {
  console.error(err?.stack || String(err));
  process.exit(1);
});
