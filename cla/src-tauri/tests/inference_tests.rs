// Inference engine tests for CLA
// Tests model loading, embedding generation, and inference operations

#![cfg(test)]

use cla::inference::{
    InferenceEngine, InferenceConfig, InferenceTask, InferenceResult,
    embedding::EmbeddingModel,
    ModelInfo, ModelTier,
};
use std::path::PathBuf;

mod embedding_tests {
    use super::*;

    #[test]
    fn test_cosine_similarity() {
        use cla::inference::embedding::cosine_similarity;

        // Identical vectors = 1.0
        let v1 = vec![1.0, 0.0, 0.0];
        assert!((cosine_similarity(&v1, &v1) - 1.0).abs() < 0.001);

        // Orthogonal vectors = 0.0
        let v2 = vec![0.0, 1.0, 0.0];
        assert!(cosine_similarity(&v1, &v2).abs() < 0.001);

        // Opposite vectors = -1.0
        let v3 = vec![-1.0, 0.0, 0.0];
        assert!((cosine_similarity(&v1, &v3) + 1.0).abs() < 0.001);
    }

    #[test]
    fn test_normalize_embedding() {
        use cla::inference::embedding::normalize;

        let v = vec![3.0, 4.0]; // Pythagorean triple, length = 5
        let normalized = normalize(&v);

        assert!((normalized[0] - 0.6).abs() < 0.001);
        assert!((normalized[1] - 0.8).abs() < 0.001);

        // Length should be 1
        let length: f32 = normalized.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!((length - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_embedding_dimension() {
        // MiniLM produces 384-dimensional embeddings
        let expected_dim = 384;

        // Mock embedding for testing
        let mock_embedding: Vec<f32> = (0..expected_dim).map(|i| i as f32 / 384.0).collect();

        assert_eq!(mock_embedding.len(), expected_dim);
    }

    #[test]
    fn test_batch_embedding_consistency() {
        // When embedding same text multiple times, results should be identical
        // (assuming deterministic model behavior)

        let text = "This is a test sentence for embedding.";

        // Mock: In real test, would use actual model
        let mock_embed = |s: &str| -> Vec<f32> {
            // Simple deterministic hash-based mock
            let hash = s.bytes().fold(0u64, |acc, b| acc.wrapping_mul(31).wrapping_add(b as u64));
            (0..384).map(|i| ((hash.wrapping_add(i)) % 1000) as f32 / 1000.0).collect()
        };

        let embed1 = mock_embed(text);
        let embed2 = mock_embed(text);

        assert_eq!(embed1, embed2);
    }
}

mod model_info_tests {
    use super::*;

    #[test]
    fn test_model_tier_sizes() {
        let tier1_models = vec![
            ModelInfo {
                id: "all-minilm-l6-v2".to_string(),
                name: "MiniLM Embeddings".to_string(),
                size_mb: 23,
                tier: ModelTier::Tier1,
                capabilities: vec!["embeddings".to_string()],
                downloaded: false,
                download_progress: None,
                version: "1.0.0".to_string(),
            },
            ModelInfo {
                id: "whisper-tiny".to_string(),
                name: "Whisper Tiny".to_string(),
                size_mb: 39,
                tier: ModelTier::Tier1,
                capabilities: vec!["transcription".to_string()],
                downloaded: false,
                download_progress: None,
                version: "1.0.0".to_string(),
            },
        ];

        let total_tier1: u64 = tier1_models.iter().map(|m| m.size_mb).sum();
        assert!(total_tier1 <= 100, "Tier 1 should be under 100MB");
    }

    #[test]
    fn test_model_capabilities() {
        let model = ModelInfo {
            id: "whisper-small".to_string(),
            name: "Whisper Small".to_string(),
            size_mb: 244,
            tier: ModelTier::Tier2,
            capabilities: vec!["transcription".to_string(), "language_detection".to_string()],
            downloaded: true,
            download_progress: None,
            version: "1.0.0".to_string(),
        };

        assert!(model.has_capability("transcription"));
        assert!(model.has_capability("language_detection"));
        assert!(!model.has_capability("embeddings"));
    }

    #[test]
    fn test_tier_priority() {
        assert!(ModelTier::Tier1 < ModelTier::Tier2);
        assert!(ModelTier::Tier2 < ModelTier::Tier3);
    }
}

mod inference_task_tests {
    use super::*;

    #[test]
    fn test_task_priority_ordering() {
        let tasks = vec![
            InferenceTask::GenerateEmbedding {
                text: "low priority".to_string(),
                priority: 1,
            },
            InferenceTask::GenerateEmbedding {
                text: "high priority".to_string(),
                priority: 10,
            },
            InferenceTask::GenerateEmbedding {
                text: "medium priority".to_string(),
                priority: 5,
            },
        ];

        let mut sorted_tasks = tasks.clone();
        sorted_tasks.sort_by(|a, b| b.priority().cmp(&a.priority()));

        assert_eq!(sorted_tasks[0].priority(), 10);
        assert_eq!(sorted_tasks[1].priority(), 5);
        assert_eq!(sorted_tasks[2].priority(), 1);
    }

    #[test]
    fn test_task_resource_estimation() {
        let embedding_task = InferenceTask::GenerateEmbedding {
            text: "Short text".to_string(),
            priority: 5,
        };

        let transcription_task = InferenceTask::Transcribe {
            audio_path: PathBuf::from("/tmp/audio.wav"),
            language: None,
            priority: 5,
        };

        // Transcription should estimate higher resource usage
        assert!(transcription_task.estimated_cpu_percent() > embedding_task.estimated_cpu_percent());
    }

    #[test]
    fn test_task_timeout() {
        let quick_task = InferenceTask::GenerateEmbedding {
            text: "Quick".to_string(),
            priority: 5,
        };

        let long_task = InferenceTask::Transcribe {
            audio_path: PathBuf::from("/tmp/long_audio.wav"),
            language: None,
            priority: 5,
        };

        assert!(quick_task.timeout_seconds() < long_task.timeout_seconds());
    }
}

mod inference_result_tests {
    use super::*;

    #[test]
    fn test_embedding_result_validation() {
        let valid_embedding = InferenceResult::Embedding {
            embedding: vec![0.1; 384],
            model_id: "all-minilm-l6-v2".to_string(),
            processing_time_ms: 50,
        };

        assert!(valid_embedding.is_valid());

        let invalid_embedding = InferenceResult::Embedding {
            embedding: vec![], // Empty is invalid
            model_id: "all-minilm-l6-v2".to_string(),
            processing_time_ms: 50,
        };

        assert!(!invalid_embedding.is_valid());
    }

    #[test]
    fn test_transcription_result() {
        let result = InferenceResult::Transcription {
            text: "Hello world".to_string(),
            language: Some("en".to_string()),
            confidence: 0.95,
            segments: vec![],
            processing_time_ms: 1000,
        };

        if let InferenceResult::Transcription { confidence, .. } = result {
            assert!(confidence >= 0.0 && confidence <= 1.0);
        }
    }

    #[test]
    fn test_ocr_result() {
        let result = InferenceResult::OcrText {
            text: "Extracted text from image".to_string(),
            confidence: 0.88,
            bounding_boxes: vec![],
            processing_time_ms: 200,
        };

        if let InferenceResult::OcrText { text, confidence, .. } = result {
            assert!(!text.is_empty());
            assert!(confidence > 0.0);
        }
    }
}

mod config_tests {
    use super::*;

    #[test]
    fn test_inference_config_defaults() {
        let config = InferenceConfig::default();

        // Default should be conservative
        assert!(config.max_concurrent_tasks <= 2);
        assert!(config.prefer_gpu == false); // CPU by default for compatibility
    }

    #[test]
    fn test_model_path_resolution() {
        let config = InferenceConfig {
            models_dir: PathBuf::from("/home/user/.cla/models"),
            ..InferenceConfig::default()
        };

        let model_path = config.model_path("whisper-tiny");
        assert!(model_path.starts_with(&config.models_dir));
        assert!(model_path.to_string_lossy().contains("whisper-tiny"));
    }
}

mod tokenizer_tests {
    #[test]
    fn test_basic_tokenization() {
        // Simple whitespace tokenizer mock
        let text = "Hello, world! This is a test.";
        let tokens: Vec<&str> = text.split_whitespace().collect();

        assert_eq!(tokens.len(), 6);
        assert_eq!(tokens[0], "Hello,");
    }

    #[test]
    fn test_special_characters() {
        let text = "User's \"quoted\" text—with dashes";
        let cleaned = text
            .chars()
            .filter(|c| c.is_alphanumeric() || c.is_whitespace())
            .collect::<String>();

        assert!(!cleaned.contains('"'));
        assert!(!cleaned.contains('—'));
    }

    #[test]
    fn test_max_token_length() {
        let max_tokens = 512;
        let long_text = "word ".repeat(1000);
        let tokens: Vec<&str> = long_text.split_whitespace().take(max_tokens).collect();

        assert_eq!(tokens.len(), max_tokens);
    }
}
