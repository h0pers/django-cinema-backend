from rest_framework import serializers

from apps.api.payments.subscriptions.models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    has_trial = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = "__all__"

    def get_has_trial(self, obj):
        return obj.has_trial
