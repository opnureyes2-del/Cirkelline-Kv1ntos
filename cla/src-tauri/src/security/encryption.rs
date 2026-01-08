// Encryption module for secure local data storage
// Uses AES-256-GCM for authenticated encryption

use aes_gcm::{
    aead::{Aead, KeyInit, OsRng},
    Aes256Gcm, Nonce,
};
use argon2::{Argon2, password_hash::SaltString};
use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
use serde::{Deserialize, Serialize};

/// Encrypted data container
#[derive(Clone, Serialize, Deserialize)]
pub struct EncryptedData {
    /// Base64-encoded ciphertext
    pub ciphertext: String,
    /// Base64-encoded nonce
    pub nonce: String,
    /// Base64-encoded salt (for key derivation)
    pub salt: String,
    /// Version for future compatibility
    pub version: u8,
}

/// Encryptor for local data
pub struct Encryptor {
    key: [u8; 32],
}

impl Encryptor {
    /// Create encryptor from master password
    pub fn from_password(password: &str, salt: &[u8]) -> Result<Self, EncryptionError> {
        let key = derive_key(password, salt)?;
        Ok(Self { key })
    }

    /// Create encryptor from raw key
    pub fn from_key(key: [u8; 32]) -> Self {
        Self { key }
    }

    /// Generate a new random key
    pub fn generate_key() -> [u8; 32] {
        use rand::RngCore;
        let mut key = [0u8; 32];
        OsRng.fill_bytes(&mut key);
        key
    }

    /// Encrypt data
    pub fn encrypt(&self, plaintext: &[u8]) -> Result<EncryptedData, EncryptionError> {
        let cipher = Aes256Gcm::new_from_slice(&self.key)
            .map_err(|_| EncryptionError::KeyError)?;

        // Generate random nonce
        let mut nonce_bytes = [0u8; 12];
        use rand::RngCore;
        OsRng.fill_bytes(&mut nonce_bytes);
        let nonce = Nonce::from_slice(&nonce_bytes);

        // Generate random salt for storage
        let salt = SaltString::generate(&mut OsRng);

        // Encrypt
        let ciphertext = cipher
            .encrypt(nonce, plaintext)
            .map_err(|_| EncryptionError::EncryptionFailed)?;

        Ok(EncryptedData {
            ciphertext: BASE64.encode(&ciphertext),
            nonce: BASE64.encode(nonce_bytes),
            salt: salt.to_string(),
            version: 1,
        })
    }

    /// Decrypt data
    pub fn decrypt(&self, encrypted: &EncryptedData) -> Result<Vec<u8>, EncryptionError> {
        if encrypted.version != 1 {
            return Err(EncryptionError::UnsupportedVersion);
        }

        let cipher = Aes256Gcm::new_from_slice(&self.key)
            .map_err(|_| EncryptionError::KeyError)?;

        let ciphertext = BASE64.decode(&encrypted.ciphertext)
            .map_err(|_| EncryptionError::InvalidData)?;

        let nonce_bytes = BASE64.decode(&encrypted.nonce)
            .map_err(|_| EncryptionError::InvalidData)?;

        if nonce_bytes.len() != 12 {
            return Err(EncryptionError::InvalidData);
        }

        let nonce = Nonce::from_slice(&nonce_bytes);

        cipher
            .decrypt(nonce, ciphertext.as_ref())
            .map_err(|_| EncryptionError::DecryptionFailed)
    }

    /// Encrypt string
    pub fn encrypt_string(&self, plaintext: &str) -> Result<EncryptedData, EncryptionError> {
        self.encrypt(plaintext.as_bytes())
    }

    /// Decrypt to string
    pub fn decrypt_string(&self, encrypted: &EncryptedData) -> Result<String, EncryptionError> {
        let bytes = self.decrypt(encrypted)?;
        String::from_utf8(bytes).map_err(|_| EncryptionError::InvalidData)
    }
}

/// Derive encryption key from password using Argon2id
fn derive_key(password: &str, salt: &[u8]) -> Result<[u8; 32], EncryptionError> {
    let argon2 = Argon2::default();
    let mut key = [0u8; 32];

    argon2
        .hash_password_into(password.as_bytes(), salt, &mut key)
        .map_err(|_| EncryptionError::KeyDerivationFailed)?;

    Ok(key)
}

/// Generate a random salt
pub fn generate_salt() -> Vec<u8> {
    use rand::RngCore;
    let mut salt = vec![0u8; 16];
    OsRng.fill_bytes(&mut salt);
    salt
}

/// Encryption errors
#[derive(Debug, Clone)]
pub enum EncryptionError {
    KeyError,
    KeyDerivationFailed,
    EncryptionFailed,
    DecryptionFailed,
    InvalidData,
    UnsupportedVersion,
}

impl std::fmt::Display for EncryptionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::KeyError => write!(f, "Invalid encryption key"),
            Self::KeyDerivationFailed => write!(f, "Failed to derive key from password"),
            Self::EncryptionFailed => write!(f, "Encryption failed"),
            Self::DecryptionFailed => write!(f, "Decryption failed - wrong key or corrupted data"),
            Self::InvalidData => write!(f, "Invalid encrypted data format"),
            Self::UnsupportedVersion => write!(f, "Unsupported encryption version"),
        }
    }
}

impl std::error::Error for EncryptionError {}

/// Secure memory wiper
pub fn secure_zero(data: &mut [u8]) {
    use std::ptr;
    unsafe {
        ptr::write_volatile(data.as_mut_ptr(), 0);
        for i in 0..data.len() {
            ptr::write_volatile(data.as_mut_ptr().add(i), 0);
        }
    }
    std::sync::atomic::compiler_fence(std::sync::atomic::Ordering::SeqCst);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encrypt_decrypt() {
        let key = Encryptor::generate_key();
        let encryptor = Encryptor::from_key(key);

        let plaintext = b"Hello, World!";
        let encrypted = encryptor.encrypt(plaintext).unwrap();
        let decrypted = encryptor.decrypt(&encrypted).unwrap();

        assert_eq!(plaintext.to_vec(), decrypted);
    }

    #[test]
    fn test_encrypt_decrypt_string() {
        let key = Encryptor::generate_key();
        let encryptor = Encryptor::from_key(key);

        let plaintext = "Sensitive data æøå";
        let encrypted = encryptor.encrypt_string(plaintext).unwrap();
        let decrypted = encryptor.decrypt_string(&encrypted).unwrap();

        assert_eq!(plaintext, decrypted);
    }

    #[test]
    fn test_wrong_key_fails() {
        let key1 = Encryptor::generate_key();
        let key2 = Encryptor::generate_key();

        let encryptor1 = Encryptor::from_key(key1);
        let encryptor2 = Encryptor::from_key(key2);

        let encrypted = encryptor1.encrypt(b"secret").unwrap();
        let result = encryptor2.decrypt(&encrypted);

        assert!(result.is_err());
    }

    #[test]
    fn test_from_password() {
        let salt = generate_salt();
        let encryptor = Encryptor::from_password("my_password", &salt).unwrap();

        let plaintext = b"Password protected data";
        let encrypted = encryptor.encrypt(plaintext).unwrap();

        // Same password and salt should work
        let encryptor2 = Encryptor::from_password("my_password", &salt).unwrap();
        let decrypted = encryptor2.decrypt(&encrypted).unwrap();

        assert_eq!(plaintext.to_vec(), decrypted);
    }
}
