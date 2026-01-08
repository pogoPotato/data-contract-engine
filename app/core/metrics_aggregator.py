from typing import List, Dict, Optional
from uuid import UUID
from datetime import date, datetime, timedelta
import logging
from sqlalchemy.orm import Session

from app.models.database import ValidationResult, Contract, QualityMetric
from app.models.schemas import DailyMetrics, TrendData


class MetricsAggregator:

    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)

    def calculate_daily_metrics(
        self, contract_id: UUID, target_date: date
    ) -> DailyMetrics:
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        validations = (
            self.db.query(ValidationResult)
            .filter(
                ValidationResult.contract_id == str(contract_id),
                ValidationResult.validated_at >= start_datetime,
                ValidationResult.validated_at < end_datetime,
            )
            .all()
        )

        if not validations:
            return self._create_empty_metrics(contract_id, target_date)

        total = len(validations)
        passed = sum(1 for v in validations if v.status == "PASS")
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        avg_execution_time = sum(v.execution_time_ms for v in validations) / total

        all_errors = []
        for v in validations:
            if v.status == "FAIL" and v.errors:
                all_errors.extend(v.errors)

        error_counts = self._count_errors(all_errors)
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        quality_score = self._calculate_quality_score(
            pass_rate=pass_rate,
            total_validations=total,
            error_variety=len(error_counts),
            contract_id=contract_id,
        )

        metrics = QualityMetric(
            contract_id=str(contract_id),
            metric_date=target_date,
            total_validations=total,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            avg_execution_time_ms=avg_execution_time,
            top_errors=dict(top_errors),
            quality_score=quality_score,
        )

        existing = (
            self.db.query(QualityMetric)
            .filter(
                QualityMetric.contract_id == str(contract_id),
                QualityMetric.metric_date == target_date,
            )
            .first()
        )

        if existing:
            for key, value in metrics.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
        else:
            self.db.add(metrics)

        self.db.commit()

        return DailyMetrics.from_orm(metrics)

    def _calculate_quality_score(
        self,
        pass_rate: float,
        total_validations: int,
        error_variety: int,
        contract_id: UUID,
    ) -> float:
        pass_rate_score = pass_rate * 0.7
        consistency_score = self._calculate_consistency_score(contract_id) * 0.2
        freshness_score = min(total_validations / 1000, 1.0) * 10

        quality_score = pass_rate_score + consistency_score + freshness_score

        if error_variety > 5:
            quality_score *= 0.95

        return round(quality_score, 2)

    def _calculate_consistency_score(self, contract_id: UUID) -> float:
        seven_days_ago = date.today() - timedelta(days=7)
        metrics = (
            self.db.query(QualityMetric)
            .filter(
                QualityMetric.contract_id == str(contract_id),
                QualityMetric.metric_date >= seven_days_ago,
            )
            .all()
        )

        if len(metrics) < 2:
            return 100

        pass_rates = [m.pass_rate for m in metrics]
        variance = self._calculate_variance(pass_rates)
        consistency_score = max(0, 100 - variance)

        return consistency_score

    def _calculate_variance(self, values: List[float]) -> float:
        if not values:
            return 0

        mean = sum(values) / len(values)
        squared_diffs = [(x - mean) ** 2 for x in values]
        variance = sum(squared_diffs) / len(values)

        return variance

    def get_trend_data(self, contract_id: UUID, days: int = 30) -> TrendData:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        metrics = (
            self.db.query(QualityMetric)
            .filter(
                QualityMetric.contract_id == str(contract_id),
                QualityMetric.metric_date >= start_date,
                QualityMetric.metric_date <= end_date,
            )
            .order_by(QualityMetric.metric_date)
            .all()
        )

        if not metrics:
            return self._create_empty_trend(contract_id, days)

        dates = [m.metric_date for m in metrics]
        pass_rates = [m.pass_rate for m in metrics]
        volumes = [m.total_validations for m in metrics]
        quality_scores = [m.quality_score for m in metrics]

        pass_rate_trend = self._calculate_trend(pass_rates)
        volume_trend = self._calculate_trend(volumes)
        quality_trend = self._calculate_trend(quality_scores)

        return TrendData(
            dates=dates,
            pass_rates=pass_rates,
            volumes=volumes,
            quality_scores=quality_scores,
            pass_rate_trend=pass_rate_trend,
            volume_trend=volume_trend,
            quality_trend=quality_trend,
            days=days,
        )

    def _calculate_trend(self, values: List[float]) -> str:
        if len(values) < 2:
            return "STABLE"

        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "STABLE"

        slope = numerator / denominator

        if slope > 0.5:
            return "INCREASING"
        elif slope < -0.5:
            return "DECREASING"
        else:
            return "STABLE"

    def aggregate_daily_metrics(self, target_date: Optional[date] = None):
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        contracts = self.db.query(Contract).filter(Contract.is_active == True).all()

        self.logger.info(
            f"Aggregating metrics for {len(contracts)} contracts on {target_date}"
        )

        for contract in contracts:
            try:
                metrics = self.calculate_daily_metrics(contract.id, target_date)
                self.logger.info(
                    f"Contract {contract.name}: {metrics.pass_rate:.2f}% pass rate"
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to aggregate metrics for {contract.name}: {e}"
                )

    def _count_errors(self, errors: List) -> Dict[str, int]:
        from collections import Counter

        error_types = [err.get("error_type", "UNKNOWN") for err in errors]
        return dict(Counter(error_types))

    def _create_empty_metrics(
        self, contract_id: UUID, target_date: date
    ) -> DailyMetrics:
        return DailyMetrics(
            contract_id=str(contract_id),
            metric_date=target_date,
            total_validations=0,
            passed=0,
            failed=0,
            pass_rate=0.0,
            avg_execution_time_ms=0.0,
            top_errors={},
            quality_score=0.0,
        )

    def _create_empty_trend(self, contract_id: UUID, days: int) -> TrendData:
        return TrendData(
            dates=[],
            pass_rates=[],
            volumes=[],
            quality_scores=[],
            pass_rate_trend="STABLE",
            volume_trend="STABLE",
            quality_trend="STABLE",
            days=days,
        )
