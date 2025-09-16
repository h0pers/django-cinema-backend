from django.db import models


class CrewMember(models.Model):
    full_name = models.CharField()
    picture = models.ImageField(blank=True, null=True)
    # Slug is not unique, use this field as SEO URL with ID
    slug = models.SlugField()

    def __str__(self):
        return self.full_name
