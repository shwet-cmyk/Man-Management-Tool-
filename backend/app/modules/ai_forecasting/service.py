from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.wm_customer_score import WmCustomerScore
from app.models.wm_forecast import WmForecast
from app.models.wm_sales_history import WmSalesHistory
from app.modules.ai_forecasting.schemas import SalesHistoryIngestRequest, TargetGenerateRequest


class AiForecastingService:
    def __init__(self, db: Session):
        self.db = db

    def ingest_sales_history(self, payload: SalesHistoryIngestRequest):
        row = WmSalesHistory(
            sales_date=datetime(payload.sales_date.year, payload.sales_date.month, payload.sales_date.day),
            product_id=payload.product_id,
            customer_id=payload.customer_id,
            quantity=payload.quantity,
            revenue=payload.revenue,
            branch_id=payload.branch_id,
        )
        self.db.add(row)
        self.db.commit()
        return {"sales_history_id": row.sales_history_id}

    def get_forecast(self, forecast_type: str, period: str, entity_id: int | None = None):
        if period not in {"weekly", "monthly", "yearly"}:
            raise HTTPException(status_code=422, detail="Invalid period")

        grouped = self._group_sales(forecast_type, entity_id)
        if len(grouped) < 6:
            return {"forecast": [], "model": "FALLBACK", "reason": "Minimum 6 data points required"}

        slope, intercept = self._linear_fit([x[0] for x in grouped], [x[1] for x in grouped])
        horizon = 6 if period in {"weekly", "monthly"} else 3
        last_index = grouped[-1][0]
        out = []
        for i in range(1, horizon + 1):
            idx = last_index + i
            val = max((slope * idx) + intercept, 0)
            out.append({"index": idx, "predicted_value": round(val, 2)})
            self.db.add(
                WmForecast(
                    entity_type=forecast_type.upper(),
                    entity_id=entity_id or 0,
                    forecast_date=datetime.utcnow() + timedelta(days=30 * i),
                    predicted_value=val,
                    model_used="LINEAR_TREND",
                )
            )
        self.db.commit()
        return {"forecast": out, "model": "LINEAR_TREND"}

    def get_customer_prediction(self, customer_id: int):
        score = self.db.query(WmCustomerScore).filter(WmCustomerScore.customer_id == customer_id).first()
        if score:
            return {
                "customer_id": customer_id,
                "churn_score": float(score.churn_score),
                "repeat_probability": float(score.repeat_probability),
                "lifetime_value": float(score.lifetime_value),
            }

        sales = (
            self.db.query(WmSalesHistory)
            .filter(WmSalesHistory.customer_id == customer_id)
            .order_by(WmSalesHistory.sales_date.desc())
            .all()
        )
        if not sales:
            return {"customer_id": customer_id, "churn_score": 0.7, "repeat_probability": 0.2, "lifetime_value": 0.0}

        last_purchase_days = (datetime.utcnow() - sales[0].sales_date).days
        churn = self._churn_score(last_purchase_days)
        repeat = round(max(1 - churn, 0.05), 4)
        ltv = float(sum(float(x.revenue) for x in sales))

        row = WmCustomerScore(customer_id=customer_id, churn_score=churn, repeat_probability=repeat, lifetime_value=ltv)
        self.db.add(row)
        self.db.commit()
        return {"customer_id": customer_id, "churn_score": churn, "repeat_probability": repeat, "lifetime_value": ltv}

    def generate_targets(self, payload: TargetGenerateRequest):
        forecast = self.get_forecast(payload.entity_type, payload.period)
        vals = [x["predicted_value"] for x in forecast.get("forecast", [])]
        if not vals:
            return {"targets": [], "reason": "Insufficient data"}
        avg = sum(vals) / len(vals)
        return {
            "targets": [
                {"segment": "base", "target": round(avg, 2)},
                {"segment": "stretch", "target": round(avg * 1.15, 2)},
            ],
            "period": payload.period,
            "entity_type": payload.entity_type,
        }

    def _group_sales(self, forecast_type: str, entity_id: int | None):
        query = self.db.query(WmSalesHistory)
        if forecast_type == "product" and entity_id is not None:
            query = query.filter(WmSalesHistory.product_id == entity_id)
        if forecast_type == "branch" and entity_id is not None:
            query = query.filter(WmSalesHistory.branch_id == entity_id)

        rows = query.order_by(WmSalesHistory.sales_date.asc()).all()
        grouped = {}
        for row in rows:
            key = row.sales_date.strftime("%Y-%m")
            grouped.setdefault(key, 0.0)
            grouped[key] += float(row.revenue)
        return list(enumerate(grouped.values(), start=1))

    @staticmethod
    def _linear_fit(xs: list[int], ys: list[float]):
        n = len(xs)
        sx = sum(xs)
        sy = sum(ys)
        sxy = sum(x * y for x, y in zip(xs, ys))
        sxx = sum(x * x for x in xs)
        den = (n * sxx) - (sx * sx)
        if den == 0:
            return 0.0, ys[-1] if ys else 0.0
        slope = ((n * sxy) - (sx * sy)) / den
        intercept = (sy - (slope * sx)) / n
        return slope, intercept

    @staticmethod
    def _churn_score(last_purchase_days: int):
        if last_purchase_days > 90:
            return 0.9
        if last_purchase_days > 60:
            return 0.6
        if last_purchase_days > 30:
            return 0.4
        return 0.2
