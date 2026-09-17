# OCR Index

Input: `/Users/pmlecuong/Downloads/IMG_4884.HEIC`
Output: `application-system/data/personal_documents/2026-06-social-insurance-certificate`
Languages: `deu+eng`
Default PSM: `6`

## Rerun Summary
- Total files: 1
- OCR status: direct HEIC unsupported by batch script; temporary PNG conversion was used.
- Reviewed output: `social-insurance-certificate-2026-06.md`
- OCR quality: low; final extraction is based on visual review with OCR as secondary support.

| File path | Doc type guess | Language detected | OCR method | Quality score | Confidence | Key extracted fields | Action needed | Notes |
|---|---|---|---|---|---|---|---|---|
| `/Users/pmlecuong/Downloads/IMG_4884.HEIC` | German social insurance certificate under § 25 DEÜV | German | `sips` HEIC-to-PNG conversion + Tesseract `deu+eng` PSM 6/3 + visual review | 2 | Medium for OCR, high for visually readable core fields | Employer, recipient, social-insurance number, personnel number, DOB, reporting period, contribution group, health insurer | Keep private; verify medium-confidence fields before formal use | OCR was noisy due photo angle and dense form layout. |
