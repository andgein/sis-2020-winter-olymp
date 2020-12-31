import collections
from typing import List

from django.contrib.auth.models import User

from . import models


def get_solutions(contest: models.Contest, user: User) -> List[models.Solution]:
    return list(models.Solution.objects.filter(user=user, problem__contests=contest).prefetch_related("problem"))


def get_correct_solutions(contest: models.Contest, user: User) -> List[models.Solution]:
    return list(
        models.Solution.objects.filter(user=user, problem__contests=contest, is_correct=True).prefetch_related("problem")
    )


def get_correct_solutions_for_problem(contest: models.Contest, problem: models.Problem) -> List[models.Solution]:
    return list(
        models.Solution.objects.filter(user__contests=contest, problem__contests=contest, problem=problem, is_correct=True)
    )


def get_problems_solved_on_first_attempt(contest: models.Contest, user: User) -> List[models.Problem]:
    problems = {problem.id: problem for problem in contest.problems.all()}

    problem_solutions = collections.defaultdict(list)
    for solution in get_solutions(contest, user):
        problem_solutions[solution.problem_id].append(solution)

    result = []
    for problem_id, solutions in problem_solutions.items():
        if min(solutions, key=lambda s: s.created_at).is_correct:
            result.append(problems[problem_id])

    return result

