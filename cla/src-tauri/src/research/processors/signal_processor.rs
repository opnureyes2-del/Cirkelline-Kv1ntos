// Signal Processor - Converts research findings to Commander signals
// Part of the OODA loop integration

use crate::commander::{ResearchFinding, ResearchSource, Signal};

/// Signal processor for converting findings to commander signals
#[derive(Debug, Clone)]
pub struct SignalProcessor {
    /// Minimum relevance score to generate a signal
    pub relevance_threshold: f32,
    /// Minimum stars/popularity for tech detection
    pub popularity_threshold: u32,
}

impl Default for SignalProcessor {
    fn default() -> Self {
        Self {
            relevance_threshold: 0.6,
            popularity_threshold: 100,
        }
    }
}

impl SignalProcessor {
    /// Create with custom thresholds
    pub fn new(relevance_threshold: f32, popularity_threshold: u32) -> Self {
        Self {
            relevance_threshold,
            popularity_threshold,
        }
    }

    /// Process a finding and generate appropriate signal
    pub fn process(&self, finding: &ResearchFinding) -> Option<Signal> {
        // Skip low relevance findings
        if finding.relevance_score < self.relevance_threshold {
            log::debug!(
                "Skipping finding {} (relevance {} < threshold {})",
                finding.id,
                finding.relevance_score,
                self.relevance_threshold
            );
            return None;
        }

        // Determine signal type based on source and content
        let signal = match &finding.source {
            ResearchSource::GitHub => self.process_github_finding(finding),
            ResearchSource::ArXiv => self.process_arxiv_finding(finding),
            ResearchSource::Twitter | ResearchSource::Farcaster | ResearchSource::LensProtocol => {
                self.process_social_finding(finding)
            }
            ResearchSource::CustomFeed(_) => self.process_custom_finding(finding),
        };

        signal
    }

    /// Process GitHub finding
    fn process_github_finding(&self, finding: &ResearchFinding) -> Option<Signal> {
        // Check for security-related content
        let security_keywords = ["cve", "vulnerability", "security", "exploit", "patch"];
        let is_security = security_keywords.iter().any(|kw| {
            finding.title.to_lowercase().contains(kw)
                || finding.summary.to_lowercase().contains(kw)
        });

        if is_security {
            // Determine severity from content
            let severity = if finding.summary.to_lowercase().contains("critical") {
                crate::commander::decision_engine::Severity::Critical
            } else if finding.summary.to_lowercase().contains("high") {
                crate::commander::decision_engine::Severity::High
            } else {
                crate::commander::decision_engine::Severity::Medium
            };

            return Some(Signal::SecurityVulnerability {
                cve_id: Some(finding.id.clone()),
                severity,
                affected_component: finding.title.clone(),
            });
        }

        // Check popularity from metadata
        let stars = finding
            .metadata
            .get("stars")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u32;

        if stars >= self.popularity_threshold || finding.relevance_score >= 0.8 {
            Some(Signal::NewTechnologyDetected {
                name: finding.title.clone(),
                relevance_score: finding.relevance_score,
                source: "GitHub".to_string(),
            })
        } else {
            None
        }
    }

    /// Process ArXiv finding (academic paper)
    fn process_arxiv_finding(&self, finding: &ResearchFinding) -> Option<Signal> {
        Some(Signal::ResearchPublished {
            title: finding.title.clone(),
            relevance_score: finding.relevance_score,
            domain: finding
                .tags
                .first()
                .cloned()
                .unwrap_or_else(|| "Unknown".to_string()),
        })
    }

    /// Process social media finding
    fn process_social_finding(&self, finding: &ResearchFinding) -> Option<Signal> {
        // Check for trending content
        let engagement = finding
            .metadata
            .get("engagement")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u32;

        if engagement > 1000 || finding.relevance_score >= 0.75 {
            Some(Signal::SocialTrend {
                topic: finding.title.clone(),
                momentum: finding.relevance_score,
                platform: format!("{:?}", finding.source),
            })
        } else {
            None
        }
    }

    /// Process custom feed finding
    fn process_custom_finding(&self, finding: &ResearchFinding) -> Option<Signal> {
        // Generic new technology signal
        if finding.relevance_score >= 0.7 {
            Some(Signal::NewTechnologyDetected {
                name: finding.title.clone(),
                relevance_score: finding.relevance_score,
                source: "CustomFeed".to_string(),
            })
        } else {
            None
        }
    }

    /// Process multiple findings and return all signals
    pub fn process_batch(&self, findings: &[ResearchFinding]) -> Vec<Signal> {
        findings
            .iter()
            .filter_map(|f| self.process(f))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    fn create_finding(title: &str, source: ResearchSource, score: f32) -> ResearchFinding {
        ResearchFinding {
            id: "test-1".to_string(),
            source,
            title: title.to_string(),
            summary: "Test summary".to_string(),
            relevance_score: score,
            discovered_at: Utc::now(),
            tags: vec!["cs.AI".to_string()],
            url: None,
            metadata: serde_json::json!({"stars": 500}),
        }
    }

    #[test]
    fn test_process_github_finding() {
        let processor = SignalProcessor::default();
        let finding = create_finding("AI Framework", ResearchSource::GitHub, 0.8);

        let signal = processor.process(&finding);
        assert!(signal.is_some());

        if let Some(Signal::NewTechnologyDetected { name, .. }) = signal {
            assert_eq!(name, "AI Framework");
        } else {
            panic!("Expected NewTechnologyDetected signal");
        }
    }

    #[test]
    fn test_process_arxiv_finding() {
        let processor = SignalProcessor::default();
        let finding = create_finding("Neural Networks Paper", ResearchSource::ArXiv, 0.7);

        let signal = processor.process(&finding);
        assert!(signal.is_some());

        if let Some(Signal::ResearchPublished { title, .. }) = signal {
            assert_eq!(title, "Neural Networks Paper");
        } else {
            panic!("Expected ResearchPublished signal");
        }
    }

    #[test]
    fn test_low_relevance_skipped() {
        let processor = SignalProcessor::default();
        let finding = create_finding("Low relevance", ResearchSource::GitHub, 0.3);

        let signal = processor.process(&finding);
        assert!(signal.is_none());
    }
}
