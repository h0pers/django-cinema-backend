from celery import shared_task


@shared_task
def clean_up_uncompleted_files():
    pass
