// Embedding model implementation using ONNX Runtime v2
// Model: all-MiniLM-L6-v2 (384 dimensions)

use std::path::Path;
use ort::session::{Session, builder::GraphOptimizationLevel};
use ort::value::Tensor;

/// Embedding model for semantic search
pub struct EmbeddingModel {
    session: Session,
    tokenizer: Tokenizer,
    model_id: String,
}

impl EmbeddingModel {
    /// Load the embedding model from disk
    pub fn load(model_path: &Path) -> Result<Self, String> {
        // Initialize ONNX Runtime environment
        ort::init()
            .with_name("cirkelline-cla")
            .commit()
            .map_err(|e| format!("Failed to initialize ONNX Runtime: {}", e))?;

        // Load the model using ort v2 API
        let session = Session::builder()
            .map_err(|e| format!("Failed to create session builder: {}", e))?
            .with_optimization_level(GraphOptimizationLevel::Level3)
            .map_err(|e| format!("Failed to set optimization level: {}", e))?
            .with_intra_threads(4)
            .map_err(|e| format!("Failed to set thread count: {}", e))?
            .commit_from_file(model_path)
            .map_err(|e| format!("Failed to load model: {}", e))?;

        // Load tokenizer (vocab.txt should be alongside the model)
        let vocab_path = model_path.parent()
            .ok_or("Invalid model path")?
            .join("vocab.txt");

        let tokenizer = Tokenizer::new(&vocab_path)?;

        Ok(Self {
            session,
            tokenizer,
            model_id: "all-MiniLM-L6-v2".to_string(),
        })
    }

    /// Generate embedding for text (synchronous)
    pub fn encode(&mut self, text: &str) -> Result<Vec<f32>, String> {
        // Tokenize input
        let encoding = self.tokenizer.encode(text, 512)?;

        // Prepare inputs
        let input_ids: Vec<i64> = encoding.input_ids.iter().map(|&x| x as i64).collect();
        let attention_mask: Vec<i64> = encoding.attention_mask.iter().map(|&x| x as i64).collect();
        let token_type_ids: Vec<i64> = vec![0i64; input_ids.len()];

        let seq_len = input_ids.len();

        // Create input tensors using ort v2 API
        let input_ids_tensor = Tensor::from_array(([1usize, seq_len], input_ids))
            .map_err(|e| format!("Failed to create input_ids tensor: {}", e))?;
        let attention_mask_tensor = Tensor::from_array(([1usize, seq_len], attention_mask.clone()))
            .map_err(|e| format!("Failed to create attention_mask tensor: {}", e))?;
        let token_type_ids_tensor = Tensor::from_array(([1usize, seq_len], token_type_ids))
            .map_err(|e| format!("Failed to create token_type_ids tensor: {}", e))?;

        // Build inputs vec - ort v2 inputs! returns Vec directly
        let inputs = ort::inputs![
            "input_ids" => input_ids_tensor,
            "attention_mask" => attention_mask_tensor,
            "token_type_ids" => token_type_ids_tensor
        ];

        // Run inference using ort v2 API
        let outputs = self.session.run(inputs)
            .map_err(|e| format!("Inference failed: {}", e))?;

        // Extract output - last_hidden_state shape: (1, seq_len, 384)
        let output = outputs.get("last_hidden_state")
            .ok_or("Missing output: last_hidden_state")?;

        // ort v2: try_extract_tensor returns (&Shape, &[T]) tuple
        let (shape, data) = output.try_extract_tensor::<f32>()
            .map_err(|e| format!("Failed to extract output tensor: {}", e))?;

        // Verify shape is correct
        let shape_dims: Vec<i64> = shape.iter().cloned().collect();
        if shape_dims.len() != 3 {
            return Err(format!("Expected 3D output, got {}D", shape_dims.len()));
        }

        let hidden_size = shape_dims[2] as usize;

        // Mean pooling over sequence dimension
        let embedding = mean_pooling_flat(data, &encoding.attention_mask, seq_len, hidden_size)?;

        // L2 normalize
        let normalized = l2_normalize(&embedding);

        Ok(normalized)
    }

    /// Get model ID
    pub fn model_id(&self) -> &str {
        &self.model_id
    }

    /// Get embedding dimension
    pub fn embedding_dim(&self) -> usize {
        384
    }
}

/// Mean pooling over sequence dimension with attention mask (for flat tensor data)
fn mean_pooling_flat(
    hidden_states: &[f32],
    attention_mask: &[u32],
    seq_len: usize,
    hidden_size: usize,
) -> Result<Vec<f32>, String> {
    let mut embedding = vec![0.0f32; hidden_size];
    let mut total_weight = 0.0f32;

    // hidden_states shape: (1, seq_len, hidden_size) - stored in row-major order
    for i in 0..seq_len {
        let weight = attention_mask.get(i).copied().unwrap_or(0) as f32;
        total_weight += weight;

        for j in 0..hidden_size {
            // Access flattened tensor: batch=0, seq=i, hidden=j
            let idx = i * hidden_size + j;
            if let Some(&val) = hidden_states.get(idx) {
                embedding[j] += val * weight;
            }
        }
    }

    if total_weight > 0.0 {
        for val in &mut embedding {
            *val /= total_weight;
        }
    }

    Ok(embedding)
}

/// L2 normalize a vector
fn l2_normalize(vec: &[f32]) -> Vec<f32> {
    let norm: f32 = vec.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        vec.iter().map(|x| x / norm).collect()
    } else {
        vec.to_vec()
    }
}

/// Simple WordPiece tokenizer for BERT-based models
pub struct Tokenizer {
    vocab: std::collections::HashMap<String, u32>,
    unk_id: u32,
    cls_id: u32,
    sep_id: u32,
    #[allow(dead_code)]
    pad_id: u32,
}

pub struct Encoding {
    pub input_ids: Vec<u32>,
    pub attention_mask: Vec<u32>,
}

impl Tokenizer {
    pub fn new(vocab_path: &Path) -> Result<Self, String> {
        let vocab_text = std::fs::read_to_string(vocab_path)
            .map_err(|e| format!("Failed to read vocab: {}", e))?;

        let mut vocab = std::collections::HashMap::new();
        for (idx, line) in vocab_text.lines().enumerate() {
            vocab.insert(line.to_string(), idx as u32);
        }

        let unk_id = *vocab.get("[UNK]").unwrap_or(&0);
        let cls_id = *vocab.get("[CLS]").unwrap_or(&101);
        let sep_id = *vocab.get("[SEP]").unwrap_or(&102);
        let pad_id = *vocab.get("[PAD]").unwrap_or(&0);

        Ok(Self {
            vocab,
            unk_id,
            cls_id,
            sep_id,
            pad_id,
        })
    }

    pub fn encode(&self, text: &str, max_len: usize) -> Result<Encoding, String> {
        let tokens = self.tokenize(text);

        // Truncate if needed (leaving room for [CLS] and [SEP])
        let max_tokens = max_len.saturating_sub(2);
        let tokens: Vec<_> = tokens.into_iter().take(max_tokens).collect();

        // Build input_ids: [CLS] + tokens + [SEP]
        let mut input_ids = Vec::with_capacity(tokens.len() + 2);
        input_ids.push(self.cls_id);
        for token in &tokens {
            let id = self.vocab.get(token).copied().unwrap_or(self.unk_id);
            input_ids.push(id);
        }
        input_ids.push(self.sep_id);

        // Attention mask
        let attention_mask = vec![1u32; input_ids.len()];

        Ok(Encoding {
            input_ids,
            attention_mask,
        })
    }

    fn tokenize(&self, text: &str) -> Vec<String> {
        let mut tokens = Vec::new();
        let text = text.to_lowercase();

        for word in text.split_whitespace() {
            // Simple WordPiece tokenization
            let mut start = 0;
            while start < word.len() {
                let mut end = word.len();
                let mut found = false;

                while start < end {
                    let substr = if start == 0 {
                        word[start..end].to_string()
                    } else {
                        format!("##{}", &word[start..end])
                    };

                    if self.vocab.contains_key(&substr) {
                        tokens.push(substr);
                        found = true;
                        break;
                    }
                    end -= 1;
                }

                if !found {
                    tokens.push("[UNK]".to_string());
                    break;
                }
                start = end;
            }
        }

        tokens
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_l2_normalize() {
        let vec = vec![3.0, 4.0];
        let normalized = l2_normalize(&vec);
        assert!((normalized[0] - 0.6).abs() < 0.001);
        assert!((normalized[1] - 0.8).abs() < 0.001);
    }
}
