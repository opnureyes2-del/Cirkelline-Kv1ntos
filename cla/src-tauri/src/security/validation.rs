// Input validation module for Cirkelline Local Agent
// Prevents injection attacks and ensures data integrity

use std::collections::HashSet;
use regex::Regex;
use once_cell::sync::Lazy;

/// Input validator
pub struct InputValidator {
    max_text_length: usize,
    max_path_length: usize,
    allowed_file_extensions: HashSet<String>,
}

impl Default for InputValidator {
    fn default() -> Self {
        Self {
            max_text_length: 100_000, // 100KB max text
            max_path_length: 4096,
            allowed_file_extensions: [
                "txt", "md", "json", "yaml", "yml",
                "png", "jpg", "jpeg", "gif", "webp", "bmp",
                "wav", "mp3", "ogg", "flac", "m4a",
                "pdf", "doc", "docx", "xls", "xlsx",
            ].iter().map(|s| s.to_string()).collect(),
        }
    }
}

impl InputValidator {
    pub fn new() -> Self {
        Self::default()
    }

    /// Validate text input
    pub fn validate_text(&self, text: &str) -> Result<(), ValidationError> {
        if text.is_empty() {
            return Err(ValidationError::Empty);
        }

        if text.len() > self.max_text_length {
            return Err(ValidationError::TooLong {
                max: self.max_text_length,
                actual: text.len(),
            });
        }

        // Check for null bytes
        if text.contains('\0') {
            return Err(ValidationError::InvalidCharacters);
        }

        Ok(())
    }

    /// Validate file path
    pub fn validate_path(&self, path: &str) -> Result<(), ValidationError> {
        if path.is_empty() {
            return Err(ValidationError::Empty);
        }

        if path.len() > self.max_path_length {
            return Err(ValidationError::TooLong {
                max: self.max_path_length,
                actual: path.len(),
            });
        }

        // Check for path traversal attempts
        if path.contains("..") {
            return Err(ValidationError::PathTraversal);
        }

        // Check for null bytes
        if path.contains('\0') {
            return Err(ValidationError::InvalidCharacters);
        }

        // Validate file extension if present
        if let Some(ext) = std::path::Path::new(path)
            .extension()
            .and_then(|e| e.to_str())
        {
            if !self.allowed_file_extensions.contains(&ext.to_lowercase()) {
                return Err(ValidationError::DisallowedExtension(ext.to_string()));
            }
        }

        Ok(())
    }

    /// Validate email format
    pub fn validate_email(&self, email: &str) -> Result<(), ValidationError> {
        static EMAIL_REGEX: Lazy<Regex> = Lazy::new(|| {
            Regex::new(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$").unwrap()
        });

        if !EMAIL_REGEX.is_match(email) {
            return Err(ValidationError::InvalidEmail);
        }

        Ok(())
    }

    /// Validate URL format
    pub fn validate_url(&self, url: &str) -> Result<(), ValidationError> {
        // Basic URL validation
        if !url.starts_with("http://") && !url.starts_with("https://") {
            return Err(ValidationError::InvalidUrl);
        }

        // Check for dangerous characters
        if url.contains('<') || url.contains('>') || url.contains('"') {
            return Err(ValidationError::InvalidCharacters);
        }

        Ok(())
    }

    /// Validate JSON structure
    pub fn validate_json(&self, json: &str) -> Result<serde_json::Value, ValidationError> {
        self.validate_text(json)?;

        serde_json::from_str(json).map_err(|e| ValidationError::InvalidJson(e.to_string()))
    }

    /// Sanitize text for safe storage
    pub fn sanitize_text(&self, text: &str) -> String {
        text.chars()
            .filter(|c| !c.is_control() || *c == '\n' || *c == '\t' || *c == '\r')
            .take(self.max_text_length)
            .collect()
    }

    /// Sanitize filename
    pub fn sanitize_filename(&self, filename: &str) -> String {
        filename
            .chars()
            .filter(|c| c.is_alphanumeric() || *c == '.' || *c == '-' || *c == '_')
            .take(255)
            .collect()
    }

    /// Add allowed extension
    pub fn add_extension(&mut self, ext: &str) {
        self.allowed_file_extensions.insert(ext.to_lowercase());
    }

    /// Set max text length
    pub fn set_max_text_length(&mut self, max: usize) {
        self.max_text_length = max;
    }
}

/// Validation errors
#[derive(Debug, Clone)]
pub enum ValidationError {
    Empty,
    TooLong { max: usize, actual: usize },
    TooShort { min: usize, actual: usize },
    InvalidCharacters,
    InvalidEmail,
    InvalidUrl,
    InvalidJson(String),
    PathTraversal,
    DisallowedExtension(String),
    Custom(String),
}

impl std::fmt::Display for ValidationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Empty => write!(f, "Input cannot be empty"),
            Self::TooLong { max, actual } => {
                write!(f, "Input too long: {} characters (max {})", actual, max)
            }
            Self::TooShort { min, actual } => {
                write!(f, "Input too short: {} characters (min {})", actual, min)
            }
            Self::InvalidCharacters => write!(f, "Input contains invalid characters"),
            Self::InvalidEmail => write!(f, "Invalid email format"),
            Self::InvalidUrl => write!(f, "Invalid URL format"),
            Self::InvalidJson(msg) => write!(f, "Invalid JSON: {}", msg),
            Self::PathTraversal => write!(f, "Path traversal detected"),
            Self::DisallowedExtension(ext) => write!(f, "File extension not allowed: {}", ext),
            Self::Custom(msg) => write!(f, "{}", msg),
        }
    }
}

impl std::error::Error for ValidationError {}

/// Validate memory content
pub fn validate_memory_content(content: &str) -> Result<(), ValidationError> {
    let validator = InputValidator::default();
    validator.validate_text(content)?;

    // Additional memory-specific validation
    if content.len() < 3 {
        return Err(ValidationError::TooShort {
            min: 3,
            actual: content.len(),
        });
    }

    Ok(())
}

/// Validate session context
pub fn validate_session_context(context: &serde_json::Value) -> Result<(), ValidationError> {
    // Check context isn't too deeply nested (prevent DoS)
    fn check_depth(value: &serde_json::Value, depth: usize) -> Result<(), ValidationError> {
        if depth > 10 {
            return Err(ValidationError::Custom("JSON too deeply nested".to_string()));
        }

        match value {
            serde_json::Value::Object(map) => {
                for v in map.values() {
                    check_depth(v, depth + 1)?;
                }
            }
            serde_json::Value::Array(arr) => {
                for v in arr {
                    check_depth(v, depth + 1)?;
                }
            }
            _ => {}
        }

        Ok(())
    }

    check_depth(context, 0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_text() {
        let validator = InputValidator::default();

        assert!(validator.validate_text("Hello, World!").is_ok());
        assert!(validator.validate_text("").is_err());
        assert!(validator.validate_text("test\0null").is_err());
    }

    #[test]
    fn test_validate_path() {
        let validator = InputValidator::default();

        assert!(validator.validate_path("/home/user/document.txt").is_ok());
        assert!(validator.validate_path("/home/../etc/passwd").is_err());
        assert!(validator.validate_path("/test.exe").is_err());
    }

    #[test]
    fn test_validate_email() {
        let validator = InputValidator::default();

        assert!(validator.validate_email("user@example.com").is_ok());
        assert!(validator.validate_email("user@sub.example.com").is_ok());
        assert!(validator.validate_email("invalid").is_err());
        assert!(validator.validate_email("@example.com").is_err());
    }

    #[test]
    fn test_validate_url() {
        let validator = InputValidator::default();

        assert!(validator.validate_url("https://example.com").is_ok());
        assert!(validator.validate_url("http://localhost:8080").is_ok());
        assert!(validator.validate_url("ftp://example.com").is_err());
        assert!(validator.validate_url("https://example.com/<script>").is_err());
    }

    #[test]
    fn test_sanitize_text() {
        let validator = InputValidator::default();

        let input = "Hello\x00World\x1f!";
        let sanitized = validator.sanitize_text(input);
        assert_eq!(sanitized, "HelloWorld!");
    }

    #[test]
    fn test_sanitize_filename() {
        let validator = InputValidator::default();

        let input = "../etc/passwd";
        let sanitized = validator.sanitize_filename(input);
        assert_eq!(sanitized, "etcpasswd");

        let input2 = "my-file_name.txt";
        let sanitized2 = validator.sanitize_filename(input2);
        assert_eq!(sanitized2, "my-file_name.txt");
    }

    #[test]
    fn test_validate_json() {
        let validator = InputValidator::default();

        assert!(validator.validate_json(r#"{"key": "value"}"#).is_ok());
        assert!(validator.validate_json("not json").is_err());
    }

    #[test]
    fn test_validate_session_context() {
        let shallow = serde_json::json!({"a": {"b": "c"}});
        assert!(validate_session_context(&shallow).is_ok());

        // Create deeply nested JSON
        let mut deep = serde_json::json!("value");
        for _ in 0..15 {
            deep = serde_json::json!({"nested": deep});
        }
        assert!(validate_session_context(&deep).is_err());
    }
}
