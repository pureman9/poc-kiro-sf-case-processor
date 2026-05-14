/**
 * ocr.js — Thai Document OCR & Verification Engine
 * Uses Tesseract.js (loaded via CDN in index.html)
 * Supports: Thai National ID Card, Name Change Certificate,
 *           Birth Certificate, Marriage Certificate
 */

// ── Document type definitions per intent ─────────────────────────────────────
const DOC_REQUIREMENTS = {
  'change-firstname': {
    docType:     'thai-id',
    docLabel:    'บัตรประชาชน (Thai National ID Card)',
    docLabelEn:  'Thai National ID Card',
    icon:        '🪪',
    description: 'Upload a clear photo or scan of the customer\'s Thai National ID Card (บัตรประชาชน). The name on the card must match the new name being requested.',
    acceptTypes: 'image/*,.pdf',
  },
  'change-lastname': {
    docType:     'thai-id',
    docLabel:    'บัตรประชาชน (Thai National ID Card)',
    docLabelEn:  'Thai National ID Card',
    icon:        '🪪',
    description: 'Upload a clear photo or scan of the Thai National ID Card. The last name on the card must match the new last name being requested.',
    acceptTypes: 'image/*,.pdf',
  },
  'change-title': {
    docType:     'thai-id',
    docLabel:    'บัตรประชาชน (Thai National ID Card)',
    docLabelEn:  'Thai National ID Card',
    icon:        '🪪',
    description: 'Upload the Thai National ID Card to confirm identity. Title change is auto-approved after identity verification.',
    acceptTypes: 'image/*,.pdf',
  },
  'change-fullname': {
    docType:     'name-change-cert',
    docLabel:    'ใบเปลี่ยนชื่อ-นามสกุล + บัตรประชาชน',
    docLabelEn:  'Name Change Certificate + ID Card',
    icon:        '📜',
    description: 'Upload the official Name Change Certificate (ใบเปลี่ยนชื่อ-นามสกุล) issued by the district office (อำเภอ/เขต). The new name on the certificate must match the requested change.',
    acceptTypes: 'image/*,.pdf',
  },
  'change-id': {
    docType:     'thai-id',
    docLabel:    'บัตรประชาชนใหม่ (New Thai National ID Card)',
    docLabelEn:  'New Thai National ID Card',
    icon:        '🪪',
    description: 'Upload the NEW Thai National ID Card showing the updated 13-digit ID number. The number must pass the Thai ID checksum validation.',
    acceptTypes: 'image/*,.pdf',
  },
  'change-dob': {
    docType:     'birth-cert',
    docLabel:    'สูติบัตร (Birth Certificate)',
    docLabelEn:  'Thai Birth Certificate',
    icon:        '📋',
    description: 'Upload the Thai Birth Certificate (สูติบัตร) or a certified copy. The date of birth on the certificate must match the new date being requested.',
    acceptTypes: 'image/*,.pdf',
  },
};

// ── Thai text patterns ────────────────────────────────────────────────────────
const THAI_PATTERNS = {
  // Thai National ID: 13 digits, may have spaces or dashes
  nationalId: /\b(\d[\s-]?\d{4}[\s-]?\d{5}[\s-]?\d{2}[\s-]?\d)\b/,
  nationalIdClean: /\d{13}/,

  // Thai name: คำนำหน้า + ชื่อ (Thai chars, 2+ chars each part)
  thaiName: /([ก-๙]{2,})\s+([ก-๙]{2,})/,

  // Thai title prefixes
  thaiTitle: /\b(นาย|นาง(?:สาว)?|เด็กชาย|เด็กหญิง|ด\.ต\.|ร\.ต\.|ส\.ต\.|พ\.ต\.|พ\.อ\.|นพ\.|ทพ\.|ภก\.)\b/,

  // ID card keyword markers
  idCardKeyword: /บัตรประจำตัวประชาชน|THAI\s*NATIONAL\s*ID|Identification\s*Number/i,

  // Name change certificate keywords
  nameChangeCert: /ใบเปลี่ยน(?:ชื่อ|นามสกุล|ชื่อ-นามสกุล)|เปลี่ยนชื่อ|เปลี่ยนนามสกุล|สำนักทะเบียน|อำเภอ|เขต/,

  // Birth certificate keywords
  birthCert: /สูติบัตร|ใบสูติบัตร|วันเกิด|เกิดเมื่อ|BIRTH\s*CERTIFICATE/i,

  // Marriage certificate keywords
  marriageCert: /ทะเบียนสมรส|ใบสำคัญการสมรส|MARRIAGE\s*CERTIFICATE/i,

  // Date patterns (Thai Buddhist Era and CE)
  thaiDate: /(\d{1,2})\s*(?:มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s*(\d{4})/,
  isoDate: /(\d{4})-(\d{2})-(\d{2})/,

  // Expiry date
  expiryDate: /(?:วันหมดอายุ|Expiry|Expires?)[:\s]+(.+)/i,
};

// ── Thai ID checksum validation ───────────────────────────────────────────────
function validateThaiIdChecksum(id) {
  const digits = id.replace(/\D/g, '');
  if (digits.length !== 13) return false;
  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(digits[i]) * (13 - i);
  }
  const checkDigit = (11 - (sum % 11)) % 10;
  return checkDigit === parseInt(digits[12]);
}

// ── Extract Thai month number ─────────────────────────────────────────────────
const THAI_MONTHS = {
  'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4,
  'พฤษภาคม': 5, 'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8,
  'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12,
};

function thaiDateToISO(thaiDateStr) {
  const m = thaiDateStr.match(/(\d{1,2})\s*([\u0E00-\u0E7F]+)\s*(\d{4})/);
  if (!m) return null;
  const day   = m[1].padStart(2, '0');
  const month = String(THAI_MONTHS[m[2]] || 0).padStart(2, '0');
  let year    = parseInt(m[3]);
  if (year > 2400) year -= 543; // Convert Buddhist Era to CE
  return `${year}-${month}-${day}`;
}

// ── Image realism analysis (canvas-based, runs before OCR) ───────────────────
const ImageAnalysis = {

  /**
   * Analyse an image file for document realism signals.
   * Returns { checks, score, ok }
   * Runs entirely in-browser via Canvas API — no server needed.
   */
  async analyse(imageFile) {
    return new Promise((resolve) => {
      const img = new Image();
      const url = URL.createObjectURL(imageFile);
      img.onload = () => {
        URL.revokeObjectURL(url);
        const checks = [];

        const w = img.naturalWidth;
        const h = img.naturalHeight;

        // ── 1. Minimum resolution ──────────────────────────────────────────
        const minPx = 300;
        const hasMinRes = w >= minPx && h >= minPx;
        checks.push({
          pass: hasMinRes, critical: true,
          label: 'Image Resolution',
          detail: hasMinRes
            ? `${w}×${h}px — sufficient resolution ✓`
            : `${w}×${h}px — too low. Minimum ${minPx}×${minPx}px required for reliable OCR`,
        });

        // ── 2. Aspect ratio (Thai ID card is 85.6×54mm → ~1.585:1) ────────
        const ratio = w / h;
        const landscape = ratio > 1;
        // Accept landscape (card held normally) or portrait (card rotated)
        // Thai ID: ~1.58 landscape. Allow 1.3–1.9 or 0.53–0.77 (portrait)
        const validRatio = (ratio >= 1.25 && ratio <= 2.0) || (ratio >= 0.5 && ratio <= 0.8);
        checks.push({
          pass: validRatio, critical: false,
          label: 'Document Aspect Ratio',
          detail: validRatio
            ? `Ratio ${ratio.toFixed(2)} — consistent with ID card format ✓`
            : `Ratio ${ratio.toFixed(2)} — unusual for an ID card (expected ~1.58 landscape or ~0.63 portrait)`,
        });

        // ── Canvas pixel analysis ──────────────────────────────────────────
        const canvas  = document.createElement('canvas');
        // Sample at max 200×200 for speed
        const sampleW = Math.min(w, 200);
        const sampleH = Math.min(h, 200);
        canvas.width  = sampleW;
        canvas.height = sampleH;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, sampleW, sampleH);
        const data = ctx.getImageData(0, 0, sampleW, sampleH).data;

        // ── 3. Not blank / not solid color ────────────────────────────────
        let rSum = 0, gSum = 0, bSum = 0;
        let rSqSum = 0, gSqSum = 0, bSqSum = 0;
        const n = sampleW * sampleH;
        for (let i = 0; i < data.length; i += 4) {
          const r = data[i], g = data[i+1], b = data[i+2];
          rSum += r; gSum += g; bSum += b;
          rSqSum += r*r; gSqSum += g*g; bSqSum += b*b;
        }
        const rMean = rSum / n, gMean = gSum / n, bMean = bSum / n;
        const rVar  = rSqSum/n - rMean*rMean;
        const gVar  = gSqSum/n - gMean*gMean;
        const bVar  = bSqSum/n - bMean*bMean;
        const avgVariance = (rVar + gVar + bVar) / 3;

        const hasContent = avgVariance > 200; // solid/blank images have near-zero variance
        checks.push({
          pass: hasContent, critical: true,
          label: 'Image Content',
          detail: hasContent
            ? `Color variance ${avgVariance.toFixed(0)} — image has visible content ✓`
            : `Color variance ${avgVariance.toFixed(0)} — image appears blank or solid color`,
        });

        // ── 4. Not too dark / not overexposed ─────────────────────────────
        const brightness = (rMean + gMean + bMean) / 3;
        const goodBrightness = brightness >= 40 && brightness <= 230;
        checks.push({
          pass: goodBrightness, critical: false,
          label: 'Image Brightness',
          detail: goodBrightness
            ? `Brightness ${brightness.toFixed(0)}/255 — well-lit document ✓`
            : brightness < 40
              ? `Brightness ${brightness.toFixed(0)}/255 — image too dark. Use better lighting`
              : `Brightness ${brightness.toFixed(0)}/255 — image overexposed. Reduce glare`,
        });

        // ── 5. Edge density (documents have text/borders = many edges) ────
        // Simple Sobel-like: count pixels with high gradient vs neighbours
        let edgeCount = 0;
        const threshold = 30;
        for (let y = 1; y < sampleH - 1; y++) {
          for (let x = 1; x < sampleW - 1; x++) {
            const idx = (y * sampleW + x) * 4;
            const idxR = (y * sampleW + x + 1) * 4;
            const idxD = ((y+1) * sampleW + x) * 4;
            const grayC = (data[idx]   + data[idx+1]   + data[idx+2])   / 3;
            const grayR = (data[idxR]  + data[idxR+1]  + data[idxR+2])  / 3;
            const grayD = (data[idxD]  + data[idxD+1]  + data[idxD+2])  / 3;
            if (Math.abs(grayC - grayR) > threshold || Math.abs(grayC - grayD) > threshold) {
              edgeCount++;
            }
          }
        }
        const edgeDensity = edgeCount / n;
        // Documents typically have 5–40% edge pixels. Photos/blank have <3% or >50%
        const goodEdgeDensity = edgeDensity >= 0.03 && edgeDensity <= 0.55;
        checks.push({
          pass: goodEdgeDensity, critical: false,
          label: 'Document Structure',
          detail: goodEdgeDensity
            ? `Edge density ${(edgeDensity*100).toFixed(1)}% — consistent with a document containing text ✓`
            : edgeDensity < 0.03
              ? `Edge density ${(edgeDensity*100).toFixed(1)}% — very few edges detected. Ensure document text is visible`
              : `Edge density ${(edgeDensity*100).toFixed(1)}% — very noisy image. Ensure document is flat and in focus`,
        });

        // ── 6. Thai ID card color signature ───────────────────────────────
        // Thai ID cards have a distinctive light blue/teal background
        // Check if there's a meaningful blue-green component
        const blueGreenRatio = (gMean + bMean) / (rMean + 1);
        const hasIdColors = blueGreenRatio >= 0.8; // blue/green dominant or balanced
        checks.push({
          pass: hasIdColors, critical: false,
          label: 'Document Color Profile',
          detail: hasIdColors
            ? `Color profile (B/G ratio ${blueGreenRatio.toFixed(2)}) — consistent with Thai ID card ✓`
            : `Color profile (B/G ratio ${blueGreenRatio.toFixed(2)}) — may not be a Thai ID card. Expected blue-teal tones`,
        });

        const passed = checks.filter(c => c.pass).length;
        const total  = checks.length;
        const score  = Math.round((passed / total) * 100);
        const criticalFail = checks.some(c => c.critical && !c.pass);
        const ok = score >= 60 && !criticalFail;

        resolve({ checks, score, ok, width: w, height: h });
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        resolve({
          checks: [{ pass: false, critical: true, label: 'Image Load', detail: 'Could not load image file' }],
          score: 0, ok: false,
        });
      };
      img.src = url;
    });
  },
};

// ── Main OCR + verification function ─────────────────────────────────────────
const OCR = {

  worker: null,
  _initPromise: null,

  /** Check if Tesseract is available */
  isAvailable() {
    return typeof Tesseract !== 'undefined' && !window._tesseractLoadFailed;
  },

  async init() {
    if (!this.isAvailable()) throw new Error('Tesseract.js not loaded — OCR unavailable. Check internet connection or use Skip Verification.');
    if (this.worker) return;
    if (this._initPromise) return this._initPromise;

    this._initPromise = (async () => {
      this.worker = await Tesseract.createWorker(['tha', 'eng'], 1, {
        logger: m => {
          if (m.status === 'recognizing text') {
            const pct = Math.round(m.progress * 100);
            const bar = document.getElementById('ocr-progress-bar');
            const lbl = document.getElementById('ocr-progress-label');
            if (bar) bar.style.width = `${pct}%`;
            if (lbl) lbl.textContent = `Recognizing text... ${pct}%`;
          }
        },
      });
    })();

    try {
      await this._initPromise;
    } catch (e) {
      this._initPromise = null;
      this.worker = null;
      throw e;
    }
  },

  async terminate() {
    if (this.worker) {
      await this.worker.terminate();
      this.worker = null;
    }
  },

  /**
   * Run OCR on an image file and return extracted text
   */
  async extractText(imageFile) {
    await this.init();
    const url = URL.createObjectURL(imageFile);
    try {
      const { data: { text } } = await this.worker.recognize(url);
      return text;
    } finally {
      URL.revokeObjectURL(url);
    }
  },

  /**
   * Verify a document for a given intent and new values.
   * Step 1: Image realism analysis (canvas — instant)
   * Step 2: OCR text extraction + pattern checks
   * Returns: { ok, score, imageScore, ocrScore, checks, extractedFields, warnings, rawText }
   */
  async verifyDocument(intentKey, imageFile, newValues) {
    const req = DOC_REQUIREMENTS[intentKey];
    if (!req) return { ok: false, score: 0, checks: [], extractedFields: {}, warnings: ['Unknown intent'] };

    // ── Phase 1: Image realism (canvas, no network) ────────────────────────
    const imgAnalysis = await ImageAnalysis.analyse(imageFile);

    // If image is fundamentally bad, skip OCR
    if (!imgAnalysis.ok && imgAnalysis.score < 40) {
      return {
        ok: false,
        score: imgAnalysis.score,
        imageScore: imgAnalysis.score,
        ocrScore: 0,
        checks: imgAnalysis.checks,
        extractedFields: {},
        warnings: ['Image quality too low for OCR'],
        rawText: '',
      };
    }

    // ── Phase 2: OCR text extraction ───────────────────────────────────────
    let rawText = '';
    let ocrFailed = false;
    try {
      rawText = await this.extractText(imageFile);
    } catch (e) {
      ocrFailed = true;
    }

    const ocrChecks = [];
    const extractedFields = {};
    const warnings = [];

    if (ocrFailed) {
      ocrChecks.push({ pass: false, critical: true, label: 'OCR Processing',
        detail: 'Could not read text from image. Ensure the image is clear and well-lit.' });
    } else {
      switch (req.docType) {
        case 'thai-id':
          this._checkIdCard(rawText, newValues, intentKey, ocrChecks, extractedFields, warnings);
          break;
        case 'name-change-cert':
          this._checkNameChangeCert(rawText, newValues, ocrChecks, extractedFields, warnings);
          break;
        case 'birth-cert':
          this._checkBirthCert(rawText, newValues, ocrChecks, extractedFields, warnings);
          break;
      }
    }

    // ── Combine scores: image 40% weight, OCR 60% weight ──────────────────
    const ocrPassed = ocrChecks.filter(c => c.pass).length;
    const ocrTotal  = ocrChecks.length || 1;
    const ocrScore  = Math.round((ocrPassed / ocrTotal) * 100);

    const combinedScore = Math.round(imgAnalysis.score * 0.4 + ocrScore * 0.6);

    const allChecks    = [...imgAnalysis.checks, ...ocrChecks];
    const criticalFail = allChecks.some(c => c.critical && !c.pass);
    const ok           = combinedScore >= 60 && !criticalFail;

    return {
      ok,
      score:      combinedScore,
      imageScore: imgAnalysis.score,
      ocrScore,
      checks:     allChecks,
      extractedFields,
      warnings,
      rawText,
    };
  },

  // ── ID Card checks ──────────────────────────────────────────────────────────
  _checkIdCard(text, newValues, intentKey, checks, extractedFields, warnings) {
    // 1. Document type keyword
    const hasIdKeyword = THAI_PATTERNS.idCardKeyword.test(text);
    checks.push({
      pass: hasIdKeyword, critical: true,
      label: 'Document Type',
      detail: hasIdKeyword
        ? 'Thai National ID Card keyword detected'
        : 'Could not confirm this is a Thai National ID Card — keyword "บัตรประจำตัวประชาชน" not found',
    });

    // 2. Extract and validate 13-digit ID number
    const idMatch = text.match(THAI_PATTERNS.nationalId) || text.match(THAI_PATTERNS.nationalIdClean);
    if (idMatch) {
      const rawId = idMatch[0].replace(/\D/g, '');
      extractedFields.nationalId = rawId;
      const checksumOk = validateThaiIdChecksum(rawId);
      checks.push({
        pass: checksumOk, critical: true,
        label: 'ID Number Checksum',
        detail: checksumOk
          ? `ID number ${rawId.replace(/(\d)(\d{4})(\d{5})(\d{2})(\d)/, '$1-$2-$3-$4-$5')} — checksum valid ✓`
          : `ID number found but checksum invalid — may be OCR misread`,
      });

      // If intent is change-id, cross-check with new value
      if (intentKey === 'change-id' && newValues.nationalId) {
        const match = rawId === newValues.nationalId.replace(/\D/g, '');
        checks.push({
          pass: match, critical: true,
          label: 'New ID Number Match',
          detail: match
            ? `New ID number matches document: ${rawId}`
            : `New ID entered (${newValues.nationalId}) does not match document (${rawId})`,
        });
      }
    } else {
      checks.push({
        pass: false, critical: true,
        label: 'ID Number Extraction',
        detail: 'Could not extract 13-digit ID number from document',
      });
      warnings.push('ID number not found — image may be blurry or cropped');
    }

    // 3. Extract Thai name
    const nameMatch = text.match(THAI_PATTERNS.thaiName);
    if (nameMatch) {
      extractedFields.firstName = nameMatch[1];
      extractedFields.lastName  = nameMatch[2];

      // Cross-check new name values
      if (intentKey === 'change-firstname' && newValues.firstName) {
        const match = this._nameSimilar(nameMatch[1], newValues.firstName);
        checks.push({
          pass: match, critical: false,
          label: 'First Name on Document',
          detail: match
            ? `New first name "${newValues.firstName}" found on document ✓`
            : `New first name "${newValues.firstName}" not clearly found on document (extracted: "${nameMatch[1]}")`,
        });
      }
      if (intentKey === 'change-lastname' && newValues.lastName) {
        const match = this._nameSimilar(nameMatch[2], newValues.lastName);
        checks.push({
          pass: match, critical: false,
          label: 'Last Name on Document',
          detail: match
            ? `New last name "${newValues.lastName}" found on document ✓`
            : `New last name "${newValues.lastName}" not clearly found on document (extracted: "${nameMatch[2]}")`,
        });
      }
    } else {
      checks.push({
        pass: false, critical: false,
        label: 'Name Extraction',
        detail: 'Could not extract Thai name from document — OCR may need clearer image',
      });
    }

    // 4. Title check
    const titleMatch = text.match(THAI_PATTERNS.thaiTitle);
    if (titleMatch) {
      extractedFields.title = titleMatch[1];
      if (intentKey === 'change-title' && newValues.title) {
        const match = titleMatch[1] === newValues.title;
        checks.push({
          pass: match, critical: false,
          label: 'Title on Document',
          detail: match
            ? `Title "${newValues.title}" matches document ✓`
            : `Title on document: "${titleMatch[1]}", requested: "${newValues.title}"`,
        });
      }
    }

    // 5. Expiry check (warn if expired)
    const expiryMatch = text.match(THAI_PATTERNS.expiryDate);
    if (expiryMatch) {
      extractedFields.expiry = expiryMatch[1].trim();
      checks.push({
        pass: true, critical: false,
        label: 'Document Expiry',
        detail: `Expiry date found: ${extractedFields.expiry}`,
      });
    }
  },

  // ── Name Change Certificate checks ─────────────────────────────────────────
  _checkNameChangeCert(text, newValues, checks, extractedFields, warnings) {
    // 1. Document type
    const hasCertKeyword = THAI_PATTERNS.nameChangeCert.test(text);
    checks.push({
      pass: hasCertKeyword, critical: true,
      label: 'Document Type',
      detail: hasCertKeyword
        ? 'Name Change Certificate keywords detected (ใบเปลี่ยนชื่อ/นามสกุล)'
        : 'Could not confirm this is a Name Change Certificate — required keywords not found',
    });

    // 2. Issuing authority (อำเภอ/เขต)
    const hasAuthority = /อำเภอ|เขต|สำนักทะเบียน/.test(text);
    checks.push({
      pass: hasAuthority, critical: false,
      label: 'Issuing Authority',
      detail: hasAuthority
        ? 'District office (อำเภอ/เขต) reference found ✓'
        : 'Issuing authority not detected — ensure full document is visible',
    });

    // 3. New name on certificate
    const nameMatch = text.match(THAI_PATTERNS.thaiName);
    if (nameMatch) {
      extractedFields.firstName = nameMatch[1];
      extractedFields.lastName  = nameMatch[2];

      if (newValues.firstName) {
        const match = this._nameSimilar(nameMatch[1], newValues.firstName);
        checks.push({
          pass: match, critical: true,
          label: 'New First Name on Certificate',
          detail: match
            ? `New first name "${newValues.firstName}" found on certificate ✓`
            : `New first name "${newValues.firstName}" not found (extracted: "${nameMatch[1]}")`,
        });
      }
      if (newValues.lastName) {
        const match = this._nameSimilar(nameMatch[2], newValues.lastName);
        checks.push({
          pass: match, critical: true,
          label: 'New Last Name on Certificate',
          detail: match
            ? `New last name "${newValues.lastName}" found on certificate ✓`
            : `New last name "${newValues.lastName}" not found (extracted: "${nameMatch[2]}")`,
        });
      }
    } else {
      checks.push({
        pass: false, critical: true,
        label: 'Name Extraction',
        detail: 'Could not extract Thai name from certificate',
      });
    }

    // 4. Date on certificate
    const dateMatch = text.match(THAI_PATTERNS.thaiDate);
    if (dateMatch) {
      extractedFields.issueDate = dateMatch[0];
      checks.push({
        pass: true, critical: false,
        label: 'Issue Date',
        detail: `Certificate date found: ${dateMatch[0]}`,
      });
    }
  },

  // ── Birth Certificate checks ────────────────────────────────────────────────
  _checkBirthCert(text, newValues, checks, extractedFields, warnings) {
    // 1. Document type
    const hasBirthKeyword = THAI_PATTERNS.birthCert.test(text);
    checks.push({
      pass: hasBirthKeyword, critical: true,
      label: 'Document Type',
      detail: hasBirthKeyword
        ? 'Birth Certificate keywords detected (สูติบัตร)'
        : 'Could not confirm this is a Birth Certificate — "สูติบัตร" keyword not found',
    });

    // 2. Date of birth extraction
    const dateMatch = text.match(THAI_PATTERNS.thaiDate);
    if (dateMatch) {
      const isoDate = thaiDateToISO(dateMatch[0]);
      extractedFields.dob = isoDate || dateMatch[0];
      if (newValues.dob && isoDate) {
        const match = isoDate === newValues.dob;
        checks.push({
          pass: match, critical: true,
          label: 'Date of Birth Match',
          detail: match
            ? `Date of birth ${isoDate} matches requested change ✓`
            : `Document date: ${isoDate}, requested: ${newValues.dob}`,
        });
      } else {
        checks.push({
          pass: true, critical: false,
          label: 'Date of Birth Found',
          detail: `Date found on document: ${dateMatch[0]}`,
        });
      }
    } else {
      // Try ISO date
      const isoMatch = text.match(THAI_PATTERNS.isoDate);
      if (isoMatch) {
        extractedFields.dob = isoMatch[0];
        checks.push({ pass: true, critical: false, label: 'Date Found', detail: `Date: ${isoMatch[0]}` });
      } else {
        checks.push({
          pass: false, critical: true,
          label: 'Date of Birth Extraction',
          detail: 'Could not extract date of birth from document',
        });
      }
    }

    // 3. Name on birth cert
    const nameMatch = text.match(THAI_PATTERNS.thaiName);
    if (nameMatch) {
      extractedFields.name = `${nameMatch[1]} ${nameMatch[2]}`;
      checks.push({ pass: true, critical: false, label: 'Name Found', detail: `Name on document: ${extractedFields.name}` });
    }
  },

  // ── Fuzzy Thai name comparison ──────────────────────────────────────────────
  _nameSimilar(extracted, entered) {
    if (!extracted || !entered) return false;
    const a = extracted.trim().replace(/\s+/g, '');
    const b = entered.trim().replace(/\s+/g, '');
    if (a === b) return true;
    // Allow if one contains the other (OCR may add/miss chars)
    if (a.includes(b) || b.includes(a)) return true;
    // Allow if 80%+ chars match (simple similarity)
    const longer  = a.length > b.length ? a : b;
    const shorter = a.length > b.length ? b : a;
    let matches = 0;
    for (const ch of shorter) { if (longer.includes(ch)) matches++; }
    return matches / longer.length >= 0.75;
  },
};
