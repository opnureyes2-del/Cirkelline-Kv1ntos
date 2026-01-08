// Research Processors Module - CLA FASE 6
// Post-processing components for research findings

mod relevance_scorer;
mod signal_processor;

pub use relevance_scorer::RelevanceScorer;
pub use signal_processor::SignalProcessor;

use crate::commander::ResearchFinding;
use std::collections::HashMap;

/// Processor configuration
#[derive(Debug, Clone)]
pub struct ProcessorConfig {
    /// Minimum score threshold to keep findings
    pub min_score_threshold: f32,
    /// Maximum findings to keep per source
    pub max_per_source: usize,
    /// Enable deduplication
    pub deduplicate: bool,
    /// Weight factors for scoring
    pub weights: ScoringWeights,
}

impl Default for ProcessorConfig {
    fn default() -> Self {
        Self {
            min_score_threshold: 0.3,
            max_per_source: 20,
            deduplicate: true,
            weights: ScoringWeights::default(),
        }
    }
}

/// Weights for different scoring factors
#[derive(Debug, Clone)]
pub struct ScoringWeights {
    /// Weight for keyword match
    pub keyword_match: f32,
    /// Weight for recency
    pub recency: f32,
    /// Weight for source authority
    pub source_authority: f32,
    /// Weight for engagement metrics
    pub engagement: f32,
}

impl Default for ScoringWeights {
    fn default() -> Self {
        Self {
            keyword_match: 0.4,
            recency: 0.2,
            source_authority: 0.25,
            engagement: 0.15,
        }
    }
}

/// Result of processing
#[derive(Debug, Clone)]
pub struct ProcessingResult {
    /// Processed findings
    pub findings: Vec<ResearchFinding>,
    /// Processing statistics
    pub stats: ProcessingStats,
}

/// Statistics from processing
#[derive(Debug, Clone, Default)]
pub struct ProcessingStats {
    /// Total input findings
    pub input_count: usize,
    /// Total output findings
    pub output_count: usize,
    /// Findings removed by threshold
    pub threshold_filtered: usize,
    /// Duplicates removed
    pub duplicates_removed: usize,
    /// Average final score
    pub avg_score: f32,
}

/// Trait for research processors
pub trait ResearchProcessor: Send + Sync {
    /// Process findings and return filtered/scored results
    fn process(&self, findings: Vec<ResearchFinding>) -> ProcessingResult;
    
    /// Get processor name
    fn name(&self) -> &str;
}

/// Combine multiple findings into a deduplicated, scored list
pub fn merge_findings(
    all_findings: Vec<Vec<ResearchFinding>>,
    config: &ProcessorConfig,
) -> ProcessingResult {
    let mut all: Vec<ResearchFinding> = all_findings.into_iter().flatten().collect();
    let input_count = all.len();
    
    // Sort by relevance score
    all.sort_by(|a, b| b.relevance_score.partial_cmp(&a.relevance_score).unwrap());
    
    // Deduplicate by title similarity
    let mut seen_titles: HashMap<String, bool> = HashMap::new();
    let mut duplicates_removed = 0;
    
    if config.deduplicate {
        all.retain(|f| {
            let normalized = normalize_title(&f.title);
            if seen_titles.contains_key(&normalized) {
                duplicates_removed += 1;
                false
            } else {
                seen_titles.insert(normalized, true);
                true
            }
        });
    }
    
    // Filter by threshold
    let threshold_filtered = all.iter()
        .filter(|f| f.relevance_score < config.min_score_threshold)
        .count();
    
    all.retain(|f| f.relevance_score >= config.min_score_threshold);
    
    // Calculate average score and output count before moving
    let output_count = all.len();
    let avg_score = if all.is_empty() {
        0.0
    } else {
        all.iter().map(|f| f.relevance_score).sum::<f32>() / output_count as f32
    };

    ProcessingResult {
        findings: all,
        stats: ProcessingStats {
            input_count,
            output_count,
            threshold_filtered,
            duplicates_removed,
            avg_score,
        },
    }
}

/// Normalize title for comparison
fn normalize_title(title: &str) -> String {
    title
        .to_lowercase()
        .chars()
        .filter(|c| c.is_alphanumeric() || c.is_whitespace())
        .collect::<String>()
        .split_whitespace()
        .collect::<Vec<&str>>()
        .join(" ")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::commander::ResearchSource;
    use chrono::Utc;
    
    fn make_finding(title: &str, score: f32) -> ResearchFinding {
        ResearchFinding {
            id: uuid::Uuid::new_v4().to_string(),
            source: ResearchSource::GitHub,
            title: title.to_string(),
            summary: "Test summary".to_string(),
            relevance_score: score,
            discovered_at: Utc::now(),
            tags: vec![],
            url: None,
            metadata: serde_json::json!({}),
        }
    }
    
    #[test]
    fn test_merge_findings_dedup() {
        let config = ProcessorConfig::default();
        let findings = vec![
            vec![make_finding("Test Title", 0.8)],
            vec![make_finding("Test Title", 0.7)],  // Duplicate
        ];
        
        let result = merge_findings(findings, &config);
        assert_eq!(result.stats.duplicates_removed, 1);
        assert_eq!(result.findings.len(), 1);
    }
    
    #[test]
    fn test_merge_findings_threshold() {
        let config = ProcessorConfig {
            min_score_threshold: 0.5,
            ..Default::default()
        };
        let findings = vec![
            vec![make_finding("High Score", 0.9)],
            vec![make_finding("Low Score", 0.2)],
        ];
        
        let result = merge_findings(findings, &config);
        assert_eq!(result.stats.threshold_filtered, 1);
        assert_eq!(result.findings.len(), 1);
    }
}
