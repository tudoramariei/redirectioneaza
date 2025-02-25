# Generated by Django 5.1.6 on 2025-02-18 11:06
import logging

from django.db import IntegrityError, migrations, transaction

logger = logging.getLogger(__name__)


def copy_ngos_to_causes(apps, _):
    Cause = apps.get_model("donations", "Cause")
    Ngo = apps.get_model("donations", "Ngo")

    batch_size = 1000
    pending_causes = []
    for ngo in Ngo.objects.all():
        if ngo.causes.exists():
            logger.warning("NGO %s already has causes. Skipping.", ngo)

            continue

        cause = Cause(
            ngo=ngo,
            allow_online_collection=ngo.is_accepting_forms,
            display_image=ngo.logo,
            slug=ngo.slug,
            name=ngo.name,
            description=ngo.description,
            bank_account=ngo.bank_account,
        )

        pending_causes.append(cause)

        if len(pending_causes) >= batch_size:
            try:
                Cause.objects.bulk_create(pending_causes)
                pending_causes = []
            except IntegrityError as e:
                logger.error("Failed to bulk create causes: %s", e)

    try:
        Cause.objects.bulk_create(pending_causes, batch_size=1000)
    except IntegrityError as e:
        logger.error("Failed to bulk create causes: %s", e)


def copy_causes_to_ngos(apps, _):
    Cause = apps.get_model("donations", "Cause")
    Ngo = apps.get_model("donations", "Ngo")

    for ngo in Ngo.objects.filter(causes__isnull=False):
        # get the oldest form of the NGO
        cause: Cause = ngo.causes.order_by("date_created").first()
        ngo.logo = cause.display_image
        ngo.slug = cause.slug
        ngo.description = cause.description
        ngo.bank_account = cause.bank_account

        with transaction.atomic():
            ngo.save()
            ngo.causes.all().delete()


def add_cause_to_donors(apps, _):
    Cause = apps.get_model("donations", "Cause")
    Donor = apps.get_model("donations", "Donor")

    batch_size = 1000
    pending_donors = []
    for donor in Donor.objects.filter(ngo__isnull=False, cause__isnull=True):
        cause: Cause = donor.ngo.causes.first()

        donor.cause = cause
        pending_donors.append(donor)

        if len(pending_donors) >= batch_size:
            Donor.objects.bulk_update(pending_donors, ["cause"])
            pending_donors = []

    if len(pending_donors) > 0:
        Donor.objects.bulk_update(pending_donors, ["cause"])


def add_cause_to_jobs(apps, _):
    Cause = apps.get_model("donations", "Cause")
    Job = apps.get_model("donations", "Job")

    batch_size = 1000
    pending_jobs = []
    for job in Job.objects.filter(ngo__isnull=False, cause__isnull=True):
        cause: Cause = job.ngo.causes.first()

        job.cause = cause
        pending_jobs.append(job)

        if len(pending_jobs) >= batch_size:
            Job.objects.bulk_update(pending_jobs, ["cause"])
            pending_jobs = []

    if len(pending_jobs) > 0:
        Job.objects.bulk_update(pending_jobs, ["cause"])


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("donations", "0022_cause_donor_cause_job_cause"),
    ]

    operations = [
        migrations.RunPython(copy_ngos_to_causes, reverse_code=copy_causes_to_ngos),
        migrations.RunPython(add_cause_to_donors, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(add_cause_to_jobs, reverse_code=migrations.RunPython.noop),
    ]
