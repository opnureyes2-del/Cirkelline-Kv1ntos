// Research Module - Research adapters and processors for Commander Unit
// Part of CLA FASE 6 - Autonomous research capabilities

pub mod adapters;
pub mod processors;
pub mod traits;

pub use adapters::{
    ArXivAdapter, GitHubAdapter, ResearchAdapterRegistry,
};
pub use processors::{RelevanceScorer, SignalProcessor};
pub use traits::ResearchAdapter;
