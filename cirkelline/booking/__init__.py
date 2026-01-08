"""
Cirkelline Booking Module
=========================

High-performance booking system with SQS queue processing.
Supports 1M+ bookings overnight with batch processing.

Princip: "Man behøver ikke se for at vide - vi bygger så alt er gennemsigtigt."
"""

from cirkelline.booking.queue_worker import (
    # Enums
    BookingStatus,

    # Config
    QueueConfig,
    BookingMessage,
    WorkerStats,

    # Clients
    QueueClient,
    LocalQueueClient,
    SQSQueueClient,

    # Processors
    BookingProcessor,
    DatabaseBookingProcessor,

    # Worker
    BookingWorker,

    # Factory
    get_booking_worker,
    start_booking_worker,
    stop_booking_worker,
)

__all__ = [
    # Enums
    "BookingStatus",

    # Config
    "QueueConfig",
    "BookingMessage",
    "WorkerStats",

    # Clients
    "QueueClient",
    "LocalQueueClient",
    "SQSQueueClient",

    # Processors
    "BookingProcessor",
    "DatabaseBookingProcessor",

    # Worker
    "BookingWorker",

    # Factory
    "get_booking_worker",
    "start_booking_worker",
    "stop_booking_worker",
]
