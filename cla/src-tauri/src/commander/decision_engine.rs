// Decision Engine - Autonomous decision-making for Commander Unit

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Signal types that the Commander can receive
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Signal {
    /// New technology detected in scan
    NewTechnologyDetected {
        name: String,
        relevance_score: f32,
        source: String,
    },
    /// Security vulnerability found
    SecurityVulnerability {
        severity: Severity,
        cve_id: Option<String>,
        affected_component: String,
    },
    /// Market signal detected
    MarketSignal {
        signal_type: MarketSignalType,
        confidence: f32,
        details: String,
    },
    /// Research paper published
    ResearchPublished {
        title: String,
        relevance_score: f32,
        domain: String,
    },
    /// Social media trend
    SocialTrend {
        topic: String,
        momentum: f32,
        platform: String,
    },
}

/// Severity levels
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Severity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

/// Market signal types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MarketSignalType {
    BullishTrend,
    BearishTrend,
    NewProject,
    PartnershipAnnouncement,
    RegulatoryNews,
}

/// Actions the Commander can take
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Action {
    /// Perform deep analysis
    DeepAnalyze,
    /// Queue for human review
    QueueForReview,
    /// Archive without action
    Archive,
    /// Send immediate alert
    ImmediateAlert,
    /// Monitor for further signals
    Monitor,
    /// Recommend action to user
    RecommendAction,
    /// Request user validation
    RequestValidation,
    /// Standard processing
    StandardProcess,
}

/// A decision made by the Decision Engine
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Decision {
    pub id: String,
    pub signal_type: String,
    pub action: Action,
    pub confidence: f32,
    pub rationale: String,
    pub timestamp: DateTime<Utc>,
    pub requires_approval: bool,
}

/// Decision rule for matching signals
struct Rule {
    condition: Box<dyn Fn(&SignalContext) -> bool + Send + Sync>,
    action: Action,
}

/// Context for evaluating rules
pub struct SignalContext {
    pub relevance_score: f32,
    pub severity: Option<Severity>,
    pub confidence: f32,
}

/// The Decision Engine - OODA loop implementation
pub struct DecisionEngine {
    // In real implementation, would have ML model and rules DB
}

impl DecisionEngine {
    pub fn new() -> Self {
        Self {}
    }

    /// Process a signal and return a decision (OODA: Observe-Orient-Decide-Act)
    pub async fn process_signal(&self, signal: Signal) -> Decision {
        // OBSERVE: Extract context from signal
        let context = self.build_context(&signal);

        // ORIENT: Contextualize within Cirkelline strategy
        let signal_type = self.get_signal_type(&signal);

        // DECIDE: Apply decision rules
        let (action, confidence) = self.apply_rules(&signal, &context);

        // Create decision
        let decision = Decision {
            id: uuid::Uuid::new_v4().to_string(),
            signal_type,
            action: action.clone(),
            confidence,
            rationale: self.generate_rationale(&signal, &action),
            timestamp: Utc::now(),
            requires_approval: self.requires_approval(&action, confidence),
        };

        // Log decision
        log::info!(
            "Decision made: {} -> {:?} (confidence: {:.2})",
            decision.signal_type,
            decision.action,
            decision.confidence
        );

        decision
    }

    /// Build context from signal
    fn build_context(&self, signal: &Signal) -> SignalContext {
        match signal {
            Signal::NewTechnologyDetected { relevance_score, .. } => SignalContext {
                relevance_score: *relevance_score,
                severity: None,
                confidence: *relevance_score,
            },
            Signal::SecurityVulnerability { severity, .. } => SignalContext {
                relevance_score: 1.0,
                severity: Some(severity.clone()),
                confidence: 0.9,
            },
            Signal::MarketSignal { confidence, .. } => SignalContext {
                relevance_score: 0.7,
                severity: None,
                confidence: *confidence,
            },
            Signal::ResearchPublished { relevance_score, .. } => SignalContext {
                relevance_score: *relevance_score,
                severity: None,
                confidence: *relevance_score,
            },
            Signal::SocialTrend { momentum, .. } => SignalContext {
                relevance_score: *momentum,
                severity: None,
                confidence: momentum * 0.7,
            },
        }
    }

    /// Get signal type string
    fn get_signal_type(&self, signal: &Signal) -> String {
        match signal {
            Signal::NewTechnologyDetected { .. } => "new_technology_detected".to_string(),
            Signal::SecurityVulnerability { .. } => "security_vulnerability".to_string(),
            Signal::MarketSignal { .. } => "market_signal".to_string(),
            Signal::ResearchPublished { .. } => "research_published".to_string(),
            Signal::SocialTrend { .. } => "social_trend".to_string(),
        }
    }

    /// Apply decision rules
    fn apply_rules(&self, signal: &Signal, context: &SignalContext) -> (Action, f32) {
        match signal {
            Signal::NewTechnologyDetected { relevance_score, .. } => {
                if *relevance_score > 0.8 {
                    (Action::DeepAnalyze, 0.9)
                } else if *relevance_score > 0.5 {
                    (Action::QueueForReview, 0.7)
                } else {
                    (Action::Archive, 0.8)
                }
            }
            Signal::SecurityVulnerability { severity, .. } => {
                match severity {
                    Severity::Critical => (Action::ImmediateAlert, 0.95),
                    Severity::High => (Action::DeepAnalyze, 0.85),
                    _ => (Action::StandardProcess, 0.7),
                }
            }
            Signal::MarketSignal { confidence, .. } => {
                if *confidence > 0.9 {
                    (Action::RecommendAction, 0.85)
                } else if *confidence > 0.7 {
                    (Action::RequestValidation, 0.75)
                } else {
                    (Action::Monitor, 0.6)
                }
            }
            Signal::ResearchPublished { relevance_score, .. } => {
                if *relevance_score > 0.7 {
                    (Action::DeepAnalyze, 0.8)
                } else {
                    (Action::Archive, 0.7)
                }
            }
            Signal::SocialTrend { momentum, .. } => {
                if *momentum > 0.8 {
                    (Action::DeepAnalyze, 0.7)
                } else {
                    (Action::Monitor, 0.6)
                }
            }
        }
    }

    /// Generate rationale for decision
    fn generate_rationale(&self, signal: &Signal, action: &Action) -> String {
        match (signal, action) {
            (Signal::SecurityVulnerability { severity: Severity::Critical, .. }, Action::ImmediateAlert) => {
                "Critical security vulnerability detected - immediate attention required".to_string()
            }
            (Signal::NewTechnologyDetected { relevance_score, name, .. }, Action::DeepAnalyze) => {
                format!("High relevance technology '{}' detected (score: {:.2}) - deep analysis recommended", name, relevance_score)
            }
            (Signal::MarketSignal { confidence, .. }, Action::RecommendAction) => {
                format!("High confidence market signal ({:.0}%) - action recommended", confidence * 100.0)
            }
            _ => format!("Standard processing for {:?}", action),
        }
    }

    /// Determine if decision requires human approval
    fn requires_approval(&self, action: &Action, confidence: f32) -> bool {
        match action {
            Action::ImmediateAlert => false, // Alert immediately
            Action::Archive => false, // Safe to auto-archive
            Action::Monitor => false, // Safe to monitor
            Action::DeepAnalyze => confidence < 0.85,
            Action::RecommendAction => true, // Always require approval for recommendations
            Action::RequestValidation => true,
            Action::QueueForReview => true,
            Action::StandardProcess => false,
        }
    }
}

impl Default for DecisionEngine {
    fn default() -> Self {
        Self::new()
    }
}
