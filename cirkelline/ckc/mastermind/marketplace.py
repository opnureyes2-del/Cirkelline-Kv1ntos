"""
DEL J: Markedsspace & Fællesskab
=================================

Komponenter til markedsplads og community i MASTERMIND.

Komponenter:
- MarketplaceConnector: Forbindelse til markedsplads
- CommunityHub: Fællesskabsfunktioner
- AssetListing: Oplistning af assets
- ReviewSystem: Anmeldelsessystem
- DiscoveryEngine: Opdagelses- og søgemotor
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import asyncio


# =============================================================================
# ENUMS
# =============================================================================

class AssetType(Enum):
    """Typer af assets på markedsplads."""
    TEMPLATE = "template"
    PLUGIN = "plugin"
    AGENT = "agent"
    WORKFLOW = "workflow"
    DATASET = "dataset"
    MODEL = "model"
    INTEGRATION = "integration"


class AssetStatus(Enum):
    """Status for et asset."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class PricingModel(Enum):
    """Prismodeller for assets."""
    FREE = "free"
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    FREEMIUM = "freemium"


class CommunityRole(Enum):
    """Roller i fællesskabet."""
    MEMBER = "member"
    CONTRIBUTOR = "contributor"
    MODERATOR = "moderator"
    ADMIN = "admin"
    VERIFIED_PUBLISHER = "verified_publisher"


class ReviewStatus(Enum):
    """Status for anmeldelse."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class DiscoverySort(Enum):
    """Sorteringsmuligheder for discovery."""
    RELEVANCE = "relevance"
    POPULARITY = "popularity"
    RATING = "rating"
    NEWEST = "newest"
    PRICE_LOW = "price_low"
    PRICE_HIGH = "price_high"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Asset:
    """Et asset på markedspladsen."""
    asset_id: str
    asset_type: AssetType
    name: str
    description: str
    publisher_id: str
    status: AssetStatus
    pricing_model: PricingModel
    price: Decimal = Decimal("0")
    currency: str = "DKK"
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    downloads: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssetVersion:
    """En version af et asset."""
    version_id: str
    asset_id: str
    version: str
    changelog: str
    download_url: str
    file_size_bytes: int
    released_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CommunityMember:
    """Et medlem af fællesskabet."""
    member_id: str
    user_id: str
    display_name: str
    role: CommunityRole
    reputation: int = 0
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    contributions: int = 0
    badges: List[str] = field(default_factory=list)
    bio: str = ""


@dataclass
class Review:
    """En anmeldelse."""
    review_id: str
    asset_id: str
    reviewer_id: str
    rating: int  # 1-5
    title: str
    content: str
    status: ReviewStatus = ReviewStatus.PENDING
    helpful_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not 1 <= self.rating <= 5:
            raise ValueError("Rating skal være mellem 1 og 5")


@dataclass
class SearchResult:
    """Et søgeresultat."""
    asset: Asset
    score: float
    highlights: Dict[str, str] = field(default_factory=dict)


@dataclass
class DiscoveryQuery:
    """En discovery/søgeforespørgsel."""
    query: str = ""
    asset_types: List[AssetType] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    pricing_models: List[PricingModel] = field(default_factory=list)
    min_rating: float = 0.0
    max_price: Optional[Decimal] = None
    sort_by: DiscoverySort = DiscoverySort.RELEVANCE
    page: int = 1
    page_size: int = 20


@dataclass
class DiscoveryResponse:
    """Svar fra discovery-søgning."""
    results: List[SearchResult]
    total_count: int
    page: int
    page_size: int
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)


# =============================================================================
# MARKETPLACE CONNECTOR
# =============================================================================

class MarketplaceConnector:
    """Forbinder til og administrerer markedspladsen."""

    def __init__(self):
        self._assets: Dict[str, Asset] = {}
        self._versions: Dict[str, List[AssetVersion]] = {}
        self._purchases: Dict[str, Set[str]] = {}  # user_id -> asset_ids
        self._lock = asyncio.Lock()

    async def publish_asset(
        self,
        publisher_id: str,
        asset_type: AssetType,
        name: str,
        description: str,
        pricing_model: PricingModel,
        price: Decimal = Decimal("0"),
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Asset:
        """Publicer et nyt asset."""
        async with self._lock:
            asset_id = f"asset_{uuid4().hex[:12]}"

            asset = Asset(
                asset_id=asset_id,
                asset_type=asset_type,
                name=name,
                description=description,
                publisher_id=publisher_id,
                status=AssetStatus.PENDING_REVIEW,
                pricing_model=pricing_model,
                price=price,
                tags=tags or [],
                metadata=metadata or {}
            )

            self._assets[asset_id] = asset
            return asset

    async def approve_asset(self, asset_id: str) -> Optional[Asset]:
        """Godkend et asset til publicering."""
        async with self._lock:
            if asset_id not in self._assets:
                return None

            asset = self._assets[asset_id]
            asset.status = AssetStatus.PUBLISHED
            asset.updated_at = datetime.now(timezone.utc)
            return asset

    async def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Hent et asset."""
        return self._assets.get(asset_id)

    async def update_asset(
        self,
        asset_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Asset]:
        """Opdater et asset."""
        async with self._lock:
            if asset_id not in self._assets:
                return None

            asset = self._assets[asset_id]
            for key, value in updates.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)

            asset.updated_at = datetime.now(timezone.utc)
            return asset

    async def add_version(
        self,
        asset_id: str,
        version: str,
        changelog: str,
        download_url: str,
        file_size_bytes: int
    ) -> Optional[AssetVersion]:
        """Tilføj ny version af et asset."""
        async with self._lock:
            if asset_id not in self._assets:
                return None

            version_id = f"ver_{uuid4().hex[:8]}"
            asset_version = AssetVersion(
                version_id=version_id,
                asset_id=asset_id,
                version=version,
                changelog=changelog,
                download_url=download_url,
                file_size_bytes=file_size_bytes
            )

            if asset_id not in self._versions:
                self._versions[asset_id] = []
            self._versions[asset_id].append(asset_version)

            # Opdater asset version
            self._assets[asset_id].version = version
            self._assets[asset_id].updated_at = datetime.now(timezone.utc)

            return asset_version

    async def purchase_asset(
        self,
        user_id: str,
        asset_id: str
    ) -> bool:
        """Køb et asset."""
        async with self._lock:
            if asset_id not in self._assets:
                return False

            asset = self._assets[asset_id]
            if asset.status != AssetStatus.PUBLISHED:
                return False

            if user_id not in self._purchases:
                self._purchases[user_id] = set()

            self._purchases[user_id].add(asset_id)
            asset.downloads += 1
            return True

    async def get_user_purchases(self, user_id: str) -> List[Asset]:
        """Hent brugerens køb."""
        purchased_ids = self._purchases.get(user_id, set())
        return [self._assets[aid] for aid in purchased_ids if aid in self._assets]

    async def get_publisher_assets(
        self,
        publisher_id: str
    ) -> List[Asset]:
        """Hent alle assets fra en publisher."""
        return [a for a in self._assets.values() if a.publisher_id == publisher_id]


# =============================================================================
# COMMUNITY HUB
# =============================================================================

class CommunityHub:
    """Håndterer fællesskabsfunktioner."""

    def __init__(self):
        self._members: Dict[str, CommunityMember] = {}
        self._discussions: Dict[str, List[Dict]] = {}  # asset_id -> discussions
        self._follows: Dict[str, Set[str]] = {}  # user_id -> followed_user_ids
        self._lock = asyncio.Lock()

    async def register_member(
        self,
        user_id: str,
        display_name: str,
        bio: str = ""
    ) -> CommunityMember:
        """Registrer nyt medlem."""
        async with self._lock:
            member_id = f"member_{uuid4().hex[:8]}"

            member = CommunityMember(
                member_id=member_id,
                user_id=user_id,
                display_name=display_name,
                role=CommunityRole.MEMBER,
                bio=bio
            )

            self._members[user_id] = member
            return member

    async def get_member(self, user_id: str) -> Optional[CommunityMember]:
        """Hent medlem."""
        return self._members.get(user_id)

    async def update_role(
        self,
        user_id: str,
        new_role: CommunityRole
    ) -> Optional[CommunityMember]:
        """Opdater medlemsrolle."""
        async with self._lock:
            if user_id not in self._members:
                return None

            self._members[user_id].role = new_role
            return self._members[user_id]

    async def add_reputation(
        self,
        user_id: str,
        points: int,
        reason: str
    ) -> Optional[CommunityMember]:
        """Tilføj reputation points."""
        async with self._lock:
            if user_id not in self._members:
                return None

            self._members[user_id].reputation += points
            return self._members[user_id]

    async def award_badge(
        self,
        user_id: str,
        badge: str
    ) -> Optional[CommunityMember]:
        """Tildel badge til medlem."""
        async with self._lock:
            if user_id not in self._members:
                return None

            if badge not in self._members[user_id].badges:
                self._members[user_id].badges.append(badge)

            return self._members[user_id]

    async def follow_user(
        self,
        follower_id: str,
        followed_id: str
    ) -> bool:
        """Følg en anden bruger."""
        async with self._lock:
            if follower_id not in self._follows:
                self._follows[follower_id] = set()

            self._follows[follower_id].add(followed_id)
            return True

    async def unfollow_user(
        self,
        follower_id: str,
        followed_id: str
    ) -> bool:
        """Stop med at følge en bruger."""
        async with self._lock:
            if follower_id in self._follows:
                self._follows[follower_id].discard(followed_id)
                return True
            return False

    async def get_followers(self, user_id: str) -> List[str]:
        """Hent brugerens følgere."""
        followers = []
        for follower_id, following in self._follows.items():
            if user_id in following:
                followers.append(follower_id)
        return followers

    async def get_following(self, user_id: str) -> List[str]:
        """Hent hvem brugeren følger."""
        return list(self._follows.get(user_id, set()))

    async def get_leaderboard(self, limit: int = 10) -> List[CommunityMember]:
        """Hent reputation leaderboard."""
        sorted_members = sorted(
            self._members.values(),
            key=lambda m: m.reputation,
            reverse=True
        )
        return sorted_members[:limit]


# =============================================================================
# ASSET LISTING
# =============================================================================

class AssetListing:
    """Håndterer asset listings og kategorier."""

    def __init__(self, marketplace: MarketplaceConnector):
        self._marketplace = marketplace
        self._categories: Dict[str, List[str]] = {}  # category -> asset_ids
        self._featured: List[str] = []
        self._lock = asyncio.Lock()

    async def add_to_category(
        self,
        asset_id: str,
        category: str
    ) -> bool:
        """Tilføj asset til kategori."""
        async with self._lock:
            if category not in self._categories:
                self._categories[category] = []

            if asset_id not in self._categories[category]:
                self._categories[category].append(asset_id)
            return True

    async def remove_from_category(
        self,
        asset_id: str,
        category: str
    ) -> bool:
        """Fjern asset fra kategori."""
        async with self._lock:
            if category in self._categories:
                if asset_id in self._categories[category]:
                    self._categories[category].remove(asset_id)
                    return True
            return False

    async def get_category_assets(
        self,
        category: str
    ) -> List[Asset]:
        """Hent assets i en kategori."""
        asset_ids = self._categories.get(category, [])
        assets = []
        for aid in asset_ids:
            asset = await self._marketplace.get_asset(aid)
            if asset and asset.status == AssetStatus.PUBLISHED:
                assets.append(asset)
        return assets

    async def get_categories(self) -> List[str]:
        """Hent alle kategorier."""
        return list(self._categories.keys())

    async def set_featured(self, asset_ids: List[str]) -> None:
        """Sæt featured assets."""
        async with self._lock:
            self._featured = asset_ids

    async def get_featured(self) -> List[Asset]:
        """Hent featured assets."""
        assets = []
        for aid in self._featured:
            asset = await self._marketplace.get_asset(aid)
            if asset and asset.status == AssetStatus.PUBLISHED:
                assets.append(asset)
        return assets

    async def get_trending(self, limit: int = 10) -> List[Asset]:
        """Hent trending assets baseret på downloads."""
        all_assets = [
            a for a in self._marketplace._assets.values()
            if a.status == AssetStatus.PUBLISHED
        ]
        sorted_assets = sorted(
            all_assets,
            key=lambda a: a.downloads,
            reverse=True
        )
        return sorted_assets[:limit]


# =============================================================================
# REVIEW SYSTEM
# =============================================================================

class ReviewSystem:
    """Håndterer anmeldelser."""

    def __init__(self, marketplace: MarketplaceConnector):
        self._marketplace = marketplace
        self._reviews: Dict[str, Review] = {}
        self._asset_reviews: Dict[str, List[str]] = {}  # asset_id -> review_ids
        self._lock = asyncio.Lock()

    async def submit_review(
        self,
        asset_id: str,
        reviewer_id: str,
        rating: int,
        title: str,
        content: str
    ) -> Review:
        """Indsend anmeldelse."""
        async with self._lock:
            review_id = f"review_{uuid4().hex[:12]}"

            review = Review(
                review_id=review_id,
                asset_id=asset_id,
                reviewer_id=reviewer_id,
                rating=rating,
                title=title,
                content=content
            )

            self._reviews[review_id] = review

            if asset_id not in self._asset_reviews:
                self._asset_reviews[asset_id] = []
            self._asset_reviews[asset_id].append(review_id)

            return review

    async def approve_review(self, review_id: str) -> Optional[Review]:
        """Godkend anmeldelse."""
        async with self._lock:
            if review_id not in self._reviews:
                return None

            review = self._reviews[review_id]
            review.status = ReviewStatus.APPROVED
            review.updated_at = datetime.now(timezone.utc)

            # Opdater asset rating
            await self._update_asset_rating(review.asset_id)

            return review

    async def _update_asset_rating(self, asset_id: str) -> None:
        """Opdater asset rating baseret på godkendte reviews."""
        review_ids = self._asset_reviews.get(asset_id, [])
        approved_reviews = [
            self._reviews[rid] for rid in review_ids
            if self._reviews[rid].status == ReviewStatus.APPROVED
        ]

        if approved_reviews:
            avg_rating = sum(r.rating for r in approved_reviews) / len(approved_reviews)
            asset = await self._marketplace.get_asset(asset_id)
            if asset:
                asset.rating_avg = round(avg_rating, 2)
                asset.rating_count = len(approved_reviews)

    async def get_reviews(
        self,
        asset_id: str,
        status: Optional[ReviewStatus] = ReviewStatus.APPROVED
    ) -> List[Review]:
        """Hent anmeldelser for et asset."""
        review_ids = self._asset_reviews.get(asset_id, [])
        reviews = [self._reviews[rid] for rid in review_ids]

        if status:
            reviews = [r for r in reviews if r.status == status]

        return sorted(reviews, key=lambda r: r.created_at, reverse=True)

    async def mark_helpful(self, review_id: str) -> Optional[Review]:
        """Marker anmeldelse som hjælpsom."""
        async with self._lock:
            if review_id not in self._reviews:
                return None

            self._reviews[review_id].helpful_count += 1
            return self._reviews[review_id]

    async def flag_review(
        self,
        review_id: str,
        reason: str
    ) -> Optional[Review]:
        """Flag anmeldelse for gennemgang."""
        async with self._lock:
            if review_id not in self._reviews:
                return None

            self._reviews[review_id].status = ReviewStatus.FLAGGED
            return self._reviews[review_id]

    async def get_reviewer_stats(self, reviewer_id: str) -> Dict[str, Any]:
        """Hent statistik for en reviewer."""
        user_reviews = [r for r in self._reviews.values() if r.reviewer_id == reviewer_id]
        approved = [r for r in user_reviews if r.status == ReviewStatus.APPROVED]

        return {
            "total_reviews": len(user_reviews),
            "approved_reviews": len(approved),
            "total_helpful": sum(r.helpful_count for r in approved),
            "average_rating_given": sum(r.rating for r in approved) / len(approved) if approved else 0
        }


# =============================================================================
# DISCOVERY ENGINE
# =============================================================================

class DiscoveryEngine:
    """Søge- og opdagelsesmotor."""

    def __init__(
        self,
        marketplace: MarketplaceConnector,
        review_system: ReviewSystem
    ):
        self._marketplace = marketplace
        self._reviews = review_system
        self._search_history: Dict[str, List[str]] = {}  # user_id -> queries

    async def search(self, query: DiscoveryQuery) -> DiscoveryResponse:
        """Udfør søgning."""
        # Hent alle publicerede assets
        all_assets = [
            a for a in self._marketplace._assets.values()
            if a.status == AssetStatus.PUBLISHED
        ]

        # Filtrer
        filtered = all_assets

        if query.asset_types:
            filtered = [a for a in filtered if a.asset_type in query.asset_types]

        if query.tags:
            filtered = [a for a in filtered if any(t in a.tags for t in query.tags)]

        if query.pricing_models:
            filtered = [a for a in filtered if a.pricing_model in query.pricing_models]

        if query.min_rating > 0:
            filtered = [a for a in filtered if a.rating_avg >= query.min_rating]

        if query.max_price is not None:
            filtered = [a for a in filtered if a.price <= query.max_price]

        # Tekstsøgning
        if query.query:
            query_lower = query.query.lower()
            filtered = [
                a for a in filtered
                if query_lower in a.name.lower() or query_lower in a.description.lower()
            ]

        # Sortering
        if query.sort_by == DiscoverySort.POPULARITY:
            filtered.sort(key=lambda a: a.downloads, reverse=True)
        elif query.sort_by == DiscoverySort.RATING:
            filtered.sort(key=lambda a: a.rating_avg, reverse=True)
        elif query.sort_by == DiscoverySort.NEWEST:
            filtered.sort(key=lambda a: a.created_at, reverse=True)
        elif query.sort_by == DiscoverySort.PRICE_LOW:
            filtered.sort(key=lambda a: a.price)
        elif query.sort_by == DiscoverySort.PRICE_HIGH:
            filtered.sort(key=lambda a: a.price, reverse=True)

        total_count = len(filtered)

        # Paginering
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        paginated = filtered[start:end]

        # Opret resultater
        results = [
            SearchResult(
                asset=a,
                score=self._calculate_score(a, query.query)
            )
            for a in paginated
        ]

        # Beregn facets
        facets = self._calculate_facets(all_assets)

        return DiscoveryResponse(
            results=results,
            total_count=total_count,
            page=query.page,
            page_size=query.page_size,
            facets=facets
        )

    def _calculate_score(self, asset: Asset, query: str) -> float:
        """Beregn relevans-score."""
        score = 0.0

        if query:
            query_lower = query.lower()
            if query_lower in asset.name.lower():
                score += 10.0
            if query_lower in asset.description.lower():
                score += 5.0

        # Bonus for rating og downloads
        score += asset.rating_avg * 2
        score += min(asset.downloads / 100, 5.0)

        return round(score, 2)

    def _calculate_facets(
        self,
        assets: List[Asset]
    ) -> Dict[str, Dict[str, int]]:
        """Beregn facets for filtrering."""
        facets = {
            "asset_type": {},
            "pricing_model": {},
            "tags": {}
        }

        for asset in assets:
            # Asset type
            type_key = asset.asset_type.value
            facets["asset_type"][type_key] = facets["asset_type"].get(type_key, 0) + 1

            # Pricing model
            pricing_key = asset.pricing_model.value
            facets["pricing_model"][pricing_key] = facets["pricing_model"].get(pricing_key, 0) + 1

            # Tags
            for tag in asset.tags:
                facets["tags"][tag] = facets["tags"].get(tag, 0) + 1

        return facets

    async def get_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Asset]:
        """Hent anbefalinger for bruger."""
        # Simpel implementation baseret på brugerens køb
        purchases = await self._marketplace.get_user_purchases(user_id)

        if not purchases:
            # Returner trending hvis ingen køb
            return await self._get_popular(limit)

        # Find tags fra køb
        user_tags = set()
        for purchase in purchases:
            user_tags.update(purchase.tags)

        # Find assets med lignende tags
        all_assets = [
            a for a in self._marketplace._assets.values()
            if a.status == AssetStatus.PUBLISHED
            and a.asset_id not in {p.asset_id for p in purchases}
        ]

        scored = []
        for asset in all_assets:
            tag_overlap = len(set(asset.tags) & user_tags)
            if tag_overlap > 0:
                scored.append((asset, tag_overlap + asset.rating_avg))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [a for a, _ in scored[:limit]]

    async def _get_popular(self, limit: int) -> List[Asset]:
        """Hent populære assets."""
        all_assets = [
            a for a in self._marketplace._assets.values()
            if a.status == AssetStatus.PUBLISHED
        ]
        sorted_assets = sorted(all_assets, key=lambda a: a.downloads, reverse=True)
        return sorted_assets[:limit]

    async def record_search(self, user_id: str, query: str) -> None:
        """Registrer søgning i historik."""
        if user_id not in self._search_history:
            self._search_history[user_id] = []
        self._search_history[user_id].append(query)

    async def get_search_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[str]:
        """Hent søgehistorik."""
        history = self._search_history.get(user_id, [])
        return history[-limit:]


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

# Singleton instances
_marketplace_connector: Optional[MarketplaceConnector] = None
_community_hub: Optional[CommunityHub] = None
_asset_listing: Optional[AssetListing] = None
_review_system: Optional[ReviewSystem] = None
_discovery_engine: Optional[DiscoveryEngine] = None


def create_marketplace_connector() -> MarketplaceConnector:
    """Opret ny MarketplaceConnector instans."""
    return MarketplaceConnector()


def get_marketplace_connector() -> MarketplaceConnector:
    """Hent eller opret singleton MarketplaceConnector."""
    global _marketplace_connector
    if _marketplace_connector is None:
        _marketplace_connector = create_marketplace_connector()
    return _marketplace_connector


def create_community_hub() -> CommunityHub:
    """Opret ny CommunityHub instans."""
    return CommunityHub()


def get_community_hub() -> CommunityHub:
    """Hent eller opret singleton CommunityHub."""
    global _community_hub
    if _community_hub is None:
        _community_hub = create_community_hub()
    return _community_hub


def create_asset_listing(
    marketplace: Optional[MarketplaceConnector] = None
) -> AssetListing:
    """Opret ny AssetListing instans."""
    return AssetListing(marketplace or get_marketplace_connector())


def get_asset_listing() -> AssetListing:
    """Hent eller opret singleton AssetListing."""
    global _asset_listing
    if _asset_listing is None:
        _asset_listing = create_asset_listing()
    return _asset_listing


def create_review_system(
    marketplace: Optional[MarketplaceConnector] = None
) -> ReviewSystem:
    """Opret ny ReviewSystem instans."""
    return ReviewSystem(marketplace or get_marketplace_connector())


def get_review_system() -> ReviewSystem:
    """Hent eller opret singleton ReviewSystem."""
    global _review_system
    if _review_system is None:
        _review_system = create_review_system()
    return _review_system


def create_discovery_engine(
    marketplace: Optional[MarketplaceConnector] = None,
    review_system: Optional[ReviewSystem] = None
) -> DiscoveryEngine:
    """Opret ny DiscoveryEngine instans."""
    return DiscoveryEngine(
        marketplace or get_marketplace_connector(),
        review_system or get_review_system()
    )


def get_discovery_engine() -> DiscoveryEngine:
    """Hent eller opret singleton DiscoveryEngine."""
    global _discovery_engine
    if _discovery_engine is None:
        _discovery_engine = create_discovery_engine()
    return _discovery_engine
