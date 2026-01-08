"""
Storage Module
==============
Decentralized storage adapters.

Components:
- IPFSAdapter: IPFS integration
- ArweaveAdapter: Arweave permanent storage
- StorageRouter: Intelligent storage routing
"""

from cirkelline.web3.storage.ipfs_adapter import (
    IPFSAdapter,
    IPFSFile,
    PinStatus,
    get_ipfs_adapter,
)

from cirkelline.web3.storage.arweave_adapter import (
    ArweaveAdapter,
    ArweaveTransaction,
    get_arweave_adapter,
)

from cirkelline.web3.storage.storage_router import (
    StorageRouter,
    StorageResult,
    StorageProvider,
    StoragePolicy,
    get_storage_router,
)

from typing import Optional, Dict, Any


__all__ = [
    # IPFS
    'IPFSAdapter',
    'IPFSFile',
    'PinStatus',
    'get_ipfs_adapter',
    # Arweave
    'ArweaveAdapter',
    'ArweaveTransaction',
    'get_arweave_adapter',
    # Router
    'StorageRouter',
    'StorageResult',
    'StorageProvider',
    'StoragePolicy',
    'get_storage_router',
]
