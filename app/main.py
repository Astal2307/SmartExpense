from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .ml import classify_text, load_model
from .models import Transaction
from .schemas import (
    AnalyticsByCategory,
    AnalyticsByMonth,
    AnalyticsResponse,
    TransactionCreate,
    TransactionRead,
)


app = FastAPI(title="SmartExpense API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

model = load_model()


@app.post("/api/v1/transactions", response_model=TransactionRead)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
):
    category, confidence = classify_text(model, payload.description)

    db_obj = Transaction(
        description=payload.description,
        amount=payload.amount,
        date=payload.date,
        category=category,
        model_confidence=confidence,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@app.post("/api/v1/transactions/upload", response_model=List[TransactionRead])
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Ожидается CSV с заголовками: description,amount,date
    date в ISO-формате, например 2025-06-01T12:00:00.
    """
    import csv
    import io

    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(status_code=400, detail="Ожидается CSV-файл")

    content = await file.read()
    text_stream = io.StringIO(content.decode("utf-8"))
    reader = csv.DictReader(text_stream)

    created: List[Transaction] = []
    for row in reader:
        try:
            description = row["description"]
            amount = Decimal(row["amount"])
            date = datetime.fromisoformat(row["date"])
        except Exception:
            # пропускаем битые строки
            continue

        category, confidence = classify_text(model, description)

        db_obj = Transaction(
            description=description,
            amount=amount,
            date=date,
            category=category,
            model_confidence=confidence,
        )
        db.add(db_obj)
        created.append(db_obj)

    db.commit()
    for obj in created:
        db.refresh(obj)

    return created


@app.get("/api/v1/transactions", response_model=List[TransactionRead])
def list_transactions(
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)
    if category:
        query = query.filter(Transaction.category == category)

    transactions = (
        query.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()
    )
    return transactions


@app.delete("/api/v1/transactions/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    db.delete(tx)
    db.commit()
    return


@app.get("/api/v1/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    # total_spent и count
    total_spent, tx_count = db.query(
        func.coalesce(func.sum(Transaction.amount), 0),
        func.count(Transaction.id),
    ).one()

    # by_category
    cat_rows = (
        db.query(
            Transaction.category.label("category"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(Transaction.id).label("count"),
            func.coalesce(func.avg(Transaction.amount), 0).label("avg_amount"),
        )
        .group_by(Transaction.category)
        .all()
    )

    by_category = [
        AnalyticsByCategory(
            category=row.category,
            total_amount=row.total_amount,
            count=row.count,
            avg_amount=row.avg_amount,
        )
        for row in cat_rows
    ]

    # by_month (формат YYYY-MM)
    month_rows = (
        db.query(
            func.to_char(Transaction.date, "YYYY-MM").label("month"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(Transaction.id).label("count"),
        )
        .group_by(func.to_char(Transaction.date, "YYYY-MM"))
        .order_by(func.to_char(Transaction.date, "YYYY-MM"))
        .all()
    )

    by_month = [
        AnalyticsByMonth(
            month=row.month,
            total_amount=row.total_amount,
            count=row.count,
        )
        for row in month_rows
    ]

    return AnalyticsResponse(
        total_spent=total_spent,
        transaction_count=tx_count,
        by_category=by_category,
        by_month=by_month,
    )

