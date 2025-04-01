from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException, status
from sqlalchemy.sql import select

from app.models.payment_admin import PaymentAdminAssignment, PaymentAdminMetrics
from app.models.user import User
from app.models.bank_card import BankCard
from app.schemas.payment_admin import (
    PaymentAdminAssignmentCreate,
    PaymentAdminAssignmentUpdate,
    PaymentAdminMetricsCreate,
    PaymentAdminMetricsUpdate,
    PaymentAdminAssignmentWithMetrics,
    PaymentAdminStatistics,
    PaymentAdminReportData,
    PaymentAdminPerformanceMetrics
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PaymentAdminService:
    """
    Service for managing payment admins and their assignments.
    
    This service handles the business logic for payment admin management,
    including creating and updating assignments, tracking metrics, and
    selecting admins for payment verification.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_assignment(self, assignment_id: int) -> Optional[PaymentAdminAssignment]:
        """
        Get a payment admin assignment by ID.
        
        Args:
            assignment_id: The ID of the assignment to retrieve
            
        Returns:
            The assignment or None if not found
        """
        assignment = self.db.query(PaymentAdminAssignment).filter(
            PaymentAdminAssignment.id == assignment_id
        ).first()
        
        return assignment
    
    def get_assignments_by_user(self, user_id: int) -> List[PaymentAdminAssignment]:
        """
        Get all payment admin assignments for a specific user.
        
        Args:
            user_id: The ID of the user whose assignments to retrieve
            
        Returns:
            List of payment admin assignments
        """
        assignments = self.db.query(PaymentAdminAssignment).filter(
            PaymentAdminAssignment.user_id == user_id
        ).all()
        
        return assignments
    
    def get_assignments_by_bank_card(self, bank_card_id: int) -> List[PaymentAdminAssignment]:
        """
        Get all payment admin assignments for a specific bank card.
        
        Args:
            bank_card_id: The ID of the bank card
            
        Returns:
            List of payment admin assignments
        """
        assignments = self.db.query(PaymentAdminAssignment).filter(
            PaymentAdminAssignment.bank_card_id == bank_card_id
        ).all()
        
        return assignments
    
    def get_assignments_by_telegram_group(self, telegram_group_id: str) -> List[PaymentAdminAssignment]:
        """
        Get all payment admin assignments for a specific Telegram group.
        
        Args:
            telegram_group_id: The ID of the Telegram group
            
        Returns:
            List of payment admin assignments
        """
        assignments = self.db.query(PaymentAdminAssignment).filter(
            PaymentAdminAssignment.telegram_group_id == telegram_group_id
        ).all()
        
        return assignments
    
    def create_assignment(self, assignment_in: PaymentAdminAssignmentCreate) -> PaymentAdminAssignment:
        """
        Create a new payment admin assignment.
        
        Args:
            assignment_in: The data for the new assignment
            
        Returns:
            The created assignment
            
        Raises:
            HTTPException: If validation fails
        """
        # Check if user exists
        user = self.db.query(User).filter(User.id == assignment_in.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {assignment_in.user_id} not found"
            )
        
        # Check if bank card exists (if provided)
        if assignment_in.bank_card_id:
            bank_card = self.db.query(BankCard).filter(
                BankCard.id == assignment_in.bank_card_id
            ).first()
            
            if not bank_card:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bank card with ID {assignment_in.bank_card_id} not found"
                )
            
            # Check if this bank card already has an active assignment
            existing_assignment = self.db.query(PaymentAdminAssignment).filter(
                PaymentAdminAssignment.bank_card_id == assignment_in.bank_card_id,
                PaymentAdminAssignment.is_active == True
            ).first()
            
            if existing_assignment and existing_assignment.user_id != assignment_in.user_id:
                logger.warning(
                    f"Bank card {assignment_in.bank_card_id} already assigned to user {existing_assignment.user_id}"
                )
        
        # Create the assignment
        assignment = PaymentAdminAssignment(
            user_id=assignment_in.user_id,
            bank_card_id=assignment_in.bank_card_id,
            telegram_group_id=assignment_in.telegram_group_id,
            is_active=assignment_in.is_active,
            daily_limit=assignment_in.daily_limit,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        # Create metrics record if not exists
        self._ensure_metrics_exist(assignment_in.user_id)
        
        return assignment
    
    def update_assignment(
        self, assignment_id: int, assignment_in: PaymentAdminAssignmentUpdate
    ) -> Optional[PaymentAdminAssignment]:
        """
        Update an existing payment admin assignment.
        
        Args:
            assignment_id: The ID of the assignment to update
            assignment_in: The updated data
            
        Returns:
            The updated assignment or None if not found
            
        Raises:
            HTTPException: If validation fails
        """
        assignment = self.get_assignment(assignment_id)
        if not assignment:
            return None
        
        update_data = assignment_in.dict(exclude_unset=True)
        
        # Check if bank card exists (if provided)
        if update_data.get("bank_card_id"):
            bank_card = self.db.query(BankCard).filter(
                BankCard.id == update_data["bank_card_id"]
            ).first()
            
            if not bank_card:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bank card with ID {update_data['bank_card_id']} not found"
                )
            
            # Check if this bank card already has an active assignment
            existing_assignment = self.db.query(PaymentAdminAssignment).filter(
                PaymentAdminAssignment.bank_card_id == update_data["bank_card_id"],
                PaymentAdminAssignment.is_active == True,
                PaymentAdminAssignment.id != assignment_id
            ).first()
            
            if existing_assignment:
                logger.warning(
                    f"Bank card {update_data['bank_card_id']} already assigned to user {existing_assignment.user_id}"
                )
        
        # Update the assignment
        for field, value in update_data.items():
            setattr(assignment, field, value)
        
        assignment.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(assignment)
        
        return assignment
    
    def delete_assignment(self, assignment_id: int) -> bool:
        """
        Delete a payment admin assignment.
        
        Args:
            assignment_id: The ID of the assignment to delete
            
        Returns:
            True if successful, False if not found
        """
        assignment = self.get_assignment(assignment_id)
        if not assignment:
            return False
        
        self.db.delete(assignment)
        self.db.commit()
        
        return True
    
    def get_metrics(self, user_id: int) -> Optional[PaymentAdminMetrics]:
        """
        Get metrics for a specific payment admin.
        
        Args:
            user_id: The ID of the user whose metrics to retrieve
            
        Returns:
            The metrics or None if not found
        """
        metrics = self.db.query(PaymentAdminMetrics).filter(
            PaymentAdminMetrics.user_id == user_id
        ).first()
        
        return metrics
    
    def update_metrics(
        self, user_id: int, metrics_in: PaymentAdminMetricsUpdate
    ) -> Optional[PaymentAdminMetrics]:
        """
        Update metrics for a payment admin.
        
        Args:
            user_id: The ID of the user whose metrics to update
            metrics_in: The updated metrics data
            
        Returns:
            The updated metrics or None if not found
        """
        metrics = self.get_metrics(user_id)
        if not metrics:
            return None
        
        update_data = metrics_in.dict(exclude_unset=True)
        
        # Update the metrics
        for field, value in update_data.items():
            setattr(metrics, field, value)
        
        metrics.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(metrics)
        
        return metrics
    
    def select_admin_for_payment(
        self, bank_card_id: Optional[int] = None
    ) -> Optional[PaymentAdminAssignment]:
        """
        Select an appropriate payment admin for a new payment verification.
        
        This method uses a load-balancing algorithm to distribute work among admins
        based on their daily limits, current workload, and previous assignments.
        
        Args:
            bank_card_id: Optional ID of the bank card used for payment
            
        Returns:
            The selected assignment or None if no suitable admin is found
        """
        # Query base: active assignments
        query = self.db.query(PaymentAdminAssignment).filter(
            PaymentAdminAssignment.is_active == True
        )
        
        # If bank card specified, prioritize admins assigned to that card
        if bank_card_id:
            query = query.filter(
                or_(
                    PaymentAdminAssignment.bank_card_id == bank_card_id,
                    PaymentAdminAssignment.bank_card_id.is_(None)
                )
            )
        
        # Order by:
        # 1. Admins with this specific card (if provided)
        # 2. Admins with fewer assignments today (based on metrics)
        # 3. Admins with longer time since last assignment
        query = query.outerjoin(
            PaymentAdminMetrics,
            PaymentAdminAssignment.user_id == PaymentAdminMetrics.user_id
        ).order_by(
            # If bank_card_id provided, prioritize assignments with matching bank_card_id
            desc(PaymentAdminAssignment.bank_card_id == bank_card_id) if bank_card_id else None,
            # Prioritize admins with fewer processed payments
            PaymentAdminMetrics.total_processed.asc().nulls_first(),
            # Prioritize admins with older last assignment date
            PaymentAdminAssignment.last_assignment_date.asc().nulls_first()
        )
        
        # Get the most suitable assignment
        assignment = query.first()
        
        if assignment:
            # Update the last assignment date
            assignment.last_assignment_date = datetime.utcnow()
            assignment.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(assignment)
        
        return assignment
    
    def get_admin_statistics(self) -> PaymentAdminStatistics:
        """
        Get overall statistics for payment admins.
        
        Returns:
            Statistics about payment admin performance
        """
        # Get count of active admins
        total_admins = self.db.query(func.count(PaymentAdminAssignment.id)).filter(
            PaymentAdminAssignment.is_active == True
        ).scalar() or 0
        
        # Get aggregate metrics
        metrics_query = self.db.query(
            func.sum(PaymentAdminMetrics.total_processed).label("total_processed"),
            func.sum(PaymentAdminMetrics.total_approved).label("total_approved"),
            func.avg(PaymentAdminMetrics.avg_response_time_seconds).label("avg_response_time")
        ).first()
        
        total_processed = metrics_query.total_processed or 0
        total_approved = metrics_query.total_approved or 0
        avg_response_time = metrics_query.avg_response_time
        
        # Calculate average approval rate
        avg_approval_rate = (total_approved / total_processed * 100) if total_processed > 0 else 0
        
        return PaymentAdminStatistics(
            total_admins=total_admins,
            total_processed_payments=total_processed,
            avg_approval_rate=avg_approval_rate,
            avg_response_time=avg_response_time
        )
    
    def get_assignment_with_metrics(self, assignment_id: int) -> Optional[PaymentAdminAssignmentWithMetrics]:
        """
        Get a payment admin assignment with its associated metrics.
        
        Args:
            assignment_id: The ID of the assignment to retrieve
            
        Returns:
            The assignment with metrics or None if not found
        """
        assignment = self.get_assignment(assignment_id)
        if not assignment:
            return None
        
        metrics = self.get_metrics(assignment.user_id)
        
        return PaymentAdminAssignmentWithMetrics(
            assignment=assignment,
            metrics=metrics
        )
    
    def _ensure_metrics_exist(self, user_id: int) -> None:
        """
        Ensure that metrics exist for a user, creating them if they don't.
        
        Args:
            user_id: The ID of the user
        """
        metrics = self.get_metrics(user_id)
        if not metrics:
            metrics = PaymentAdminMetrics(
                user_id=user_id,
                total_processed=0,
                total_approved=0,
                total_rejected=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(metrics)
            self.db.commit()
            self.db.refresh(metrics)
    
    def record_payment_processed(
        self, user_id: int, approved: bool, response_time_seconds: float
    ) -> Optional[PaymentAdminMetrics]:
        """
        Record a processed payment in the admin's metrics.
        
        Args:
            user_id: The ID of the admin who processed the payment
            approved: Whether the payment was approved
            response_time_seconds: The time taken to respond (in seconds)
            
        Returns:
            The updated metrics or None if not found
        """
        metrics = self.get_metrics(user_id)
        if not metrics:
            return None
        
        # Update metrics
        metrics.total_processed += 1
        
        if approved:
            metrics.total_approved += 1
        else:
            metrics.total_rejected += 1
        
        # Update average response time (weighted average)
        if metrics.avg_response_time_seconds is None:
            metrics.avg_response_time_seconds = response_time_seconds
        else:
            # Calculate weighted average based on total processed
            total_processed = metrics.total_processed
            current_avg = metrics.avg_response_time_seconds
            
            metrics.avg_response_time_seconds = (
                (current_avg * (total_processed - 1) + response_time_seconds) / total_processed
            )
        
        metrics.last_processed_at = datetime.utcnow()
        metrics.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(metrics)
        
        return metrics

    async def get_admin_for_card(self, bank_card_id: int) -> Optional[PaymentAdminAssignment]:
        """
        Get the most appropriate admin assignment for a specific bank card.
        
        Args:
            bank_card_id: ID of the bank card
            
        Returns:
            The most appropriate PaymentAdminAssignment based on load balancing algorithm
        """
        try:
            # First check if there are specific admins assigned to this card
            card_assignments = await self.db.execute(
                select(PaymentAdminAssignment)
                .filter(
                    PaymentAdminAssignment.bank_card_id == bank_card_id,
                    PaymentAdminAssignment.is_active == True
                )
            )
            card_assignments = card_assignments.scalars().all()
            
            if card_assignments:
                # If there are multiple admins assigned to this card, use load balancing
                if len(card_assignments) > 1:
                    return await self._select_admin_using_load_balancing(card_assignments)
                else:
                    # If there's only one admin, use that one
                    return card_assignments[0]
            
            # If no specific assignments, get a general admin (bank_card_id=None)
            general_assignments = await self.db.execute(
                select(PaymentAdminAssignment)
                .filter(
                    PaymentAdminAssignment.bank_card_id.is_(None),
                    PaymentAdminAssignment.is_active == True
                )
            )
            general_assignments = general_assignments.scalars().all()
            
            if general_assignments:
                # Use load balancing to select the best admin
                return await self._select_admin_using_load_balancing(general_assignments)
            
            # If no assignments found at all, return None
            return None
        
        except Exception as e:
            logger.error(f"Error getting admin for bank card {bank_card_id}: {str(e)}")
            return None

    async def _select_admin_using_load_balancing(
        self, 
        assignments: List[PaymentAdminAssignment]
    ) -> PaymentAdminAssignment:
        """
        Select the most appropriate admin from a list of assignments using load balancing.
        
        Args:
            assignments: List of PaymentAdminAssignment objects to choose from
            
        Returns:
            The most appropriate PaymentAdminAssignment based on workload and performance
        """
        if not assignments:
            return None
        
        if len(assignments) == 1:
            return assignments[0]
        
        # Get metrics for all admins in the assignments
        metrics_by_admin_id = {}
        for assignment in assignments:
            metrics = self.get_metrics(assignment.user_id)
            metrics_by_admin_id[assignment.user_id] = metrics
        
        # Calculate a score for each admin based on:
        # 1. Current pending payments (lower is better)
        # 2. Response time (lower is better)
        # 3. Approval rate (higher is better)
        # 4. Last assignment time (older is better)
        
        admin_scores = []
        for assignment in assignments:
            metrics = metrics_by_admin_id.get(assignment.user_id)
            
            if not metrics:
                # If no metrics, give a default middle score
                admin_scores.append((assignment, 50))
                continue
            
            # Calculate score components
            pending_score = 100 - min(metrics.total_processed * 10, 80)  # Fewer pending is better
            
            # Response time score (faster is better)
            response_time_score = 100
            if metrics.avg_response_time_seconds is not None and metrics.avg_response_time_seconds > 0:
                response_time_score = max(100 - (metrics.avg_response_time_seconds / 60) * 20, 20)  # Scale: 0-5 minutes
            
            # Approval rate score (higher is better)
            approval_score = metrics.avg_approval_rate * 100
            
            # Last assignment score (older is better)
            last_assignment_score = 100
            if metrics.last_processed_at:
                time_diff = datetime.utcnow() - metrics.last_processed_at
                # If assigned within the last hour, reduce score
                if time_diff.total_seconds() < 3600:
                    last_assignment_score = max(time_diff.total_seconds() / 3600 * 100, 20)
            
            # Calculate weighted score
            total_score = (
                pending_score * 0.4 +         # 40% weight for current workload
                response_time_score * 0.2 +   # 20% weight for response time
                approval_score * 0.2 +        # 20% weight for approval rate
                last_assignment_score * 0.2   # 20% weight for last assignment time
            )
            
            admin_scores.append((assignment, total_score))
        
        # Sort by score (highest first) and return the best admin
        admin_scores.sort(key=lambda x: x[1], reverse=True)
        best_assignment = admin_scores[0][0]
        
        return best_assignment

    async def generate_performance_reports(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        admin_id: Optional[int] = None
    ) -> PaymentAdminReportData:
        """
        Generate comprehensive performance reports for payment admins.
        
        This method analyzes payment verification data and generates detailed
        metrics about payment admin performance, including response times,
        approval rates, rejection reasons, and workload distribution.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            admin_id: Optional admin ID to filter for a specific admin
            
        Returns:
            PaymentAdminReportData with detailed performance metrics
        """
        try:
            # Base query to get all orders with payment verification data
            from app.models.order import Order
            from app.models.user import User
            
            # Get all orders with payment verification data
            query = (
                select(Order)
                .where(
                    Order.payment_proof_submitted_at.is_not(None),
                    Order.payment_verified_at.is_not(None)
                )
            )
            
            # Apply date filters if provided
            if start_date:
                query = query.where(Order.payment_verified_at >= start_date)
            if end_date:
                query = query.where(Order.payment_verified_at <= end_date)
                
            # Apply admin filter if provided
            if admin_id:
                query = query.where(Order.payment_verification_admin_id == admin_id)
                
            # Execute query
            result = await self.db.execute(query)
            verified_orders = result.scalars().all()
            
            # Group data by admin
            admin_data = {}
            total_payments = 0
            total_approved = 0
            total_rejected = 0
            total_response_time = 0
            
            # Current date for calculating recent statistics
            now = datetime.now()
            today_start = datetime(now.year, now.month, now.day)
            week_start = today_start - timedelta(days=now.weekday())
            month_start = datetime(now.year, now.month, 1)
            
            for order in verified_orders:
                # Skip if no admin assigned (shouldn't happen)
                if not order.payment_verification_admin_id:
                    continue
                    
                admin_id = order.payment_verification_admin_id
                
                # Initialize admin data if not exists
                if admin_id not in admin_data:
                    admin_data[admin_id] = {
                        "admin_id": admin_id,
                        "total_processed": 0,
                        "total_approved": 0,
                        "total_rejected": 0,
                        "response_times": [],
                        "total_processed_today": 0,
                        "total_processed_week": 0,
                        "total_processed_month": 0,
                        "rejection_reasons": {},
                        "bank_card_distribution": {}
                    }
                    
                    # Get admin name if possible
                    admin = await self.db.get(User, admin_id)
                    if admin:
                        admin_data[admin_id]["admin_name"] = f"{admin.first_name or ''} {admin.last_name or ''}".strip() or f"Admin #{admin_id}"
                
                # Increment overall counters
                total_payments += 1
                admin_data[admin_id]["total_processed"] += 1
                
                # Check approval status
                is_approved = order.status == "COMPLETED"
                if is_approved:
                    total_approved += 1
                    admin_data[admin_id]["total_approved"] += 1
                else:
                    total_rejected += 1
                    admin_data[admin_id]["total_rejected"] += 1
                    
                    # Track rejection reasons
                    reason = order.payment_rejection_reason or "Unknown"
                    if reason not in admin_data[admin_id]["rejection_reasons"]:
                        admin_data[admin_id]["rejection_reasons"][reason] = 0
                    admin_data[admin_id]["rejection_reasons"][reason] += 1
                
                # Calculate response time (seconds between submission and verification)
                if order.payment_proof_submitted_at and order.payment_verified_at:
                    response_time = (order.payment_verified_at - order.payment_proof_submitted_at).total_seconds()
                    admin_data[admin_id]["response_times"].append(response_time)
                    total_response_time += response_time
                    
                # Count recent activity
                if order.payment_verified_at >= today_start:
                    admin_data[admin_id]["total_processed_today"] += 1
                if order.payment_verified_at >= week_start:
                    admin_data[admin_id]["total_processed_week"] += 1
                if order.payment_verified_at >= month_start:
                    admin_data[admin_id]["total_processed_month"] += 1
                    
                # Track bank card distribution
                bank_card_id = order.payment_card_id
                if bank_card_id:
                    # Get bank card details
                    from app.models.bank_card import BankCard
                    bank_card = await self.db.get(BankCard, bank_card_id)
                    if bank_card:
                        card_key = f"{bank_card.bank_name} - {bank_card.card_number[-4:]}"
                    else:
                        card_key = f"Card #{bank_card_id}"
                        
                    if card_key not in admin_data[admin_id]["bank_card_distribution"]:
                        admin_data[admin_id]["bank_card_distribution"][card_key] = 0
                    admin_data[admin_id]["bank_card_distribution"][card_key] += 1
            
            # Calculate averages and prepare final metrics
            admin_metrics = []
            overall_avg_response_time = total_response_time / total_payments if total_payments > 0 else None
            overall_approval_rate = total_approved / total_payments if total_payments > 0 else 0
            
            for admin_id, data in admin_data.items():
                response_times = data.pop("response_times", [])
                
                # Calculate averages
                avg_response_time = sum(response_times) / len(response_times) if response_times else None
                avg_approval_rate = data["total_approved"] / data["total_processed"] if data["total_processed"] > 0 else 0
                
                # Add calculated metrics
                metrics = PaymentAdminPerformanceMetrics(
                    admin_id=admin_id,
                    admin_name=data.get("admin_name"),
                    total_processed=data["total_processed"],
                    total_approved=data["total_approved"],
                    total_rejected=data["total_rejected"],
                    avg_approval_rate=avg_approval_rate,
                    avg_response_time_seconds=avg_response_time,
                    min_response_time_seconds=min(response_times) if response_times else None,
                    max_response_time_seconds=max(response_times) if response_times else None,
                    total_processed_today=data["total_processed_today"],
                    total_processed_week=data["total_processed_week"],
                    total_processed_month=data["total_processed_month"],
                    rejection_reasons=data["rejection_reasons"],
                    bank_card_distribution=data["bank_card_distribution"]
                )
                
                admin_metrics.append(metrics)
            
            # Sort admins by number of processed payments (descending)
            admin_metrics.sort(key=lambda x: x.total_processed, reverse=True)
            
            # Create the final report
            report = PaymentAdminReportData(
                admins=admin_metrics,
                start_date=start_date,
                end_date=end_date,
                total_payments=total_payments,
                total_approved=total_approved,
                total_rejected=total_rejected,
                overall_approval_rate=overall_approval_rate,
                avg_response_time_seconds=overall_avg_response_time
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance reports: {str(e)}")
            raise