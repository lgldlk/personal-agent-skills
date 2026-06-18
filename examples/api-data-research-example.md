# API Data Research Example

This is a synthetic example that demonstrates the output shape of `api-data-research`.

## Conclusions

- The skill separates official APIs, third-party data vendors, and browser/scraping based access.
- Field availability is expressed as evidence levels instead of vague capability claims.
- Price, access scope, and operating-year basis are shown in the same matrix so readers can judge tradeoffs.

## 数据维度能力矩阵

| Option | Operating basis | Full text | Images / links | Likes / metrics | Price | Confidence | Notes |
|---|---:|---|---|---|---|---|---|
| Official API | API docs year | Own account only | Schema dependent | Account analytics | Free / review | High | Best for compliant owned-data workflows |
| Third-party API | Founded / docs year | Public lookup | `media_url`, links | Vendor fields | Credits / quote | Medium | Best for API vendor comparison |
| Browser workflow | Tool release year | Rendered page | DOM images, anchors | Visible counts | Infra cost | Low-medium | Needs policy and legal review |

## Field Alignment

| Dimension | Official API | Third-party API | Browser workflow |
|---|---|---|---|
| Body text | Documented fields only | Confirm via schema/sample | Extracted from page |
| Media | Endpoint-dependent | Usually `media_url` style fields | DOM image URLs |
| Links | Entity fields when documented | Vendor-specific fields | DOM anchors |
| Likes | Account-owned analytics or public metrics | Vendor-specific metric fields | Visible public count |
| Views | Often restricted | Rare; verify docs | Usually unavailable |
