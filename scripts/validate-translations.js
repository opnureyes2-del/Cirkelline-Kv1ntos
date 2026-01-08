#!/usr/bin/env node

/**
 * Validate translation files for:
 * - Valid JSON structure
 * - Placeholder consistency
 * - Missing translations
 * - RTL characters in Arabic
 *
 * Usage: node scripts/validate-translations.js
 */

const fs = require('fs');
const path = require('path');

const LOCALES_DIR = path.join(__dirname, '../locales');
const LANGUAGES = ['da', 'en', 'sv', 'de', 'ar'];

let errors = 0;
let warnings = 0;

console.log('='.repeat(50));
console.log('Validating Translation Files');
console.log('='.repeat(50));
console.log('');

// Load English (source) for comparison
const enPath = path.join(LOCALES_DIR, 'en/messages.json');
let enData;

try {
  enData = JSON.parse(fs.readFileSync(enPath, 'utf8'));
} catch (error) {
  console.error(`❌ Failed to load English source: ${error.message}`);
  process.exit(1);
}

function getAllKeys(obj, prefix = '') {
  let keys = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'object' && value !== null) {
      keys = keys.concat(getAllKeys(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

function getValue(obj, keyPath) {
  return keyPath.split('.').reduce((acc, key) => acc?.[key], obj);
}

function getPlaceholders(str) {
  const regex = /\{([^}]+)\}/g;
  const matches = [];
  let match;
  while ((match = regex.exec(str)) !== null) {
    matches.push(match[1]);
  }
  return matches;
}

function hasRTLCharacters(str) {
  // Arabic Unicode range
  return /[\u0600-\u06FF]/.test(str);
}

function hasBoldItalic(str) {
  return /<b>|<strong>|<i>|<em>|\*\*|__/.test(str);
}

function validateLanguage(lang) {
  console.log(`\n${'='.repeat(50)}`);
  console.log(`Validating ${lang.toUpperCase()}`);
  console.log('='.repeat(50));

  const filePath = path.join(LOCALES_DIR, `${lang}/messages.json`);

  // Check file exists
  if (!fs.existsSync(filePath)) {
    console.error(`❌ File not found: ${filePath}`);
    errors++;
    return;
  }

  // Check valid JSON
  let data;
  try {
    data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    console.error(`❌ Invalid JSON: ${error.message}`);
    errors++;
    return;
  }

  // Get all keys
  const enKeys = getAllKeys(enData);
  const langKeys = getAllKeys(data);

  console.log(`Total strings: ${langKeys.length}/${enKeys.length}`);

  // Check for missing keys
  const missingKeys = enKeys.filter(k => !langKeys.includes(k));
  if (missingKeys.length > 0) {
    console.warn(`\n⚠️  Missing ${missingKeys.length} translations:`);
    missingKeys.slice(0, 10).forEach(k => console.warn(`   - ${k}`));
    if (missingKeys.length > 10) {
      console.warn(`   ... and ${missingKeys.length - 10} more`);
    }
    warnings += missingKeys.length;
  } else {
    console.log('✓ All translations present');
  }

  // Check for extra keys (not in English)
  const extraKeys = langKeys.filter(k => !enKeys.includes(k));
  if (extraKeys.length > 0) {
    console.warn(`\n⚠️  Extra keys (not in English):`);
    extraKeys.forEach(k => console.warn(`   - ${k}`));
    warnings += extraKeys.length;
  }

  // Check placeholder consistency
  let placeholderErrors = 0;
  enKeys.forEach(key => {
    const enValue = getValue(enData, key);
    const langValue = getValue(data, key);

    if (!langValue) return; // Already reported as missing

    const enPlaceholders = getPlaceholders(enValue);
    const langPlaceholders = getPlaceholders(langValue);

    if (enPlaceholders.length !== langPlaceholders.length) {
      console.error(`\n❌ Placeholder mismatch in "${key}":`);
      console.error(`   EN:  ${enValue}`);
      console.error(`   ${lang.toUpperCase()}: ${langValue}`);
      console.error(`   Expected: {${enPlaceholders.join('}, {')}}`);
      console.error(`   Found: {${langPlaceholders.join('}, {')}}`);
      placeholderErrors++;
      errors++;
    } else if (enPlaceholders.length > 0) {
      // Check placeholder names match (order can differ)
      const missing = enPlaceholders.filter(p => !langPlaceholders.includes(p));
      const extra = langPlaceholders.filter(p => !enPlaceholders.includes(p));

      if (missing.length > 0 || extra.length > 0) {
        console.error(`\n❌ Placeholder name mismatch in "${key}":`);
        if (missing.length > 0) {
          console.error(`   Missing: {${missing.join('}, {')}}`);
        }
        if (extra.length > 0) {
          console.error(`   Extra: {${extra.join('}, {')}}`);
        }
        console.error(`   EN:  ${enValue}`);
        console.error(`   ${lang.toUpperCase()}: ${langValue}`);
        placeholderErrors++;
        errors++;
      }
    }
  });

  if (placeholderErrors === 0) {
    console.log('✓ All placeholders valid');
  } else {
    console.error(`❌ ${placeholderErrors} placeholder errors found`);
  }

  // Language-specific checks
  if (lang === 'ar') {
    console.log('\n--- Arabic (RTL) Specific Checks ---');

    // Check for RTL characters
    let hasArabic = false;
    let boldItalicCount = 0;

    langKeys.forEach(key => {
      const value = getValue(data, key);
      if (hasRTLCharacters(value)) {
        hasArabic = true;
      }
      if (hasBoldItalic(value)) {
        console.warn(`⚠️  Bold/italic in "${key}" (not recommended for Arabic)`);
        console.warn(`   Value: ${value}`);
        boldItalicCount++;
        warnings++;
      }
    });

    if (hasArabic) {
      console.log('✓ Contains Arabic characters');
    } else {
      console.warn('⚠️  No Arabic characters detected');
      console.warn('   Possible machine translation or incorrect encoding');
      warnings++;
    }

    if (boldItalicCount === 0) {
      console.log('✓ No bold/italic formatting (good for Arabic)');
    }
  }

  if (lang === 'de') {
    console.log('\n--- German Specific Checks ---');

    // Check length (German typically 30% longer)
    let longStrings = 0;
    enKeys.forEach(key => {
      const enValue = getValue(enData, key);
      const deValue = getValue(data, key);
      if (enValue && deValue) {
        const lengthRatio = deValue.length / enValue.length;
        if (lengthRatio > 1.5) {
          console.warn(`⚠️  Very long German translation in "${key}"`);
          console.warn(`   EN: ${enValue} (${enValue.length} chars)`);
          console.warn(`   DE: ${deValue} (${deValue.length} chars, +${Math.round((lengthRatio - 1) * 100)}%)`);
          longStrings++;
          warnings++;
        }
      }
    });

    if (longStrings === 0) {
      console.log('✓ No extremely long translations');
    }
  }

  console.log(`\n${lang.toUpperCase()} Summary: ${langKeys.length} translations checked`);
}

// Validate all languages
console.log('Source language: English');
console.log(`Total source strings: ${getAllKeys(enData).length}\n`);

LANGUAGES.forEach(lang => {
  if (lang === 'en') {
    // Skip validation for source language
    return;
  }
  validateLanguage(lang);
});

// Final summary
console.log('\n' + '='.repeat(50));
console.log('Validation Summary');
console.log('='.repeat(50));
console.log(`Errors:   ${errors}`);
console.log(`Warnings: ${warnings}`);

if (errors > 0) {
  console.error('\n❌ Validation FAILED!');
  console.error(`Fix ${errors} critical errors before proceeding.`);
  process.exit(1);
} else if (warnings > 0) {
  console.warn('\n⚠️  Validation passed with warnings');
  console.warn(`Review ${warnings} warnings for quality improvement.`);
  process.exit(0);
} else {
  console.log('\n✓ All translations valid!');
  console.log('Ready for deployment.');
  process.exit(0);
}
