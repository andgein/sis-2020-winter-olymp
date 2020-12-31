from django.contrib.auth.models import User
from django.core import validators
from django.db import models
from django.utils import timezone
from polymorphic.models import PolymorphicModel


class Problem(models.Model):
    index = models.IntegerField(validators=[validators.MinValueValidator(1)], help_text="Индекс задачи")

    name = models.CharField(max_length=100, help_text="Название задачи")

    statement = models.TextField(help_text="Условие задачи, поддерживается HTML")

    input_data = models.TextField(help_text="Входные данные")

    answer = models.TextField(help_text="Правильный ответ")

    max_score = models.IntegerField(validators=[validators.MinValueValidator(1)], help_text="Максимальное количество очков за задачу")

    checker = models.TextField(blank=True, help_text="Чекер. Программа на питоне, содержащая функцию check(output, answer) -> bool")

    x = models.IntegerField(help_text="Координата", default=0)

    y = models.IntegerField(help_text="Координата", default=0)

    def check_answer(self, output: str) -> bool:
        output = output.strip()
        if self.checker == "" or self.checker is None:
            return output == self.answer.strip()

        try:
            vars = {}
            exec(self.checker, vars)
            check = vars["check"]
        except Exception as e:
            print(f"Error on checker exec'ing: {e}")
            return False

        try:
            return check(output, self.answer)
        except Exception as e:
            print(f"Error on checking: {e}")
            return False

    def __str__(self):
        return f"{self.index}. {self.name}"


class Contest(models.Model):
    name = models.CharField(max_length=100, help_text="Имя контеста")

    start_time = models.DateTimeField(help_text="Начало контеста")

    finish_time = models.DateTimeField(help_text="Конец контеста")

    users = models.ManyToManyField(User, related_name="contests", help_text="Участники контеста", blank=True)

    problems = models.ManyToManyField(Problem, related_name="contests", help_text="Задачи контеста", blank=True)

    max_sabotage_users = models.IntegerField(help_text="Максимальное количество участников для саботажа", default=3)

    problem_score_coefficient = models.FloatField(
        help_text="Коэффициент уменьшения стоимости задачи после каждого успешного решения",
        default=0.05
    )

    def __str__(self):
        return self.name

    @property
    def is_running(self):
        return self.start_time <= timezone.now() < self.finish_time


class Solution(models.Model):
    user = models.ForeignKey(User, related_name="solutions", on_delete=models.CASCADE)

    problem = models.ForeignKey(Problem, related_name="solutions", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True, help_text="Время отправки ответа")

    answer = models.TextField(blank=True, help_text="Ответ")

    is_correct = models.BooleanField()

    score = models.IntegerField(help_text="Баллы за ответ")

    def __str__(self):
        return f"{self.user} + {self.problem} = {self.is_correct}"


class AbstractSabotage(PolymorphicModel):
    contest = models.ForeignKey(Contest, related_name="sabotages", on_delete=models.CASCADE)

    user = models.ForeignKey(User, related_name="own_sabotages", on_delete=models.CASCADE)

    users = models.ManyToManyField(User, related_name="sabotages")

    start_time = models.DateTimeField(help_text="Начало саботажа")

    finish_time = models.DateTimeField(help_text="Конец саботажа")

    score = models.IntegerField(help_text="Баллы саботажа")

    class Meta:
        verbose_name = "sabotage"
        verbose_name_plural = "sabotages"

    def __str__(self):
        return f"{self.id}. {self.user} саботаж против {list(self.users.all())}: {self.start_time} → {self.finish_time}"


class CloseSubmissionSabotage(AbstractSabotage):
    problem = models.ForeignKey(
        Problem, related_name="close_submission_sabotages", on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="Какую задачу закрыть. None, если все"
    )


class SolveTaskSabotage(AbstractSabotage):
    statement = models.TextField(help_text="Условие задачи, которую надо решить. Поддерживается HTML")

    correct_answer = models.TextField(help_text="Правильный ответ")


class SabotageSolution(models.Model):
    contest = models.ForeignKey(Contest, related_name="sabotage_solutions", on_delete=models.CASCADE)

    user = models.ForeignKey(User, related_name="sabotage_solutions", on_delete=models.CASCADE)

    sabotage = models.ForeignKey(AbstractSabotage, related_name="solutions", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    answer = models.TextField(blank=True, help_text="Ответ")

    is_correct = models.BooleanField()
