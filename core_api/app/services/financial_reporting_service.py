import io
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.affiliate import AffiliateCommission, CommissionStatus
from app.models.user import User
from app.models.plan import Plan
from app.models.panel import Panel


class ReportType(str, Enum):
    """Enumeration of available report types"""
    ORDERS = "orders"
    TRANSACTIONS = "transactions"
    COMMISSIONS = "commissions"
    REVENUE = "revenue"
    SUBSCRIPTION = "subscription"


class ReportFormat(str, Enum):
    """Enumeration of available report output formats"""
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class TimeFrame(str, Enum):
    """Enumeration of available time frames for reports"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class FinancialReportingService:
    """
    Service for generating financial reports and exporting data to Excel/CSV.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_date_range(self, time_frame: TimeFrame, start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        Calculate the date range based on the specified time frame.
        
        Args:
            time_frame: The time frame for the report
            start_date: Custom start date (only used when time_frame is CUSTOM)
            end_date: Custom end date (only used when time_frame is CUSTOM)
            
        Returns:
            A tuple of (start_date, end_date)
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if time_frame == TimeFrame.TODAY:
            return today, today + timedelta(days=1) - timedelta(microseconds=1)
            
        elif time_frame == TimeFrame.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday + timedelta(days=1) - timedelta(microseconds=1)
            
        elif time_frame == TimeFrame.LAST_7_DAYS:
            return today - timedelta(days=7), today + timedelta(days=1) - timedelta(microseconds=1)
            
        elif time_frame == TimeFrame.LAST_30_DAYS:
            return today - timedelta(days=30), today + timedelta(days=1) - timedelta(microseconds=1)
            
        elif time_frame == TimeFrame.THIS_MONTH:
            return today.replace(day=1), today.replace(day=1, month=today.month+1 if today.month < 12 else 1, 
                                                    year=today.year if today.month < 12 else today.year+1) - timedelta(microseconds=1)
            
        elif time_frame == TimeFrame.LAST_MONTH:
            last_month = today.replace(day=1) - timedelta(days=1)
            start = last_month.replace(day=1)
            end = today.replace(day=1) - timedelta(microseconds=1)
            return start, end
            
        elif time_frame == TimeFrame.THIS_YEAR:
            return today.replace(month=1, day=1), today.replace(year=today.year+1, month=1, day=1) - timedelta(microseconds=1)
            
        elif time_frame == TimeFrame.CUSTOM:
            if not start_date or not end_date:
                raise HTTPException(status_code=400, detail="Custom time frame requires both start_date and end_date")
            
            # Add a full day to end_date to make it inclusive
            adjusted_end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start_date, adjusted_end_date
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid time frame: {time_frame}")

    def generate_orders_report(self, time_frame: TimeFrame, 
                              start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None,
                              payment_method: Optional[PaymentMethod] = None,
                              status: Optional[OrderStatus] = None) -> pd.DataFrame:
        """
        Generate a report of orders within the specified date range.
        
        Args:
            time_frame: The time frame for the report
            start_date: Custom start date (for CUSTOM time frame)
            end_date: Custom end date (for CUSTOM time frame)
            payment_method: Filter by payment method (optional)
            status: Filter by order status (optional)
            
        Returns:
            DataFrame containing the orders report
        """
        start, end = self.get_date_range(time_frame, start_date, end_date)
        
        # Build the base query with date range filter
        query = self.db.query(
            Order,
            User.username,
            User.phone_number,
            Plan.name.label("plan_name"),
            Panel.name.label("panel_name")
        ).join(
            User, Order.user_id == User.id
        ).outerjoin(
            Plan, Order.plan_id == Plan.id
        ).outerjoin(
            Panel, Order.panel_id == Panel.id
        ).filter(
            Order.created_at.between(start, end)
        )
        
        # Apply additional filters
        if payment_method:
            query = query.filter(Order.payment_method == payment_method)
            
        if status:
            query = query.filter(Order.status == status)
            
        # Execute the query
        results = query.order_by(desc(Order.created_at)).all()
        
        # Convert to DataFrame
        data = []
        for result in results:
            order = result[0]
            data.append({
                "order_id": order.order_id,
                "user_id": order.user_id,
                "username": result.username,
                "phone_number": result.phone_number,
                "plan_name": result.plan_name,
                "panel_name": result.panel_name,
                "amount": order.amount,
                "discount_amount": order.discount_amount,
                "final_amount": order.final_amount,
                "status": order.status.value if order.status else None,
                "payment_method": order.payment_method.value if order.payment_method else None,
                "created_at": order.created_at,
                "paid_at": order.paid_at,
                "confirmed_at": order.confirmed_at
            })
            
        return pd.DataFrame(data)
        
    def generate_transactions_report(self, time_frame: TimeFrame,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None,
                                    transaction_type: Optional[TransactionType] = None,
                                    status: Optional[TransactionStatus] = None) -> pd.DataFrame:
        """
        Generate a report of transactions within the specified date range.
        
        Args:
            time_frame: The time frame for the report
            start_date: Custom start date (for CUSTOM time frame)
            end_date: Custom end date (for CUSTOM time frame)
            transaction_type: Filter by transaction type (optional)
            status: Filter by transaction status (optional)
            
        Returns:
            DataFrame containing the transactions report
        """
        start, end = self.get_date_range(time_frame, start_date, end_date)
        
        # Build the base query with date range filter
        query = self.db.query(
            Transaction,
            User.username,
            User.phone_number
        ).join(
            User, Transaction.user_id == User.id
        ).filter(
            Transaction.created_at.between(start, end)
        )
        
        # Apply additional filters
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
            
        if status:
            query = query.filter(Transaction.status == status)
            
        # Execute the query
        results = query.order_by(desc(Transaction.created_at)).all()
        
        # Convert to DataFrame
        data = []
        for result in results:
            transaction = result[0]
            data.append({
                "transaction_id": transaction.transaction_id,
                "user_id": transaction.user_id,
                "username": result.username,
                "phone_number": result.phone_number,
                "amount": transaction.amount,
                "balance_after": transaction.balance_after,
                "type": transaction.type.value if transaction.type else None,
                "status": transaction.status.value if transaction.status else None,
                "payment_method": transaction.payment_method,
                "payment_reference": transaction.payment_reference,
                "created_at": transaction.created_at,
                "description": transaction.description,
                "order_id": transaction.order_id
            })
            
        return pd.DataFrame(data)
        
    def generate_commissions_report(self, time_frame: TimeFrame,
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None,
                                  status: Optional[CommissionStatus] = None) -> pd.DataFrame:
        """
        Generate a report of affiliate commissions within the specified date range.
        
        Args:
            time_frame: The time frame for the report
            start_date: Custom start date (for CUSTOM time frame)
            end_date: Custom end date (for CUSTOM time frame)
            status: Filter by commission status (optional)
            
        Returns:
            DataFrame containing the commissions report
        """
        start, end = self.get_date_range(time_frame, start_date, end_date)
        
        # Build the base query with date range filter
        query = self.db.query(
            AffiliateCommission,
            User.username.label("affiliate_username"),
            User.phone_number.label("affiliate_phone")
        ).join(
            User, AffiliateCommission.user_id == User.id
        ).filter(
            AffiliateCommission.created_at.between(start, end)
        )
        
        # Apply additional filters
        if status:
            query = query.filter(AffiliateCommission.status == status.value)
            
        # Execute the query
        results = query.order_by(desc(AffiliateCommission.created_at)).all()
        
        # Convert to DataFrame
        data = []
        for result in results:
            commission = result[0]
            data.append({
                "commission_id": commission.id,
                "affiliate_id": commission.user_id,
                "affiliate_username": result.affiliate_username,
                "affiliate_phone": result.affiliate_phone,
                "referred_user_id": commission.referrer_id,
                "order_id": commission.order_id,
                "amount": commission.amount,
                "percentage": commission.percentage,
                "status": commission.status,
                "type": commission.commission_type,
                "created_at": commission.created_at,
                "paid_at": commission.paid_at,
                "description": commission.description
            })
            
        return pd.DataFrame(data)
        
    def generate_revenue_report(self, time_frame: TimeFrame,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Generate a revenue summary report aggregated by day.
        
        Args:
            time_frame: The time frame for the report
            start_date: Custom start date (for CUSTOM time frame)
            end_date: Custom end date (for CUSTOM time frame)
            
        Returns:
            DataFrame containing the revenue report
        """
        start, end = self.get_date_range(time_frame, start_date, end_date)
        
        # Query to get daily order totals for confirmed orders
        confirmed_orders = self.db.query(
            func.date(Order.confirmed_at).label("date"),
            func.count(Order.id).label("orders_count"),
            func.sum(Order.final_amount).label("total_revenue")
        ).filter(
            Order.status == OrderStatus.CONFIRMED,
            Order.confirmed_at.between(start, end)
        ).group_by(
            func.date(Order.confirmed_at)
        ).all()
        
        # Query to get daily transaction totals (deposits)
        deposits = self.db.query(
            func.date(Transaction.created_at).label("date"),
            func.count(Transaction.id).label("deposits_count"),
            func.sum(Transaction.amount).label("total_deposits")
        ).filter(
            Transaction.type == TransactionType.DEPOSIT,
            Transaction.status == TransactionStatus.COMPLETED,
            Transaction.created_at.between(start, end)
        ).group_by(
            func.date(Transaction.created_at)
        ).all()
        
        # Query to get commissions paid
        commissions = self.db.query(
            func.date(AffiliateCommission.created_at).label("date"),
            func.count(AffiliateCommission.id).label("commissions_count"),
            func.sum(AffiliateCommission.amount).label("total_commissions")
        ).filter(
            AffiliateCommission.status == CommissionStatus.APPROVED.value,
            AffiliateCommission.created_at.between(start, end)
        ).group_by(
            func.date(AffiliateCommission.created_at)
        ).all()
        
        # Create dictionary of dates within the range
        date_range = pd.date_range(start=start.date(), end=end.date(), freq='D')
        daily_data = {date.strftime('%Y-%m-%d'): {
            "date": date,
            "orders_count": 0,
            "total_revenue": 0,
            "deposits_count": 0,
            "total_deposits": 0,
            "commissions_count": 0,
            "total_commissions": 0
        } for date in date_range}
        
        # Fill in order data
        for date, count, total in confirmed_orders:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in daily_data:
                daily_data[date_str]["orders_count"] = count
                daily_data[date_str]["total_revenue"] = float(total) if total else 0
                
        # Fill in deposit data
        for date, count, total in deposits:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in daily_data:
                daily_data[date_str]["deposits_count"] = count
                daily_data[date_str]["total_deposits"] = float(total) if total else 0
                
        # Fill in commission data
        for date, count, total in commissions:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in daily_data:
                daily_data[date_str]["commissions_count"] = count
                daily_data[date_str]["total_commissions"] = float(total) if total else 0
        
        # Calculate net revenue
        for data in daily_data.values():
            data["net_revenue"] = data["total_revenue"] - data["total_commissions"]
            
        # Convert to DataFrame and sort by date
        df = pd.DataFrame(list(daily_data.values()))
        if not df.empty:
            df = df.sort_values(by="date")
            
        return df
        
    def generate_subscription_report(self, time_frame: TimeFrame,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Generate a report of subscription plans and their active users.
        
        Args:
            time_frame: The time frame for the report (used for newly created subscriptions)
            start_date: Custom start date (for CUSTOM time frame)
            end_date: Custom end date (for CUSTOM time frame)
            
        Returns:
            DataFrame containing the subscription report
        """
        # For this report, we'll get all active subscriptions, but filter new ones by date range
        start, end = self.get_date_range(time_frame, start_date, end_date)
        
        # Create SQL query for plan-based subscription summary
        plan_summary = self.db.execute("""
            SELECT 
                p.id AS plan_id,
                p.name AS plan_name,
                COUNT(s.id) AS total_subscriptions,
                COUNT(CASE WHEN s.status = 'active' THEN 1 END) AS active_subscriptions,
                COUNT(CASE WHEN s.is_frozen = 1 THEN 1 END) AS frozen_subscriptions,
                COUNT(CASE WHEN s.auto_renew = 1 THEN 1 END) AS auto_renew_enabled,
                COUNT(CASE WHEN s.created_at BETWEEN :start AND :end THEN 1 END) AS new_subscriptions,
                p.price AS plan_price,
                p.traffic_limit_gb AS traffic_limit,
                p.max_users AS max_users,
                p.discount_percentage AS discount_percentage
            FROM
                plans p
            LEFT JOIN
                subscriptions s ON p.id = s.plan_id
            GROUP BY
                p.id, p.name
            ORDER BY
                total_subscriptions DESC
        """, {"start": start, "end": end})
        
        # Convert to list of dictionaries
        result_data = []
        for row in plan_summary:
            result_data.append({
                "plan_id": row.plan_id,
                "plan_name": row.plan_name,
                "total_subscriptions": row.total_subscriptions,
                "active_subscriptions": row.active_subscriptions,
                "frozen_subscriptions": row.frozen_subscriptions,
                "auto_renew_enabled": row.auto_renew_enabled,
                "new_subscriptions": row.new_subscriptions,
                "plan_price": row.plan_price,
                "traffic_limit": row.traffic_limit,
                "max_users": row.max_users,
                "discount_percentage": row.discount_percentage,
                "revenue_potential": row.plan_price * row.active_subscriptions if row.plan_price and row.active_subscriptions else 0
            })
            
        return pd.DataFrame(result_data)

    def export_report(self, report_type: ReportType, report_format: ReportFormat, time_frame: TimeFrame,
                     start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                     **kwargs) -> Tuple[bytes, str]:
        """
        Generate and export a report in the specified format.
        
        Args:
            report_type: Type of report to generate
            report_format: Format to export the report in
            time_frame: Time frame for the report
            start_date: Custom start date (for CUSTOM time frame)
            end_date: Custom end date (for CUSTOM time frame)
            **kwargs: Additional filters specific to each report type
            
        Returns:
            Tuple of (file_content, filename)
        """
        # Generate the appropriate report
        if report_type == ReportType.ORDERS:
            df = self.generate_orders_report(
                time_frame, start_date, end_date,
                payment_method=kwargs.get('payment_method'),
                status=kwargs.get('status')
            )
            report_name = "orders_report"
            
        elif report_type == ReportType.TRANSACTIONS:
            df = self.generate_transactions_report(
                time_frame, start_date, end_date,
                transaction_type=kwargs.get('transaction_type'),
                status=kwargs.get('status')
            )
            report_name = "transactions_report"
            
        elif report_type == ReportType.COMMISSIONS:
            df = self.generate_commissions_report(
                time_frame, start_date, end_date,
                status=kwargs.get('status')
            )
            report_name = "commissions_report"
            
        elif report_type == ReportType.REVENUE:
            df = self.generate_revenue_report(time_frame, start_date, end_date)
            report_name = "revenue_report"
            
        elif report_type == ReportType.SUBSCRIPTION:
            df = self.generate_subscription_report(time_frame, start_date, end_date)
            report_name = "subscription_report"
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}")
            
        # Handle empty results
        if df.empty:
            df = pd.DataFrame({"No Data": ["No records found for the selected criteria"]})
            
        # Get current time for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export in the requested format
        if report_format == ReportFormat.EXCEL:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=report_type.value.capitalize())
                
                # Add metadata sheet
                metadata = pd.DataFrame({
                    "Report Type": [report_type.value],
                    "Time Frame": [time_frame.value],
                    "Start Date": [start_date.strftime("%Y-%m-%d %H:%M:%S") if start_date else "N/A"],
                    "End Date": [end_date.strftime("%Y-%m-%d %H:%M:%S") if end_date else "N/A"],
                    "Generated At": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                })
                
                for key, value in kwargs.items():
                    if value:
                        metadata[key] = [str(value.value if hasattr(value, 'value') else value)]
                        
                metadata.to_excel(writer, index=False, sheet_name="Metadata")
                
                # Auto-adjust column widths
                for sheet in writer.sheets.values():
                    for col in sheet.columns:
                        max_length = 0
                        column = col[0].column_letter
                        for cell in col:
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))
                        adjusted_width = (max_length + 2) * 1.2
                        sheet.column_dimensions[column].width = min(adjusted_width, 50)
                
            output.seek(0)
            return output.getvalue(), f"{report_name}_{timestamp}.xlsx"
            
        elif report_format == ReportFormat.CSV:
            output = io.StringIO()
            df.to_csv(output, index=False)
            return output.getvalue().encode('utf-8'), f"{report_name}_{timestamp}.csv"
            
        elif report_format == ReportFormat.JSON:
            return df.to_json(orient='records').encode('utf-8'), f"{report_name}_{timestamp}.json"
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid report format: {report_format}")
            
    def get_summary_dashboard_data(self) -> Dict[str, Any]:
        """
        Get summary data for the financial dashboard.
        
        Returns:
            Dictionary with financial summary metrics
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(microseconds=1)
        
        # Today's revenue
        today_revenue = self.db.query(func.sum(Order.final_amount)).filter(
            Order.status == OrderStatus.CONFIRMED,
            Order.confirmed_at.between(today, today + timedelta(days=1) - timedelta(microseconds=1))
        ).scalar() or 0
        
        # Yesterday's revenue
        yesterday_revenue = self.db.query(func.sum(Order.final_amount)).filter(
            Order.status == OrderStatus.CONFIRMED,
            Order.confirmed_at.between(yesterday, today - timedelta(microseconds=1))
        ).scalar() or 0
        
        # This month's revenue
        this_month_revenue = self.db.query(func.sum(Order.final_amount)).filter(
            Order.status == OrderStatus.CONFIRMED,
            Order.confirmed_at.between(this_month_start, today + timedelta(days=1) - timedelta(microseconds=1))
        ).scalar() or 0
        
        # Last month's revenue
        last_month_revenue = self.db.query(func.sum(Order.final_amount)).filter(
            Order.status == OrderStatus.CONFIRMED,
            Order.confirmed_at.between(last_month_start, last_month_end)
        ).scalar() or 0
        
        # New orders today
        new_orders_today = self.db.query(func.count(Order.id)).filter(
            Order.created_at.between(today, today + timedelta(days=1) - timedelta(microseconds=1))
        ).scalar() or 0
        
        # Confirmed orders today
        confirmed_orders_today = self.db.query(func.count(Order.id)).filter(
            Order.status == OrderStatus.CONFIRMED,
            Order.confirmed_at.between(today, today + timedelta(days=1) - timedelta(microseconds=1))
        ).scalar() or 0
        
        # Pending verification orders
        pending_verification = self.db.query(func.count(Order.id)).filter(
            Order.status == OrderStatus.VERIFICATION_PENDING
        ).scalar() or 0
        
        # Recent transactions for quick summary
        recent_transactions = self.db.query(
            Transaction,
            User.username
        ).join(
            User, Transaction.user_id == User.id
        ).order_by(
            desc(Transaction.created_at)
        ).limit(5).all()
        
        recent_transactions_data = [{
            "id": t[0].id,
            "transaction_id": t[0].transaction_id,
            "username": t[1],
            "amount": t[0].amount,
            "type": t[0].type.value if t[0].type else None,
            "status": t[0].status.value if t[0].status else None,
            "created_at": t[0].created_at
        } for t in recent_transactions]
        
        # Gather trending plans (most ordered in last 30 days)
        trending_plans = self.db.query(
            Plan.id,
            Plan.name,
            func.count(Order.id).label("order_count")
        ).join(
            Order, Plan.id == Order.plan_id
        ).filter(
            Order.created_at.between(today - timedelta(days=30), today + timedelta(days=1) - timedelta(microseconds=1))
        ).group_by(
            Plan.id, Plan.name
        ).order_by(
            desc("order_count")
        ).limit(5).all()
        
        trending_plans_data = [{
            "id": p.id,
            "name": p.name,
            "order_count": p.order_count
        } for p in trending_plans]
        
        return {
            "today_revenue": float(today_revenue),
            "yesterday_revenue": float(yesterday_revenue),
            "this_month_revenue": float(this_month_revenue),
            "last_month_revenue": float(last_month_revenue),
            "revenue_change_percentage": ((float(this_month_revenue) - float(last_month_revenue)) / float(last_month_revenue) * 100) if last_month_revenue > 0 else 0,
            "new_orders_today": new_orders_today,
            "confirmed_orders_today": confirmed_orders_today,
            "pending_verification": pending_verification,
            "recent_transactions": recent_transactions_data,
            "trending_plans": trending_plans_data
        } 