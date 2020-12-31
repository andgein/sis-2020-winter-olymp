from typing import List, Optional

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from . import models
from . import scoring


def get_available_sabotages_count(contest: models.Contest, user: User) -> int:
    total_available_sabotages = len(scoring.get_problems_solved_on_first_attempt(contest, user))
    used_sabotages = models.AbstractSabotage.objects.not_instance_of(models.CloseSubmissionSabotage).filter(user=user).count()
    return max(0, total_available_sabotages - used_sabotages)


def get_available_close_submissions_count(contest: models.Contest, user: User) -> int:
    total_available_sabotages = len(scoring.get_correct_solutions(contest, user))
    used_sabotages = models.AbstractSabotage.objects.instance_of(models.CloseSubmissionSabotage).filter(user=user).count()
    return max(0, total_available_sabotages - used_sabotages)


def get_close_submission_sabotages(contest: models.Contest, user: User) -> List[models.CloseSubmissionSabotage]:
    sabotages = models.CloseSubmissionSabotage.objects.filter(
        Q(problem__contests=contest) | Q(problem__isnull=True),
        users=user, start_time__lte=timezone.now(), finish_time__gte=timezone.now()
    ).prefetch_related("problem")
    return list(sabotages)


def get_current_sabotage_for(contest: models.Contest, user: User) -> Optional[models.AbstractSabotage]:
    sabotages = models.AbstractSabotage.objects.not_instance_of(models.CloseSubmissionSabotage).filter(
        contest=contest,
        users=user,
        start_time__lt=timezone.now(),
        finish_time__gte=timezone.now()
    )
    for sabotage in sabotages:
        if sabotage.solutions.filter(user=user).count() == 0:
            return sabotage

    return None
