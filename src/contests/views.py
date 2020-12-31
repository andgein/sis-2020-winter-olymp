import collections
import datetime
import random
from typing import Optional
from django.conf import settings
import os.path

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone, dateformat
from django.views.decorators.http import require_POST

from . import models, sabotages, forms, scoring


def home(request):
    if not request.user.is_authenticated:
        return render(request, "contests/login.html", {
            "form": forms.LoginForm()
        })

    contests = models.Contest.objects.filter(users=request.user)
    if len(contests) == 0:
        return HttpResponse(b"Contest for you is not found")

    return redirect(reverse("contest", kwargs={"contest_id": contests[0].id}))


@login_required
def view_contest(request, contest_id: int, problem_id: Optional[int] = None, is_correct: Optional[bool] = None,
                 error: Optional[str] = None, close_submission_error: Optional[str] = None,
                 create_sabotage_error: Optional[str] = None):
    contest = get_object_or_404(models.Contest, id=contest_id)
    if request.user not in contest.users.all() and not request.user.is_staff:
        return HttpResponseForbidden(b"You are not allowed here")

    if sabotage := sabotages.get_current_sabotage_for(contest, request.user):
        return redirect("sabotage", contest_id=contest_id, sabotage_id=sabotage.id)

    if contest.start_time > timezone.now():
        return render(request, "contests/rules.html", {
            "contest": contest
        })

    problems = list(contest.problems.all())

    close_submission_sabotages = collections.defaultdict(list)
    for sabotage in sabotages.get_close_submission_sabotages(contest, request.user):
        if sabotage.problem is None:
            for problem in problems:
                close_submission_sabotages[problem.id].append(sabotage)
        else:
            close_submission_sabotages[sabotage.problem.id].append(sabotage)

    user_ids = [u.id for u in contest.users.all() if u.id != request.user.id]

    own_closed_submissions = list(request.user.own_sabotages.all().instance_of(models.CloseSubmissionSabotage).prefetch_related("users").order_by("-start_time"))
    own_sabotages = list(request.user.own_sabotages.all().not_instance_of(models.CloseSubmissionSabotage).prefetch_related("users").order_by("-start_time"))

    solved_problems = [s.problem for s in scoring.get_correct_solutions(contest, request.user)]

    return render(request, "contests/contest.html", {
        "contest": contest,
        "problems": problems,
        "users": list(contest.users.all()),
        "available_sabotages_count": sabotages.get_available_sabotages_count(contest, request.user),
        "available_close_submissions_count": sabotages.get_available_close_submissions_count(contest, request.user),
        "solved_problems": solved_problems,

        "problem_submission_form": forms.SubmitSolutionForm(),
        "close_submission_form": forms.CloseSubmissionForm(user_ids),
        "create_sabotage_form": forms.CreateSabotageForm(user_ids),
        "close_submission_sabotages": close_submission_sabotages,

        "selected_problem": None if problem_id is None else get_object_or_404(models.Problem, id=problem_id),
        "is_correct": is_correct,
        "error": error,
        "close_submission_error": close_submission_error,
        "create_sabotage_error": create_sabotage_error,

        "own_closed_submissions": own_closed_submissions,
        "own_sabotages": own_sabotages,
    })


@login_required
def problem_input(request, contest_id: int, problem_id: int):
    contest = get_object_or_404(models.Contest, id=contest_id)
    if request.user not in contest.users.all() and not request.user.is_staff:
        return HttpResponseForbidden(b"You are not allowed here")

    if sabotage := sabotages.get_current_sabotage_for(contest, request.user):
        return redirect("sabotage", contest_id=contest_id, sabotage_id=sabotage.id)

    problem = get_object_or_404(models.Problem, contests=contest, id=problem_id)

    response = HttpResponse(problem.input_data.encode(), content_type="application/data")
    response["Content-Disposition"] = f"inline; filename={problem.index}.in"
    return response


@login_required
@require_POST
def close_submission(request, contest_id: int):
    contest = get_object_or_404(models.Contest, id=contest_id)
    if request.user not in contest.users.all() and not request.user.is_staff:
        return HttpResponseForbidden(b"You are not allowed here")

    if not contest.is_running:
        return redirect("contest", contest_id=contest_id)

    form = forms.CloseSubmissionForm([u.id for u in contest.users.all() if u.id != request.user.id], data=request.POST)
    if form.is_valid():
        with transaction.atomic():
            available_count = sabotages.get_available_close_submissions_count(contest, request.user)
            if available_count <= 0:
                return view_contest(request, contest.id, close_submission_error="Решите задачу, чтобы закрывать двери")

            sabotage = models.CloseSubmissionSabotage(
                user=request.user,
                contest=contest,
                problem_id=None,
                start_time=timezone.now(),
                finish_time=timezone.now() + datetime.timedelta(minutes=5),
                score=0,
            )
            sabotage.save()
            sabotage.users.set(form.cleaned_data["users"])

            return redirect("contest", contest_id=contest.id)

    return view_contest(request, contest.id, close_submission_error="Выберите команду")


@login_required
def problem(request, contest_id: int, problem_id: int):
    contest = get_object_or_404(models.Contest, id=contest_id)
    if request.user not in contest.users.all() and not request.user.is_staff:
        return HttpResponseForbidden(b"You are not allowed here")

    if not contest.is_running:
        return redirect("contest", contest_id=contest_id)

    if sabotage := sabotages.get_current_sabotage_for(contest, request.user):
        return redirect("sabotage", contest_id=contest_id, sabotage_id=sabotage.id)

    problem = get_object_or_404(models.Problem, contests=contest, id=problem_id)

    if request.method == "GET":
        return view_contest(request, contest_id, problem_id)

    form = forms.SubmitSolutionForm(data=request.POST, files=request.FILES)

    if form.is_valid():
        with transaction.atomic():
            close_sabotages = sabotages.get_close_submission_sabotages(contest, request.user)
            for sabotage in close_sabotages:
                error_message = f"Команда «{sabotage.user.first_name if sabotage.user.first_name else sabotage.user.username}» закрыла вам двери " \
                                f"— вы не можете отправлять ответы до {dateformat.format(timezone.localtime(sabotage.finish_time), 'H:i:s')}."
                if sabotage.problem is None:
                    return view_contest(request, contest.id, problem.id, error=error_message)
                elif problem == sabotage.problem:
                    return view_contest(request, contest.id, problem.id, error=error_message)

            for solution in scoring.get_correct_solutions(contest, request.user):
                if solution.problem_id == problem_id:
                    return view_contest(request, contest.id, problem.id, error="Вы уже сдали эту задачу")

            try:
                answer = form.cleaned_data["file"].file.read().decode()
            except Exception as e:
                print(e)
                return view_contest(request, contest.id, problem.id, error="Это не текстовый файл!")

            is_correct = problem.check_answer(answer)
            if is_correct:
                score = problem.max_score * (1 - contest.problem_score_coefficient * len(scoring.get_correct_solutions_for_problem(contest, problem)))
            else:
                score = 0

            solution = models.Solution(
                problem_id=problem.id,
                user=request.user,
                answer=answer,
                is_correct=is_correct,
                score=score,
            )

            solution.save()

        return view_contest(request, contest.id, problem.id, is_correct=is_correct)

    return view_contest(request, contest.id, problem.id, error="Выберите файл")


@login_required
def sabotage(request, contest_id: int, sabotage_id: int):
    contest = get_object_or_404(models.Contest, id=contest_id)
    if request.user not in contest.users.all() and not request.user.is_staff:
        return HttpResponseForbidden(b"You are not allowed here")

    sabotage = models.AbstractSabotage.objects.not_instance_of(models.CloseSubmissionSabotage).filter(
        id=sabotage_id, contest=contest
    ).get()

    if sabotage is None:
        return HttpResponseNotFound(b"Sabotage not found")

    if request.user not in sabotage.users.all():
        return HttpResponseForbidden(b"You are not allowed to this sabotage")

    if request.method == "GET":
        if sabotage.finish_time < timezone.now():
            return redirect("contest", contest_id=contest.id)

        already_submitted = sabotage.solutions.filter(user=request.user).count() > 0

        return render(request, "contests/sabotage.html", {
            "contest": contest,
            "sabotage": sabotage,
            "form": forms.SubmitSabotageSolutionForm(),
            "already_submitted": already_submitted,
        })

    if request.method == "POST":
        with transaction.atomic():
            solution_count = models.SabotageSolution.objects.filter(
                sabotage=sabotage, user=request.user
            ).count()
            if solution_count > 0:
                return redirect("contest", contest_id=contest_id)

            form = forms.SubmitSabotageSolutionForm(data=request.POST)
            if form.is_valid():
                answer = form.cleaned_data["answer"]
                is_correct = False
                if type(sabotage) is models.SolveTaskSabotage:
                    is_correct = answer.strip() == sabotage.correct_answer

                solution = models.SabotageSolution(
                    contest=contest,
                    user=request.user,
                    sabotage=sabotage,
                    answer=answer,
                    is_correct=is_correct
                )
                solution.save()

                return render(request, "contests/sabotage.html", {
                    "contest": contest,
                    "sabotage": sabotage,
                    "form": forms.SubmitSabotageSolutionForm(),
                    "already_submitted": True,
                    "is_correct": is_correct,
                })

            return render(request, "contests/sabotage.html", {
                "contest": contest,
                "sabotage": sabotage,
                "form": form,
                "error": f"Укажите свой ответ",
            })


@login_required
def create_sabotage(request, contest_id: int):
    contest = get_object_or_404(models.Contest, id=contest_id)
    if request.user not in contest.users.all() and not request.user.is_staff:
        return HttpResponseForbidden(b"You are not allowed here")

    if not contest.is_running:
        return redirect("contest", contest_id=contest_id)

    with transaction.atomic():
        count = sabotages.get_available_sabotages_count(contest, request.user)
        if count == 0:
            return view_contest(request, contest.id, create_sabotage_error="У вас не осталось саботажей")

        form = forms.CreateSabotageForm([u.id for u in contest.users.all() if u.id != request.user.id], data=request.POST)

        if form.is_valid():
            templates = list(models.SabotageTaskTemplate.objects.all())
            template = random.choice(templates)
            sabotage = models.SolveTaskSabotage(
                statement=template.statement,
                correct_answer=template.correct_answer,
                user=request.user,
                contest=contest,
                start_time=timezone.now(),
                finish_time=timezone.now() + datetime.timedelta(minutes=10),
                score=100,
            )
            sabotage.save()
            sabotage.users.set(form.cleaned_data["users"])

            return redirect("contest", contest_id=contest_id)

        return view_contest(request, contest.id, create_sabotage_error="Выберите команды")


@login_required
def monitor(request, contest_id: int):
    contest = get_object_or_404(models.Contest, id=contest_id)

    if sabotage := sabotages.get_current_sabotage_for(contest, request.user):
        return redirect("sabotage", contest_id=contest_id, sabotage_id=sabotage.id)

    users = list(contest.users.all())
    problems = list(contest.problems.all())
    user_score = collections.defaultdict(int)
    user_problem_score = collections.defaultdict(lambda: collections.defaultdict(int))
    has_tries = collections.defaultdict(set)
    has_success_tries = collections.defaultdict(set)
    non_success_tries_count = collections.defaultdict(lambda: collections.defaultdict(int))
    problem_success_tries_count = collections.defaultdict(int)

    for solution in models.Solution.objects.filter(problem__contests=contest, user__in=users).prefetch_related("problem").order_by("created_at"):
        if solution.problem_id in has_success_tries[solution.user_id]:
            # Ignore duplicated success tries
            continue

        if not solution.is_correct:
            has_tries[solution.user_id].add(solution.problem_id)
            if solution.problem_id not in has_success_tries[solution.user_id]:
                non_success_tries_count[solution.user_id][solution.problem_id] += 1
        else:
            has_success_tries[solution.user_id].add(solution.problem_id)
            order = problem_success_tries_count[solution.problem_id]

            score = int(solution.problem.max_score * (1 - contest.problem_score_coefficient * order))
            user_problem_score[solution.user_id][solution.problem_id] = score
            user_score[solution.user_id] += score

            problem_success_tries_count[solution.problem_id] += 1

    closed_submission = collections.defaultdict(set)
    for sabotage in models.AbstractSabotage.objects.instance_of(models.CloseSubmissionSabotage).filter(
        contest=contest,
        start_time__lte=timezone.now(),
        finish_time__gte=timezone.now(),
    ).prefetch_related("problem", "users"):
        if sabotage.problem is None:
            sabotage_problems = problems[:]
        else:
            sabotage_problems = [sabotage.problem]

        for user in sabotage.users.all():
            for problem in sabotage_problems:
                closed_submission[user.id].add(problem.id)

    sabotage_score = collections.defaultdict(int)
    for sabotage in models.AbstractSabotage.objects.not_instance_of(models.CloseSubmissionSabotage).filter(
        contest=contest,
    ).prefetch_related("users"):
        sabotage_solutions = sabotage.solutions.all()
        for solution in sabotage_solutions:
            if solution.is_correct:
                sabotage_score[solution.user_id] += sabotage.score
                user_score[solution.user_id] += sabotage.score
            else:
                user_score[solution.user_id] -= sabotage.score
                sabotage_score[solution.user_id] -= sabotage.score
                user_score[sabotage.user_id] += sabotage.score
                sabotage_score[sabotage.user_id] += sabotage.score

        if sabotage.finish_time <= timezone.now():
            # Sabotage is already finished, add score for each non-submitted solution
            additional_score = sabotage.score * (sabotage.users.count() - len(sabotage_solutions))
            user_score[sabotage.user_id] += additional_score
            sabotage_score[sabotage.user_id] += additional_score

    return render(request, "contests/monitor.html", {
        "contest": contest,
        "users": sorted(users, key=lambda u: (user_score[u.id], sabotage_score[u.id]), reverse=True),
        "problems": list(contest.problems.all().order_by("index")),
        "user_score": user_score,
        "user_problem_score": user_problem_score,
        "sabotage_score": sabotage_score,
        "closed_submission": closed_submission,
        "non_success_tries_count": non_success_tries_count,
        "has_success_tries": has_success_tries,
        "has_tries": has_tries,
    })


def login(request):
    if request.method == "GET":
        return render(request, "contests/login.html", {
            "form": forms.LoginForm(),
        })

    form = forms.LoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data["login"]
        password = form.cleaned_data["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            if user.first_name != "" and user.last_name != "":
                return redirect("home")
            return redirect("profile")

    return render(request, "contests/login.html", {
        "form": form,
        "error": "Неправильный логин или пароль"
    })


@login_required
def profile(request):
    if request.method == "GET":
        return render(request, "contests/profile.html", {
            "form": forms.ProfileForm()
        })

    form = forms.ProfileForm(data=request.POST)
    if form.is_valid():
        request.user.first_name = form.cleaned_data["team_name"]
        request.user.last_name = form.cleaned_data["members"]
        request.user.save()

        return redirect("home")

    return render(request, "contests/profile.html", {
        "form": form
    })


@login_required
def check_sabotages(request, contest_id: int):
    contest = get_object_or_404(models.Contest, id=contest_id)
    if request.user not in contest.users.all() and not request.user.is_staff:
        return HttpResponseForbidden(b"You are not allowed here")

    if not contest.is_running:
        return JsonResponse({"sabotages": []})

    current_sabotages = sabotages.get_current_sabotage_for(contest, request.user)
    return JsonResponse({"sabotages": [current_sabotages.id] if current_sabotages is not None else []})


def service_worker(request):
    with open(os.path.join(settings.BASE_DIR, "contests/static/contests/js/sw.js"), "rb") as f:
        content = f.read()
    return HttpResponse(content, content_type="text/javascript")


def rules(request):
    if request.user.is_authenticated:
        contests = list(models.Contest.objects.filter(users=request.user))
        contest = contests[0] if len(contests) > 0 else None
    else:
        contest = None
    return render(request, "contests/rules.html", {
        "contest": contest,
        "link_to_main_page": True
    })
