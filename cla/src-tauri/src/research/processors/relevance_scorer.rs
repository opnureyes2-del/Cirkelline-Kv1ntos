// Relevance Scorer - Calculates relevance scores for research findings
// Uses multiple factors: keyword matching, recency, source authority

use crate::commander::{ResearchFinding, ResearchSource};
use super::{ProcessorConfig, ScoringWeights, ProcessingResult, ProcessingStats, ResearchProcessor};
use chrono::{Duration, Utc};
use std::collections::HashSet;

/// Relevance scorer for research findings
#[derive(Debug, Clone)]
pub struct RelevanceScorer {
    /// Keywords to boost relevance
    keywords: HashSet<String>,
    /// Scoring weights
    weights: ScoringWeights,
    /// Minimum threshold
    min_threshold: f32,
}

impl RelevanceScorer {
    /// Create a new relevance scorer
    pub fn new() -> Self {
        Self {
            keywords: HashSet::new(),
            weights: ScoringWeights::default(),
            min_threshold: 0.3,
        }
    }

    /// Create scorer with specific keywords
    pub fn with_keywords(keywords: Vec<String>) -> Self {
        Self {
            keywords: keywords.into_iter().map(|k| k.to_lowercase()).collect(),
            weights: ScoringWeights::default(),
            min_threshold: 0.3,
        }
    }

    /// Set custom weights
    pub fn with_weights(mut self, weights: ScoringWeights) -> Self {
        self.weights = weights;
        self
    }

    /// Set minimum threshold
    pub fn with_threshold(mut self, threshold: f32) -> Self {
        self.min_threshold = threshold;
        self
    }

    /// Add keywords
    pub fn add_keywords(&mut self, keywords: impl IntoIterator<Item = String>) {
        for kw in keywords {
            self.keywords.insert(kw.to_lowercase());
        }
    }

    /// Calculate keyword match score
    fn keyword_score(&self, finding: &ResearchFinding) -> f32 {
        if self.keywords.is_empty() {
            return 0.5; // Neutral if no keywords
        }

        let text = format!(
            "{} {} {}",
            finding.title.to_lowercase(),
            finding.summary.to_lowercase(),
            finding.tags.join(" ").to_lowercase()
        );

        let matches = self.keywords.iter()
            .filter(|kw| text.contains(kw.as_str()))
            .count();

        (matches as f32 / self.keywords.len() as f32).min(1.0)
    }

    /// Calculate recency score
    fn recency_score(&self, finding: &ResearchFinding) -> f32 {
        let now = Utc::now();
        let age = now.signed_duration_since(finding.discovered_at);

        // Score decays over time
        // - Within 1 day: 1.0
        // - Within 1 week: 0.8
        // - Within 1 month: 0.5
        // - Older: 0.2
        if age < Duration::days(1) {
            1.0
        } else if age < Duration::days(7) {
            0.8
        } else if age < Duration::days(30) {
            0.5
        } else {
            0.2
        }
    }

    /// Calculate source authority score
    fn source_authority_score(&self, finding: &ResearchFinding) -> f32 {
        match finding.source {
            ResearchSource::ArXiv => 0.95,        // Peer-reviewed papers
            ResearchSource::GitHub => 0.85,       // Code repos
            ResearchSource::Twitter => 0.5,       // Social media
            ResearchSource::Farcaster => 0.6,     // Decentralized social
            ResearchSource::LensProtocol => 0.6,  // Web3 social
            ResearchSource::CustomFeed(_) => 0.7, // Custom feeds
        }
    }

    /// Calculate engagement score from metadata
    fn engagement_score(&self, finding: &ResearchFinding) -> f32 {
        // Try to extract engagement metrics from metadata
        let stars = finding.metadata.get("stars")
            .and_then(|v| v.as_u64())
            .unwrap_or(0);
        let citations = finding.metadata.get("citations")
            .and_then(|v| v.as_u64())
            .unwrap_or(0);
        let likes = finding.metadata.get("likes")
            .and_then(|v| v.as_u64())
            .unwrap_or(0);

        let engagement = stars + (citations * 10) + likes;

        // Logarithmic scale
        if engagement == 0 {
            0.3
        } else {
            (engagement as f32).ln() / 10.0_f32.ln()
        }.min(1.0)
    }

    /// Calculate total relevance score
    pub fn score(&self, finding: &ResearchFinding) -> f32 {
        let keyword = self.keyword_score(finding);
        let recency = self.recency_score(finding);
        let authority = self.source_authority_score(finding);
        let engagement = self.engagement_score(finding);

        // Weighted sum
        let total = 
            keyword * self.weights.keyword_match +
            recency * self.weights.recency +
            authority * self.weights.source_authority +
            engagement * self.weights.engagement;

        // Ensure score is in [0, 1]
        total.max(0.0).min(1.0)
    }

    /// Score all findings
    pub fn score_all(&self, findings: &mut [ResearchFinding]) {
        for finding in findings.iter_mut() {
            finding.relevance_score = self.score(finding);
        }
    }
}

impl Default for RelevanceScorer {
    fn default() -> Self {
        Self::new()
    }
}

impl ResearchProcessor for RelevanceScorer {
    fn process(&self, mut findings: Vec<ResearchFinding>) -> ProcessingResult {
        let input_count = findings.len();

        // Score all findings
        self.score_all(&mut findings);

        // Sort by score descending
        findings.sort_by(|a, b| b.relevance_score.partial_cmp(&a.relevance_score).unwrap());

        // Filter by threshold
        let threshold_filtered = findings.iter()
            .filter(|f| f.relevance_score < self.min_threshold)
            .count();
        
        findings.retain(|f| f.relevance_score >= self.min_threshold);

        let avg_score = if findings.is_empty() {
            0.0
        } else {
            findings.iter().map(|f| f.relevance_score).sum::<f32>() / findings.len() as f32
        };

        ProcessingResult {
            findings,
            stats: ProcessingStats {
                input_count,
                output_count: input_count - threshold_filtered,
                threshold_filtered,
                duplicates_removed: 0,
                avg_score,
            },
        }
    }

    fn name(&self) -> &str {
        "RelevanceScorer"
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    fn make_finding(title: &str, tags: Vec<&str>) -> ResearchFinding {
        ResearchFinding {
            id: uuid::Uuid::new_v4().to_string(),
            source: ResearchSource::GitHub,
            title: title.to_string(),
            summary: "Test summary".to_string(),
            relevance_score: 0.0,
            discovered_at: Utc::now(),
            tags: tags.into_iter().map(|s| s.to_string()).collect(),
            url: None,
            metadata: serde_json::json!({"stars": 100}),
        }
    }

    #[test]
    fn test_keyword_scoring() {
        let scorer = RelevanceScorer::with_keywords(vec![
            "rust".to_string(),
            "async".to_string(),
        ]);

        let finding = make_finding("Rust Async Runtime", vec!["rust"]);
        let score = scorer.keyword_score(&finding);
        
        assert!(score > 0.5); // Should match both keywords
    }

    #[test]
    fn test_source_authority() {
        let scorer = RelevanceScorer::new();

        let arxiv = ResearchFinding {
            source: ResearchSource::ArXiv,
            ..make_finding("Paper", vec![])
        };
        let twitter = ResearchFinding {
            source: ResearchSource::Twitter,
            ..make_finding("Tweet", vec![])
        };

        assert!(scorer.source_authority_score(&arxiv) > scorer.source_authority_score(&twitter));
    }

    #[test]
    fn test_process() {
        let scorer = RelevanceScorer::new().with_threshold(0.0);
        let findings = vec![
            make_finding("Test 1", vec![]),
            make_finding("Test 2", vec![]),
        ];

        let result = scorer.process(findings);
        assert_eq!(result.stats.input_count, 2);
        assert_eq!(result.findings.len(), 2);
    }
}
