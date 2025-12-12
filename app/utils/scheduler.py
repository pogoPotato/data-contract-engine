from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime, timedelta

from app.database import get_db_session
from app.core.metrics_aggregator import MetricsAggregator
from app.models.database import ValidationResult


logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def setup_scheduler():
    scheduler.add_job(
        aggregate_daily_metrics_job,
        CronTrigger(hour=1, minute=0),
        id='daily_metrics',
        name='Aggregate daily metrics',
        replace_existing=True
    )
    
    scheduler.add_job(
        cleanup_old_data_job,
        CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='cleanup_data',
        name='Clean up old data',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started")


async def aggregate_daily_metrics_job():
    logger.info("Starting daily metrics aggregation")
    
    db = get_db_session()
    aggregator = MetricsAggregator(db)
    
    try:
        aggregator.aggregate_daily_metrics()
        logger.info("Daily metrics aggregation completed")
    except Exception as e:
        logger.error(f"Metrics aggregation failed: {e}")
    finally:
        db.close()


async def cleanup_old_data_job():
    logger.info("Starting data cleanup")
    
    db = get_db_session()
    retention_days = 90
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    try:
        deleted_count = db.query(ValidationResult).filter(
            ValidationResult.validated_at < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old validation results")
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()