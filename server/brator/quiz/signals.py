from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save)
def validate_model(instance, **kwargs):
    instance.full_clean()
