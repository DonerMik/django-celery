from datetime import timedelta

from freezegun import freeze_time
from mixer.backend.django import mixer
from django.core import mail

from elk.utils.testing import ClassIntegrationTestCase, create_customer, create_teacher
from lessons import models as lessons
from market.models import Subscription
from market.tasks import notification_inactive_subscribers_gte_7days
from products.models import Product1


@freeze_time('2032-11-01 12:00')
class TestNotificationInactiveSubscribers(ClassIntegrationTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product1.objects.get(pk=1)
        cls.product.duration = timedelta(days=30)
        cls.product.save()
        cls.customer = create_customer()

    def setUp(self):
        self.s_1 = Subscription(
            customer=self.customer,
            product=self.product,
            buy_price=150,
            first_lesson_date='2032-11-01 12:00'
        )
        self.s_1.save()
        self.teacher = create_teacher()

    def test_notification_inactive_subscribers_gte_7days(self):
        """
        We test the characteristic for an increase in the number of messages after 7 days
        and such a number of messages after 8 days.
        """
        lesson = mixer.blend(lessons.OrdinaryLesson)
        c_1 = mixer.blend('market.Class', customer=self.customer, subscription=self.s_1)
        entry_1 = mixer.blend('timeline.Entry',
                              teacher=self.teacher,
                              lesson=lesson,
                              start=self.tzdatetime(2032, 11, 5, 14, 0))
        c_1.timeline = entry_1
        c_1.save()
        self.assertEqual(len(mail.outbox), 2)
        with freeze_time('2032-11-11 20:01'):
            notification_inactive_subscribers_gte_7days()
            self.assertEqual(len(mail.outbox), 2)
        with freeze_time('2032-11-12 20:01'):
            notification_inactive_subscribers_gte_7days()
            self.assertEqual(len(mail.outbox), 13)
        with freeze_time('2032-11-13 20:01'):
            notification_inactive_subscribers_gte_7days()
            self.assertEqual(len(mail.outbox), 13)
