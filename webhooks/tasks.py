from celery import shared_task

@shared_task        #Celery registers this function as a task.
def test_task():
    return "Celery is working!"