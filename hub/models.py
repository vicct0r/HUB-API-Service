from django.db import models
from django.urls import reverse
from django.template.defaultfilters import slugify

class Base(models.Model):
    created = models.DateTimeField(auto_now=True)
    modified = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"added: {self.created} - active: {self.is_active}"


class DistributionCenter(Base):
    name = models.CharField('Name', max_length=100, unique=True)
    url = models.URLField(unique=True)
    region = models.CharField('Region', max_length=100, blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=False, editable=False)
    balance = models.DecimalField(default=0, max_digits=12, decimal_places=2, editable=False)
    slug = models.SlugField(null=True)

    def __str__(self):
        return f"{self.name} - running: {self.status}"
    
    def get_absolute_url(self):
        return reverse("cd_detail", kwargs={"slug": self.slug})
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)
