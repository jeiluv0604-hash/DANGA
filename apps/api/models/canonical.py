# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Integer, Float, Boolean
from apps.api.database import Base

class CanonicalPOSModel(Base):
    __tablename__ = 'canonical_pos_transactions'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    import_id = Column(String, index=True, nullable=False)
    business_date = Column(String, index=True, nullable=False)
    transaction_time = Column(String, nullable=True)
    receipt_id = Column(String, index=True, nullable=False)
    table_id = Column(String, nullable=True)
    menu_id = Column(String, index=True, nullable=False)
    menu_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    gross_sales = Column(Float, nullable=True)
    discount = Column(Float, default=0.0)
    net_sales = Column(Float, nullable=False)
    guests = Column(Integer, nullable=True)
    payment_type = Column(String, nullable=True)
    cancelled = Column(Boolean, default=False)
    void_reason = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    order_type = Column(String, nullable=True)
    source_system = Column(String, default='GENERIC')
    source_file = Column(String, nullable=False)
    source_row = Column(Integer, nullable=False)
    dataset_type = Column(String, default='SHADOW_REAL')
    verification_status = Column(String, default='UNVERIFIED')

class CanonicalAttendanceModel(Base):
    __tablename__ = 'canonical_attendance_records'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    import_id = Column(String, index=True, nullable=False)
    business_date = Column(String, index=True, nullable=False)
    employee_id = Column(String, index=True, nullable=False)
    department = Column(String, nullable=False)
    role = Column(String, nullable=False)
    clock_in = Column(String, nullable=False)
    clock_out = Column(String, nullable=False)
    worked_minutes = Column(Integer, nullable=False)
    regular_minutes = Column(Integer, nullable=False)
    overtime_minutes = Column(Integer, default=0)
    labor_cost = Column(Float, nullable=True)
    source_system = Column(String, default='GENERIC')
    source_file = Column(String, nullable=False)
    source_row = Column(Integer, nullable=False)
    dataset_type = Column(String, default='SHADOW_REAL')
    verification_status = Column(String, default='UNVERIFIED')

class CanonicalPurchaseModel(Base):
    __tablename__ = 'canonical_purchase_records'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    import_id = Column(String, index=True, nullable=False)
    purchase_date = Column(String, index=True, nullable=False)
    supplier_id = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)
    item_id = Column(String, index=True, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    source_amount = Column(Float, nullable=True)
    calculated_amount = Column(Float, nullable=True)
    invoice_id = Column(String, nullable=True)
    source_system = Column(String, default='GENERIC')
    source_file = Column(String, nullable=False)
    source_row = Column(Integer, nullable=False)
    dataset_type = Column(String, default='SHADOW_REAL')
    verification_status = Column(String, default='UNVERIFIED')

class CanonicalInventoryModel(Base):
    __tablename__ = 'canonical_inventory_records'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    import_id = Column(String, index=True, nullable=False)
    business_date = Column(String, index=True, nullable=False)
    item_id = Column(String, index=True, nullable=False)
    item_name = Column(String, nullable=False)
    opening_qty = Column(Float, nullable=False)
    incoming_qty = Column(Float, nullable=False)
    sold_qty = Column(Float, nullable=False)
    service_qty = Column(Float, nullable=True)
    waste_qty = Column(Float, nullable=True)
    staff_meal_qty = Column(Float, nullable=True)
    transfer_qty = Column(Float, nullable=True)
    theory_end_qty = Column(Float, nullable=False)
    actual_end_qty = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    source_system = Column(String, default='GENERIC')
    source_file = Column(String, nullable=False)
    source_row = Column(Integer, nullable=False)
    dataset_type = Column(String, default='SHADOW_REAL')
    verification_status = Column(String, default='UNVERIFIED')
