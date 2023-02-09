from datetime import timedelta

from django.utils import timezone

from elk.celery import app as celery
from mailer.owl import Owl
from market.models import Subscription


@celery.task
def notification_inactive_subscribers_gte_7days():
    """
    Sends email notifications if the last lesson was later than 7 days ago.
    """

    current_subscriptions = Subscription.objects.list_current_subscribe()
    for sub in current_subscriptions:
        last_classes = sub.classes.last().timeline.start
        last_classes_was_later_7 = last_classes + timedelta(days=7) <= timezone.now()
        last_classes_was_before_8 = last_classes + timedelta(days=8) > timezone.now()
        if last_classes_was_later_7 and last_classes_was_before_8:
            owl = Owl(
                template='mail/class/student/inactive_acc_information.html',
                ctx={'customer': sub.customer.customer_first_name},
                to=[sub.customer.user.email],
                timezone=sub.customer.timezone,
            )
            owl.send()
