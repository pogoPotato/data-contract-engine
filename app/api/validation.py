async def process_file_background(
    contract_id: UUID,
    file_path: str,
    file_type: str,
    batch_id: UUID
):
    from app.core.batch_processor import BatchProcessor
    from app.database import get_db_session
    from app.models.database import BatchSummary
    import logging
    import traceback
    import os
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    db = get_db_session()
    
    try:
        logger.info(f"[BATCH {batch_id}] Starting background processing")
        logger.info(f"[BATCH {batch_id}] Contract: {contract_id}, File: {file_path}, Type: {file_type}")
        
        if not os.path.exists(file_path):
            logger.error(f"[BATCH {batch_id}] File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        processor = BatchProcessor(db)
        
        logger.info(f"[BATCH {batch_id}] Calling processor.process_file()")
        result = await processor.process_file(
            contract_id=contract_id,
            file_path=file_path,
            file_type=file_type,
            batch_id=batch_id
        )
        
        logger.info(f"[BATCH {batch_id}] Processing completed")
        logger.info(f"[BATCH {batch_id}] Result: {result.passed}/{result.total_records} passed")
        
        summary = db.query(BatchSummary).filter(
            BatchSummary.batch_id == str(batch_id)
        ).first()
        
        if summary:
            logger.info(f"[BATCH {batch_id}] BatchSummary verified in database")
        else:
            logger.error(f"[BATCH {batch_id}] BatchSummary NOT found in database!")
        
    except Exception as e:
        logger.error(f"[BATCH {batch_id}] ERROR: {str(e)}")
        logger.error(f"[BATCH {batch_id}] Full traceback:")
        logger.error(traceback.format_exc())
        
        try:
            error_summary = BatchSummary(
                batch_id=str(batch_id),
                contract_id=str(contract_id),
                total_records=0,
                passed=0,
                failed=0,
                pass_rate=0.0,
                execution_time_ms=0.0,
                errors_summary={"error": str(e), "traceback": traceback.format_exc()},
                processed_at=datetime.utcnow()
            )
            db.add(error_summary)
            db.commit()
            logger.info(f"[BATCH {batch_id}] Error summary stored")
        except Exception as db_err:
            logger.error(f"[BATCH {batch_id}] Failed to store error summary: {str(db_err)}")
        
        db.rollback()
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"[BATCH {batch_id}] Removed temporary file: {file_path}")
            except Exception as e:
                logger.error(f"[BATCH {batch_id}] Error removing file: {str(e)}")
        
        db.close()
        logger.info(f"[BATCH {batch_id}] Background task completed")