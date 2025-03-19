from app.worker import celery_app

@celery_app.task
def sample_task(x, y):
    return x + y 