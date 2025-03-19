from celery import shared_task

@shared_task
def analyze_usage_patterns():
    """Periodic task to analyze user usage patterns and generate plan suggestions."""
    from .models import User, UserUsagePattern
    from .services import UsagePatternAnalyzer, PlanSuggestionService
    
    # Get all users with active subscriptions
    users = User.objects.filter(subscriptions__status='active').distinct()
    
    for user in users:
        # Analyze usage patterns
        usage_data = UsagePatternAnalyzer.analyze_usage(user)
        if not usage_data:
            continue
            
        # Update or create usage pattern
        usage_pattern, created = UserUsagePattern.objects.get_or_create(user=user)
        usage_pattern.update_patterns(usage_data)
        
        # Generate plan suggestion if needed
        PlanSuggestionService.generate_suggestion(user) 