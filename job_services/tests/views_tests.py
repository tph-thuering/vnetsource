from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse_lazy, reverse
from ..models import Quota, User
from .. import cluster_id


class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="foobar", password="1")
        login = self.client.login(username=self.user.username, password="1")
        self.assertTrue(login)
        self.cluster_name = cluster_id.ALL_KNOWN[0]

    def create_quota(self):
        self.quota = Quota.objects.create(user=self.user, max_per_month=10, max_per_run=10, cluster=self.cluster_name)

    def verify_quota_attributes(self, quota, user, max_per_month, max_per_run, cluster):
        self.assertEqual(quota.user, user)
        self.assertEqual(quota.max_per_month, max_per_month)
        self.assertEqual(quota.max_per_run, max_per_run)
        self.assertEqual(quota.cluster, cluster)

    def test_get_create_quota_view(self):
        self.assertEqual(Quota.objects.all().count(), 0)
        response = self.client.get(reverse("create_quota"))
        self.assertTemplateUsed(response, "job_services/quota.html")
        self.assertEqual(Quota.objects.all().count(), 0)

    def test_post_create_quota_view(self):
        self.assertEqual(Quota.objects.all().count(), 0)
        kwargs = {
            "user": self.user.id,
            "max_per_month": 10,
            "max_per_run": 10,
            "cluster": self.cluster_name
        }
        response = self.client.post(reverse("create_quota"), kwargs)
        self.assertRedirects(response, str(reverse_lazy("list_quotas")))
        self.assertEqual(Quota.objects.all().count(), 1)
        quota = Quota.objects.all()[0]
        self.verify_quota_attributes(quota, self.user, 10, 10, self.cluster_name)

    def test_get_delete_quota_view(self):
        self.create_quota()
        self.assertEqual(Quota.objects.all().count(), 1)
        response = self.client.get(reverse("delete_quota", kwargs={"pk": self.quota.id}))
        self.assertTemplateUsed(response, "job_services/delete.html")

    def test_post_delete_quota_view(self):
        self.create_quota()
        self.assertEqual(Quota.objects.all().count(), 1)
        response = self.client.post(reverse("delete_quota", kwargs={"pk": self.quota.id}))
        self.assertEqual(Quota.objects.all().count(), 0)
        self.assertRedirects(response, str(reverse_lazy("list_quotas")))
    
    def test_get_list_quotas_view(self):
        self.create_quota()
        self.assertEqual(Quota.objects.all().count(), 1)
        response = self.client.get(reverse("list_quotas"))
        self.assertTemplateUsed(response, "job_services/list.html")

    def test_get_update_quota_view(self):
        self.create_quota()
        self.assertEqual(Quota.objects.all().count(), 1)
        quota = Quota.objects.get(id=self.quota.id)
        self.verify_quota_attributes(quota, self.user, 10, 10, self.cluster_name)
        response = self.client.get(reverse("update_quota", kwargs={"pk": self.quota.id}))
        self.assertTemplateUsed(response, "job_services/quota.html")
        quota = Quota.objects.get(id=self.quota.id)
        self.verify_quota_attributes(quota, self.user, 10, 10, self.cluster_name)

    def test_post_update_quota_view(self):
        self.create_quota()
        self.assertEqual(Quota.objects.all().count(), 1)
        quota = Quota.objects.get(id=self.quota.id)
        self.verify_quota_attributes(quota, self.user, 10, 10, self.cluster_name)
        kwargs = {
            'user': self.user.id,
            'max_per_month': 100,
            'max_per_run': 1000,
            'cluster': self.cluster_name
        }
        response = self.client.post(reverse("update_quota", kwargs={"pk": self.quota.id}), kwargs)
        self.assertRedirects(response, str(reverse_lazy("list_quotas")))
        quota = Quota.objects.get(id=self.quota.id)
        self.verify_quota_attributes(quota, self.user, 100, 1000, self.cluster_name)