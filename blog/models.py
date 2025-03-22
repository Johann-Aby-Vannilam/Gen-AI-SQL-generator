from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
class DatabaseTypes(models.IntegerChoices):
    POSTGRESQL = 1, 'PostgreSQL'
    MONGODB = 2, 'MongoDB'
   

class GeneratorConfiguration(models.Model):
    name = models.CharField(max_length=255, help_text="Name of the configuration.")
    database_type = models.IntegerField(
        choices=DatabaseTypes.choices,
        default=DatabaseTypes.POSTGRESQL,
        help_text="Select the type of database."
    )
    # Add additional fields as required

    class Meta:
        db_table = 'generator_configurations'
    
    def __str__(self):
        return f"{self.name} ({self.get_database_type_display()})"
