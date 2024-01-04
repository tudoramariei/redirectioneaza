from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, QuerySet
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator

from .base import AccountHandler
from ..models import Donor, Ngo


class MyAccountDetailsHandler(AccountHandler):
    template_name = "ngo/my-account-details.html"

    def get(self, request, *args, **kwargs):
        context = {"user": request.user}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        post = request.POST

        request.user.last_name = post.get("nume")
        request.user.first_name = post.get("prenume")

        request.user.save()

        context = {"user": request.user}

        return render(request, self.template_name, context)


@method_decorator(login_required, name="get")
class MyAccountHandler(AccountHandler):
    template_name = "ngo/my-account.html"

    def get(self, request, *args, **kwargs):
        user_ngo: Ngo = request.user.ngo if request.user.ngo else None
        donors: QuerySet[Donor] = Donor.objects.filter(Q(ngo=user_ngo)).order_by("-date_created")

        years = range(timezone.now().year, settings.START_YEAR, -1)

        grouped_donors = OrderedDict()
        for donor in donors:
            index = donor.date_created.year
            if index in years:
                grouped_donors[index].append(donor)

        context = {
            "user": request.user,
            "limit": settings.DONATIONS_LIMIT,
            "ngo": user_ngo,
            "donors": grouped_donors,
            "counties": settings.FORM_COUNTIES,
        }
        return render(request, self.template_name, context)


class NgoDetailsHandler(AccountHandler):
    template_name = "ngo/ngo-details.html"

    def get(self, request, *args, **kwargs):
        context = {
            "user": request.user,
            "ngo": request.user.ngo if request.user.ngo else None,
            "counties": settings.FORM_COUNTIES,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        post = request.POST

        ngo: Ngo = request.user.ngo

        if not ngo:
            ngo = Ngo()
            ngo.save()

            ngo.is_verified = False
            ngo.is_active = True

            request.user.ngo = ngo
            request.user.save()

        ngo.name = post.get("ong-nume")
        ngo.description = post.get("ong-descriere")
        ngo.phone = post.get("ong-tel")
        ngo.email = post.get("ong-email")
        ngo.website = post.get("ong-website")
        ngo.address = post.get("ong-adresa")
        ngo.county = post.get("ong-judet")
        ngo.active_region = post.get("ong-activitate")
        ngo.form_url = post.get("ong-url").lower()
        ngo.registration_number = post.get("ong-cif")
        ngo.bank_account = post.get("ong-cont")
        ngo.has_special_status = True if post.get("special-status") == "on" else False
        ngo.is_accepting_forms = True if post.get("accepts-forms") == "on" else False

        ngo.other_emails = ""

        # TODO: implement the image upload
        ngo.logo_url = post.get("ong-logo-url", "")
        ngo.image_url = post.get("ong-logo")

        ngo.save()

        context = {
            "user": request.user,
            "ngo": request.user.ngo if request.user.ngo else None,
            "counties": settings.FORM_COUNTIES,
        }

        return render(request, self.template_name, context)
