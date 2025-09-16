from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib import admin
from django.contrib.sites.models import Site
from rest_framework.authtoken.models import TokenProxy

from .models import Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    pass


admin.site.unregister(Site)
admin.site.unregister(EmailAddress)
admin.site.unregister(TokenProxy)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)
